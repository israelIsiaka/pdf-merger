"""
License management for PDF Merger.

Security design
---------------
Transport layer  : HTTPS in production (plain HTTP blocked for non-localhost).
Payload layer    : Every request body is AES-256-GCM encrypted using an
                   ephemeral X25519 key pair (ECDH key exchange).
                   The server's X25519 public key is embedded here.
Token integrity  : The server signs every token with Ed25519.
                   The matching public key is embedded here.
                   Tokens cannot be forged without the server's private key.
Device lock      : Each token embeds the device fingerprint.
                   A token copied to another machine fails verification.

Local test mode
---------------
Set the environment variable  PDF_MERGER_TEST_MODE=1  OR set
LOCAL_TEST_MODE = True below to allow plain HTTP connections to localhost.
Run  python server/run_local.py  and paste the printed public keys here.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import socket
import uuid
from base64 import b64decode, b64encode
from pathlib import Path
from typing import Optional, Tuple

import requests
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey, X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidSignature

# ── Configuration — update before release ─────────────────────────────────────

# Set LOCAL_TEST_MODE = True ONLY for local testing.
# In production this must be False so HTTP is rejected.
LOCAL_TEST_MODE = True  # set to False (or use env var) for production

# Production server URL (HTTPS required in production)
_PRODUCTION_URL = "https://your-server.example.com"

# When LOCAL_TEST_MODE is True the client connects here instead
_LOCAL_URL = "http://localhost:8765"

ACTIVATION_SERVER_URL = _LOCAL_URL if LOCAL_TEST_MODE else _PRODUCTION_URL

# ── Embedded public keys (paste from keygen_keys.py / run_local.py) ──────────
# Ed25519 — verifies the server's token signatures
_SIGN_PUBLIC_KEY_B64    = "iBlJLkcVrJ6oRrluSjX//ch7t4JndAM+XwaSWv1fFPU="

# X25519 — encrypts activation request payloads
_ENCRYPT_PUBLIC_KEY_B64 = "V5VNzvfmyVGs9FCjKPX8hhrSJ8KCKV4N29HA+VTvcjU="

# ── Local storage ──────────────────────────────────────────────────────────────
_LICENSE_DIR  = Path.home() / ".pdfmerger"
_LICENSE_FILE = _LICENSE_DIR / "license.dat"

# Network timeout (seconds)
_TIMEOUT = 15


# ── Device fingerprint ────────────────────────────────────────────────────────

def _get_or_create_device_id() -> str:
    """
    Return a persistent random UUID stored in ~/.pdfmerger/device_id.
    Created on first run; survives reboots. Adds entropy on VMs and containers
    where hardware identifiers may be shared or randomised.
    """
    id_file = _LICENSE_DIR / "device_id"
    try:
        _LICENSE_DIR.mkdir(parents=True, exist_ok=True)
        if id_file.exists():
            did = id_file.read_text(encoding="utf-8").strip()
            if len(did) == 36:   # standard UUID format
                return did
        did = str(uuid.uuid4())
        id_file.write_text(did, encoding="utf-8")
        try:
            os.chmod(id_file, 0o600)
        except Exception:
            pass
        return did
    except Exception:
        return ""


def get_device_fingerprint() -> str:
    """
    SHA-256 fingerprint of stable machine identifiers + a persistent device UUID.
    Stable across reboots and minor OS updates.
    Changes on hardware replacement or fresh OS install (intended behaviour).
    The persistent UUID adds uniqueness on VMs/containers where MAC addresses
    may be identical across instances.
    """
    parts: list[str] = []
    try:
        mac = uuid.getnode()
        if not (mac >> 40) & 1:          # real MAC (not randomly generated)
            parts.append(str(mac))
    except Exception:
        pass
    try:
        parts.append(socket.gethostname())
    except Exception:
        pass
    try:
        parts.append(platform.system())
        parts.append(platform.machine())
    except Exception:
        pass
    # Persistent per-install UUID — prevents fingerprint collisions on VMs
    did = _get_or_create_device_id()
    if did:
        parts.append(did)
    raw = "|".join(parts) or "unknown"
    return hashlib.sha256(raw.encode()).hexdigest()


# ── Payload encryption (client side) ─────────────────────────────────────────

def _encrypt_payload(data: dict) -> dict:
    """
    Encrypt data with AES-256-GCM using an ephemeral X25519 key pair.

    Steps:
      1. Generate a one-time ephemeral X25519 key pair
      2. ECDH: shared = ephemeral_priv * server_pub
      3. HKDF-SHA256(shared) -> 32-byte AES key
      4. AES-256-GCM encrypt(JSON(data))

    Returns { ephemeral_pub, nonce, ciphertext } — all base64.
    The server decrypts using its X25519 private key.
    """
    if _ENCRYPT_PUBLIC_KEY_B64 == "REPLACE_WITH_X25519_PUBLIC_KEY":
        raise RuntimeError(
            "X25519 public key not configured. "
            "Run server/keygen_keys.py and paste the public key into src/license.py."
        )
    server_pub = X25519PublicKey.from_public_bytes(b64decode(_ENCRYPT_PUBLIC_KEY_B64))

    eph_priv   = X25519PrivateKey.generate()
    eph_pub    = eph_priv.public_key()
    shared     = eph_priv.exchange(server_pub)

    aes_key = HKDF(
        algorithm=hashes.SHA256(), length=32, salt=None,
        info=b"pdf-merger-activation",
    ).derive(shared)

    nonce      = os.urandom(12)
    plaintext  = json.dumps(data, separators=(",", ":")).encode()
    ciphertext = AESGCM(aes_key).encrypt(nonce, plaintext, None)

    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    return {
        "ephemeral_pub": b64encode(
            eph_pub.public_bytes(Encoding.Raw, PublicFormat.Raw)).decode(),
        "nonce":      b64encode(nonce).decode(),
        "ciphertext": b64encode(ciphertext).decode(),
    }


# ── Token verification ────────────────────────────────────────────────────────

def _verify_token(token_b64: str, sig_b64: str) -> Tuple[bool, dict]:
    """Verify Ed25519 signature over token_b64. Returns (valid, payload)."""
    if _SIGN_PUBLIC_KEY_B64 == "REPLACE_WITH_ED25519_PUBLIC_KEY":
        return False, {}
    try:
        pub        = Ed25519PublicKey.from_public_bytes(b64decode(_SIGN_PUBLIC_KEY_B64))
        token_raw  = b64decode(token_b64)
        pub.verify(b64decode(sig_b64), token_raw)
        return True, json.loads(token_raw.decode())
    except (InvalidSignature, Exception):
        return False, {}


# ── LicenseManager ────────────────────────────────────────────────────────────

class LicenseManager:

    def is_activated(self) -> bool:
        ok, _ = self._load_and_verify()
        return ok

    def get_info(self) -> dict:
        """Return license payload (email, key_hash, activated_at) or {}."""
        _, payload = self._load_and_verify()
        return payload

    def activate(self, key: str, email: str) -> Tuple[bool, str]:
        """
        Contact the activation server, validate key+email, and store token.
        Returns (success, message).
        """
        key   = key.strip().upper()
        email = email.strip().lower()

        if not key:
            return False, "Please enter your activation key."
        if not email or "@" not in email:
            return False, "Please enter a valid email address."

        # Enforce HTTPS for non-localhost in production
        url = ACTIVATION_SERVER_URL
        if not LOCAL_TEST_MODE and url.startswith("http://"):
            host = url.split("//")[-1].split("/")[0].split(":")[0]
            if host not in ("localhost", "127.0.0.1", "::1"):
                return False, "Insecure connection refused. Server must use HTTPS."

        device_fp = get_device_fingerprint()
        try:
            body = _encrypt_payload({
                "key":                key,
                "email":              email,
                "device_fingerprint": device_fp,
            })
        except RuntimeError as exc:
            return False, str(exc)

        try:
            resp = requests.post(
                f"{url}/activate",
                json=body,
                timeout=_TIMEOUT,
                verify=not LOCAL_TEST_MODE,   # skip SSL verify only on localhost
            )
        except requests.exceptions.SSLError:
            return False, (
                "SSL certificate error. The server's certificate is invalid.\n"
                "Please contact support."
            )
        except requests.exceptions.ConnectionError:
            return False, (
                "Cannot reach the activation server.\n"
                "Please check your internet connection and try again."
            )
        except requests.exceptions.Timeout:
            return False, "Activation server timed out. Please try again."
        except Exception as exc:
            return False, f"Network error: {exc}"

        if resp.status_code == 200:
            data      = resp.json()
            token_b64 = data.get("token", "")
            sig_b64   = data.get("signature", "")

            ok, payload = _verify_token(token_b64, sig_b64)
            if not ok:
                return False, "Server returned an invalid token. Please contact support."
            if payload.get("device_fingerprint") != device_fp:
                return False, "Token device mismatch. Please contact support."

            self._save(token_b64, sig_b64)
            return True, "Activation successful. Thank you for your purchase!"

        try:
            detail = resp.json().get("detail", "")
        except Exception:
            detail = ""

        if resp.status_code == 403:
            return False, (
                detail or
                "The email address does not match this license key.\n"
                "Please use the email address you purchased with."
            )
        if resp.status_code == 404:
            return False, "Invalid activation key. Please check and try again."
        if resp.status_code == 409:
            return False, (
                detail or
                "This key is already activated on another device.\n\n"
                "To transfer your license, open the app and go to\n"
                "Help > Transfer License."
            )
        if resp.status_code == 429:
            return False, "Too many attempts. Please wait a minute and try again."

        return False, detail or f"Server error (HTTP {resp.status_code}). Contact support."

    def request_transfer(
        self, key: str, email: str, reason: str, new_device: str = ""
    ) -> Tuple[bool, str]:
        """Submit a device transfer request to the server."""
        key   = key.strip().upper()
        email = email.strip().lower()
        if not key or not email:
            return False, "Key and email are required."

        try:
            body = _encrypt_payload({
                "key":        key,
                "email":      email,
                "new_device": new_device or get_device_fingerprint(),
                "reason":     reason.strip(),
            })
        except RuntimeError as exc:
            return False, str(exc)

        try:
            resp = requests.post(
                f"{ACTIVATION_SERVER_URL}/transfer/request",
                json=body,
                timeout=_TIMEOUT,
                verify=not LOCAL_TEST_MODE,
            )
        except requests.exceptions.ConnectionError:
            return False, "Cannot reach the server. Check your internet connection."
        except Exception as exc:
            return False, f"Network error: {exc}"

        if resp.status_code == 200:
            msg = resp.json().get("message", "Transfer request submitted.")
            return True, msg
        try:
            detail = resp.json().get("detail", "")
        except Exception:
            detail = ""
        return False, detail or f"Server error (HTTP {resp.status_code})."

    # -- Private helpers ───────────────────────────────────────────────────────

    def _save(self, token_b64: str, sig_b64: str):
        _LICENSE_DIR.mkdir(parents=True, exist_ok=True)
        _LICENSE_FILE.write_text(
            json.dumps({"token": token_b64, "signature": sig_b64}),
            encoding="utf-8",
        )
        try:
            os.chmod(_LICENSE_FILE, 0o600)
        except Exception:
            pass

    def _load_and_verify(self) -> Tuple[bool, dict]:
        if not _LICENSE_FILE.exists():
            return False, {}
        try:
            d = json.loads(_LICENSE_FILE.read_text(encoding="utf-8"))
            token_b64 = d.get("token", "")
            sig_b64   = d.get("signature", "")
        except Exception:
            return False, {}

        ok, payload = _verify_token(token_b64, sig_b64)
        if not ok:
            return False, {}

        if payload.get("device_fingerprint") != get_device_fingerprint():
            return False, {}

        return True, payload
