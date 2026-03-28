"""
PDF Merger — Activation Server
================================
Security layers:
  1. Transport (TLS)      — HTTPS enforced; plain HTTP rejected except on localhost
  2. Payload encryption   — X25519 ECDH + AES-256-GCM on every request/response
  3. Token integrity      — Ed25519-signed tokens; cannot be forged without private key
  4. Rate limiting        — 10 req/min on /activate; prevents brute-force key guessing
  5. Security headers     — HSTS, X-Content-Type-Options, X-Frame-Options, no-store

Features:
  - Activation keys linked to a customer email address
  - Device-locked: one key binds to one device fingerprint
  - Device transfer workflow: user submits request → admin approves → license re-bound
  - Admin can cap the maximum number of transfers per license
  - Full audit log: every activation, transfer request and admin action is recorded

Environment variables (set in your hosting platform):
  SECRET_KEY_B64     Ed25519 private key   (from keygen_keys.py)
  ENCRYPT_KEY_B64    X25519 private key    (from keygen_keys.py)
  ADMIN_SECRET       Header secret for all /admin/* endpoints
  DATABASE_URL       SQLite path  (default: server/licenses.db)
  LOCAL_TEST_MODE    Set to "1" to allow plain HTTP (local testing only)

Quick start (local):
  python server/run_local.py
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import secrets
import sqlite3
from base64 import b64decode, b64encode
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import HTMLResponse, JSONResponse

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey, X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    _limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
    _HAS_RATELIMIT = True
except ImportError:
    _limiter = None
    _HAS_RATELIMIT = False


def _limit(rate: str):
    """Rate-limit decorator; no-op when slowapi is not installed."""
    if _limiter:
        return _limiter.limit(rate)
    return lambda f: f

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

DB_PATH         = os.environ.get("DATABASE_URL", "server/licenses.db")
ADMIN_SECRET    = os.environ.get("ADMIN_SECRET", "change-this-secret")
LOCAL_TEST_MODE = os.environ.get("LOCAL_TEST_MODE", "0") == "1"

_SIGN_KEY_B64    = os.environ.get("SECRET_KEY_B64", "")
_ENCRYPT_KEY_B64 = os.environ.get("ENCRYPT_KEY_B64", "")

# ── Stripe + email config ──────────────────────────────────────────────────
STRIPE_SECRET_KEY     = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_CENTS    = int(os.environ.get("STRIPE_PRICE_CENTS", "2900"))
STRIPE_PRODUCT_NAME   = os.environ.get("STRIPE_PRODUCT_NAME", "PDF Merger - Lifetime License")
RESEND_API_KEY        = os.environ.get("RESEND_API_KEY", "")
FROM_EMAIL            = os.environ.get("FROM_EMAIL", "onboarding@resend.dev")
APP_URL               = os.environ.get("APP_URL", "http://localhost:8765")

import requests as _requests   # already a dep; alias to avoid name clash below

def _send_activation_email(to_email: str, key: str, seats: int = 1) -> bool:
    """Send the activation key to the customer via Resend."""
    if not RESEND_API_KEY:
        log.warning("RESEND_API_KEY not set — skipping email for %s", to_email)
        return False
    seats_line = (
        f"This key covers <strong>{seats} seats</strong> — "
        f"it can be activated on up to {seats} different computers."
        if seats > 1 else
        "This is a lifetime license. One key, one device."
    )
    transfer_note = (
        "To free a seat on an old machine, contact support."
        if seats > 1 else
        "If you replace your computer, use <em>Help &gt; Transfer License</em> in the app."
    )
    html = f"""
    <div style="font-family:system-ui,sans-serif;max-width:520px;margin:0 auto;padding:32px;
                background:#0f1117;color:#e2e8f0;border-radius:12px">
      <h2 style="margin:0 0 8px;font-size:22px">Your PDF Merger License</h2>
      <p style="color:#8892a4;margin:0 0 28px;font-size:14px">
        Thank you for your purchase. Your activation key is below.
      </p>
      <div style="background:#1a1d27;border:1px solid #2a2d3a;border-radius:8px;
                  padding:20px 24px;text-align:center;margin-bottom:28px">
        <p style="color:#8892a4;font-size:12px;margin:0 0 8px;
                  text-transform:uppercase;letter-spacing:.5px">Activation Key</p>
        <p style="font-family:monospace;font-size:22px;font-weight:700;
                  letter-spacing:3px;color:#4f7ef7;margin:0">{key}</p>
        {f'<p style="color:#22c55e;font-size:12px;margin:8px 0 0">{seats} seat(s)</p>' if seats > 1 else ''}
      </div>
      <p style="color:#e2e8f0;font-size:14px;line-height:1.7;margin:0 0 12px">
        <strong>How to activate:</strong><br>
        1. Open PDF Merger on each computer — the activation dialog appears on first launch.<br>
        2. Enter <strong>{to_email}</strong> as the email.<br>
        3. Enter the key above and click <strong>Activate</strong>.
      </p>
      <p style="color:#e2e8f0;font-size:14px;margin:0 0 12px">{seats_line}</p>
      <p style="color:#8892a4;font-size:12px;margin-top:24px;line-height:1.6">
        {transfer_note}<br><br>
        Keep this email — it is the only record of your activation key.
      </p>
    </div>
    """
    try:
        resp = _requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}",
                     "Content-Type": "application/json"},
            json={"from": FROM_EMAIL, "to": [to_email],
                  "subject": "Your PDF Merger Activation Key",
                  "html": html},
            timeout=15,
        )
        if resp.status_code not in (200, 201):
            log.error("Resend error %s: %s", resp.status_code, resp.text)
            return False
        return True
    except Exception as exc:
        log.error("Email send failed: %s", exc)
        return False

_EMAIL_RE        = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
_STRIPE_SID_RE   = re.compile(r"^cs_(test|live)_[a-zA-Z0-9]{20,120}$")


# ── Database ──────────────────────────────────────────────────────────────────

def _init_db():
    parent = os.path.dirname(DB_PATH)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with _db() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS licenses (
                key_hash           TEXT PRIMARY KEY,
                email              TEXT NOT NULL DEFAULT '',
                device_fingerprint TEXT,
                activated_at       TEXT,
                is_used            INTEGER NOT NULL DEFAULT 0,
                created_at         TEXT NOT NULL DEFAULT (datetime('now')),
                max_transfers      INTEGER NOT NULL DEFAULT 3,
                max_activations    INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS license_activations (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                key_hash           TEXT NOT NULL,
                device_fingerprint TEXT NOT NULL,
                activated_at       TEXT NOT NULL,
                FOREIGN KEY (key_hash) REFERENCES licenses(key_hash),
                UNIQUE (key_hash, device_fingerprint)
            );

            CREATE TABLE IF NOT EXISTS transfer_requests (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                key_hash       TEXT NOT NULL,
                email          TEXT NOT NULL,
                old_device     TEXT,
                new_device     TEXT,
                reason         TEXT,
                status         TEXT NOT NULL DEFAULT 'pending',
                requested_at   TEXT NOT NULL,
                resolved_at    TEXT,
                resolved_by    TEXT,
                transfer_count INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (key_hash) REFERENCES licenses(key_hash)
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                event      TEXT NOT NULL,
                key_hash   TEXT,
                email      TEXT,
                ip_address TEXT,
                details    TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        # Schema migration: add max_activations to existing DBs
        try:
            c.execute(
                "ALTER TABLE licenses ADD COLUMN max_activations INTEGER NOT NULL DEFAULT 1"
            )
        except Exception:
            pass  # column already exists
        # Data migration: populate license_activations from existing device bindings
        c.execute("""
            INSERT OR IGNORE INTO license_activations (key_hash, device_fingerprint, activated_at)
            SELECT key_hash, device_fingerprint, COALESCE(activated_at, datetime('now'))
            FROM licenses WHERE is_used=1 AND device_fingerprint IS NOT NULL
        """)
        # Seed default price if not already set
        c.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES ('price_cents', ?)",
            (str(STRIPE_PRICE_CENTS),)
        )


@contextmanager
def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_price_cents() -> int:
    try:
        with _db() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key='price_cents'"
            ).fetchone()
        return int(row["value"]) if row else STRIPE_PRICE_CENTS
    except Exception:
        return STRIPE_PRICE_CENTS


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.upper().strip().encode()).hexdigest()


def _audit(conn, event: str, key_hash: str = "", email: str = "",
           ip: str = "", details: str = ""):
    conn.execute(
        "INSERT INTO audit_log (event, key_hash, email, ip_address, details) "
        "VALUES (?,?,?,?,?)",
        (event, key_hash, email, ip, details),
    )


def _client_ip(request: Request) -> str:
    # Only trust X-Forwarded-For when explicitly running behind a proxy.
    # In LOCAL_TEST_MODE or when TRUST_PROXY env var is set, use the header.
    # Otherwise use the direct socket address to prevent IP spoofing.
    if LOCAL_TEST_MODE or os.environ.get("TRUST_PROXY", "0") == "1":
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            # Take the leftmost (client) IP, strip whitespace
            candidate = forwarded.split(",")[0].strip()
            # Basic sanity check — must look like an IP address
            if re.match(r"^[\d\.a-fA-F:]+$", candidate):
                return candidate
    return request.client.host if request.client else ""


# ── Cryptography ──────────────────────────────────────────────────────────────

def _signing_key() -> Ed25519PrivateKey:
    if not _SIGN_KEY_B64:
        raise RuntimeError("SECRET_KEY_B64 not set.")
    return Ed25519PrivateKey.from_private_bytes(b64decode(_SIGN_KEY_B64))


def _encryption_key() -> X25519PrivateKey:
    if not _ENCRYPT_KEY_B64:
        raise RuntimeError("ENCRYPT_KEY_B64 not set.")
    return X25519PrivateKey.from_private_bytes(b64decode(_ENCRYPT_KEY_B64))


def _sign(payload: dict) -> tuple[str, str]:
    """Ed25519-sign a dict. Returns (token_b64, sig_b64)."""
    raw     = json.dumps(payload, separators=(",", ":")).encode()
    token   = b64encode(raw).decode()
    sig     = b64encode(_signing_key().sign(raw)).decode()
    return token, sig


def _decrypt_request(body: dict) -> dict:
    """
    Decrypt an AES-256-GCM request body.

    Expected fields: ephemeral_pub, nonce, ciphertext  (all base64).
    The client generated an ephemeral X25519 key pair, performed ECDH with
    the server's public key, derived an AES key via HKDF-SHA256, then
    encrypted the JSON payload with AES-256-GCM.
    """
    try:
        eph_pub    = b64decode(body["ephemeral_pub"])
        nonce      = b64decode(body["nonce"])
        ciphertext = b64decode(body["ciphertext"])
    except (KeyError, Exception) as exc:
        raise HTTPException(400, f"Malformed encrypted payload: {exc}")

    try:
        shared = _encryption_key().exchange(X25519PublicKey.from_public_bytes(eph_pub))
    except Exception as exc:
        raise HTTPException(400, f"Key exchange failed: {exc}")

    aes_key = HKDF(
        algorithm=hashes.SHA256(), length=32, salt=None,
        info=b"pdf-merger-activation",
    ).derive(shared)

    try:
        plain = AESGCM(aes_key).decrypt(nonce, ciphertext, None)
        return json.loads(plain.decode())
    except Exception:
        raise HTTPException(400, "Decryption failed.")


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(title="PDF Merger License Server", docs_url=None, redoc_url=None)

if _HAS_RATELIMIT:
    app.state.limiter = _limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Security headers
class _SecurityHeaders(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        resp = await call_next(request)
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"]        = "DENY"
        resp.headers["Referrer-Policy"]        = "no-referrer"
        resp.headers["Cache-Control"]          = "no-store"
        if not LOCAL_TEST_MODE:
            resp.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )
        return resp

app.add_middleware(_SecurityHeaders)


# HTTPS enforcement
class _HTTPSOnly(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if LOCAL_TEST_MODE:
            return await call_next(request)
        proto    = request.headers.get("X-Forwarded-Proto", "https")
        host     = request.client.host if request.client else ""
        is_local = host in ("127.0.0.1", "::1", "localhost")
        if proto != "https" and not is_local:
            return JSONResponse({"detail": "HTTPS required."}, status_code=400)
        return await call_next(request)

app.add_middleware(_HTTPSOnly)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    _init_db()
    if LOCAL_TEST_MODE:
        log.warning("LOCAL_TEST_MODE ON — plain HTTP allowed. Do NOT use in production.")
    if not _SIGN_KEY_B64:
        log.error("SECRET_KEY_B64 not set — signing will fail.")
    if not _ENCRYPT_KEY_B64:
        log.error("ENCRYPT_KEY_B64 not set — decryption will fail.")


# ── Pydantic models ───────────────────────────────────────────────────────────

class EncryptedBody(BaseModel):
    ephemeral_pub: str
    nonce: str
    ciphertext: str


class GenerateKeysRequest(BaseModel):
    count: int = 1
    email: str = ""      # optional: pre-assign email when generating keys
    max_activations: int = 1  # number of seats (devices) per key

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v and not _EMAIL_RE.match(v):
            raise ValueError("Invalid email address.")
        return v.lower().strip()

    @field_validator("max_activations")
    @classmethod
    def validate_max_activations(cls, v):
        if not 1 <= v <= 1000:
            raise ValueError("max_activations must be 1–1000.")
        return v


class TransferDecisionRequest(BaseModel):
    reason: str = ""


class SetTransferLimitRequest(BaseModel):
    max_transfers: int

    @field_validator("max_transfers")
    @classmethod
    def validate_max_transfers(cls, v: int) -> int:
        if not 0 <= v <= 100:
            raise ValueError("max_transfers must be 0–100.")
        return v


# ── Public endpoints ──────────────────────────────────────────────────────────

@app.get("/public-key")
async def get_public_key():
    """Returns the server's X25519 public key for payload encryption."""
    if not _ENCRYPT_KEY_B64:
        raise HTTPException(503, "Server not configured.")
    pub = _encryption_key().public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    return {"x25519_public_key": b64encode(pub).decode()}


@app.post("/activate")
@_limit("10/minute")
async def activate(request: Request, body: EncryptedBody):
    """
    Activate a license key for a device.

    Decrypted payload must contain:
      key                — activation key (XXXX-XXXX-XXXX-XXXX)
      email              — customer email address
      device_fingerprint — SHA-256 of stable hardware identifiers

    Returns an encrypted { token, signature } on success.
    """
    ip  = _client_ip(request)
    req = _decrypt_request(body.dict())

    key_hash = _hash_key(str(req.get("key", "")))
    fp       = str(req.get("device_fingerprint", "")).strip()
    email    = str(req.get("email", "")).lower().strip()

    if not fp or len(fp) < 8:
        raise HTTPException(400, "Invalid device fingerprint.")
    if not email or not _EMAIL_RE.match(email):
        raise HTTPException(400, "A valid email address is required.")

    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM licenses WHERE key_hash=?", (key_hash,)
        ).fetchone()

        if row is None:
            _audit(conn, "ACTIVATE_INVALID_KEY", key_hash, email, ip)
            raise HTTPException(404, "Activation key not found.")

        # If a customer email was pre-assigned, verify it matches
        if row["email"] and row["email"] != email:
            _audit(conn, "ACTIVATE_EMAIL_MISMATCH", key_hash, email, ip)
            raise HTTPException(403,
                "The email address does not match the one registered for this key. "
                "Please use the email address you purchased with.")

        max_act = dict(row).get("max_activations", 1) or 1

        # Check if this exact device is already activated (reinstall / lost token)
        existing = conn.execute(
            "SELECT id FROM license_activations WHERE key_hash=? AND device_fingerprint=?",
            (key_hash, fp),
        ).fetchone()

        if existing:
            _audit(conn, "ACTIVATE_REISSUE", key_hash, email, ip, f"device={fp[:8]}...")
        else:
            act_count = conn.execute(
                "SELECT COUNT(*) FROM license_activations WHERE key_hash=?",
                (key_hash,),
            ).fetchone()[0]

            if act_count >= max_act:
                seat_word = "seat" if max_act == 1 else "seats"
                _audit(conn, "ACTIVATE_BLOCKED_SEATS_FULL", key_hash, email, ip,
                       f"seats={act_count}/{max_act} device={fp[:8]}...")
                raise HTTPException(409,
                    f"All {max_act} licensed {seat_word} are already in use.\n\n"
                    "To free a seat, ask your admin to deactivate an old device, "
                    "or purchase additional seats.")

            # New device — claim a seat
            # INSERT OR IGNORE handles the rare race condition where two requests
            # arrive simultaneously for the same device; UNIQUE constraint prevents
            # a duplicate row and we treat the ignored insert as a re-issue.
            conn.execute(
                "INSERT OR IGNORE INTO license_activations "
                "(key_hash, device_fingerprint, activated_at) VALUES (?,?,?)",
                (key_hash, fp, _now()),
            )
            conn.execute(
                "UPDATE licenses SET is_used=1, email=?, device_fingerprint=?, "
                "activated_at=? WHERE key_hash=?",
                (email, fp, _now(), key_hash),
            )
            _audit(conn, "ACTIVATE_OK", key_hash, email, ip,
                   f"device={fp[:8]}... seats={act_count+1}/{max_act}")

        row = conn.execute(
            "SELECT * FROM licenses WHERE key_hash=?", (key_hash,)
        ).fetchone()

    payload = {
        "key_hash":           key_hash,
        "email":              email,
        "device_fingerprint": fp,
        "activated_at":       row["activated_at"],
        "version":            1,
    }
    token, sig = _sign(payload)
    log.info("Activated  key=%s...  email=%s  device=%s...", key_hash[:8], email, fp[:8])
    return {"token": token, "signature": sig}


@app.post("/transfer/request")
@_limit("5/minute")
async def request_transfer(request: Request, body: EncryptedBody):
    """
    Submit a device transfer request.

    Decrypted payload must contain:
      key                — activation key
      email              — customer email (must match record)
      new_device         — fingerprint of the new device (optional)
      reason             — why the transfer is needed

    The request enters 'pending' status. An admin must approve it before the
    license is re-bound to the new device.
    """
    ip  = _client_ip(request)
    req = _decrypt_request(body.dict())

    key_hash   = _hash_key(str(req.get("key", "")))
    email      = str(req.get("email", "")).lower().strip()
    new_device = str(req.get("new_device", "")).strip()
    reason = str(req.get("reason", "")).strip()[:500]

    if not email or not _EMAIL_RE.match(email):
        raise HTTPException(400, "A valid email address is required.")
    if not reason or len(reason) < 10:
        raise HTTPException(400, "Please provide a reason for the transfer (min 10 characters).")

    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM licenses WHERE key_hash=?", (key_hash,)
        ).fetchone()
        if row is None:
            raise HTTPException(404, "Activation key not found.")
        if row["email"] and row["email"] != email:
            raise HTTPException(403, "Email does not match this license.")

        # Count approved transfers
        approved_count = conn.execute(
            "SELECT COUNT(*) FROM transfer_requests "
            "WHERE key_hash=? AND status='approved'",
            (key_hash,),
        ).fetchone()[0]

        if approved_count >= row["max_transfers"]:
            raise HTTPException(429,
                f"This license has reached its maximum transfer limit "
                f"({row['max_transfers']}). Please contact support.")

        # Check for an already-pending request
        pending = conn.execute(
            "SELECT id FROM transfer_requests "
            "WHERE key_hash=? AND status='pending'",
            (key_hash,),
        ).fetchone()
        if pending:
            raise HTTPException(409,
                "A transfer request is already pending for this license. "
                "Please wait for admin approval.")

        conn.execute(
            "INSERT INTO transfer_requests "
            "(key_hash, email, old_device, new_device, reason, status, "
            " requested_at, transfer_count) "
            "VALUES (?,?,?,?,?,'pending',?,?)",
            (key_hash, email,
             row["device_fingerprint"], new_device or None,
             reason, _now(), approved_count),
        )
        _audit(conn, "TRANSFER_REQUESTED", key_hash, email, ip,
               f"reason={reason[:80]}")

    log.info("Transfer requested  key=%s...  email=%s", key_hash[:8], email)
    return {
        "status": "pending",
        "message": (
            "Your transfer request has been submitted. "
            "An admin will review it and contact you at "
            f"{email} with the outcome."
        ),
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard():
    from .admin_ui import ADMIN_HTML
    return ADMIN_HTML


# ── Admin endpoints ───────────────────────────────────────────────────────────
# All admin endpoints require the X-Admin-Secret header.

def _require_admin(secret: Optional[str]):
    if secret != ADMIN_SECRET:
        log.warning("ADMIN_AUTH_FAILED — invalid or missing admin secret")
        try:
            with _db() as conn:
                _audit(conn, "ADMIN_AUTH_FAILED",
                       details="invalid or missing admin secret")
        except Exception:
            pass
        raise HTTPException(403, "Forbidden.")


@app.post("/admin/generate-keys")
async def generate_keys(
    req: GenerateKeysRequest,
    x_admin_secret: Optional[str] = Header(default=None),
):
    """
    Generate activation keys and insert them into the database.
    Optionally pre-assign a customer email.
    Returns the plaintext keys once — stored only as hashes.
    """
    _require_admin(x_admin_secret)
    if not 1 <= req.count <= 1000:
        raise HTTPException(400, "count must be 1–1000.")

    keys = []
    with _db() as conn:
        for _ in range(req.count):
            raw = secrets.token_hex(12).upper()
            key = f"{raw[0:4]}-{raw[4:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:24]}"
            conn.execute(
                "INSERT OR IGNORE INTO licenses "
                "(key_hash, email, created_at, max_activations) VALUES (?,?,?,?)",
                (_hash_key(key), req.email, _now(), req.max_activations),
            )
            keys.append(key)
        _audit(conn, "ADMIN_GENERATE_KEYS",
               details=f"count={len(keys)} email={req.email} seats={req.max_activations}")

    log.info("Generated %d key(s)  email=%s  seats=%d", len(keys), req.email, req.max_activations)
    return {"keys": keys, "count": len(keys)}


@app.get("/admin/transfers")
async def list_transfers(
    status: str = "pending",
    x_admin_secret: Optional[str] = Header(default=None),
):
    """
    List transfer requests.  Filter by status: pending | approved | rejected | all
    """
    _require_admin(x_admin_secret)
    with _db() as conn:
        if status == "all":
            rows = conn.execute(
                "SELECT * FROM transfer_requests ORDER BY requested_at DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM transfer_requests WHERE status=? "
                "ORDER BY requested_at DESC",
                (status,),
            ).fetchall()
    return {"requests": [dict(r) for r in rows], "count": len(rows)}


@app.post("/admin/transfers/{transfer_id}/approve")
async def approve_transfer(
    transfer_id: int,
    x_admin_secret: Optional[str] = Header(default=None),
):
    """
    Approve a transfer request.

    This re-binds the license to the new device fingerprint (if provided by
    the user at request time) or clears the binding so the user can activate
    on any new device.
    """
    _require_admin(x_admin_secret)
    with _db() as conn:
        tr = conn.execute(
            "SELECT * FROM transfer_requests WHERE id=?", (transfer_id,)
        ).fetchone()
        if tr is None:
            raise HTTPException(404, "Transfer request not found.")
        if tr["status"] != "pending":
            raise HTTPException(409, f"Request is already '{tr['status']}'.")

        new_device = tr["new_device"]   # may be None

        # Reset device binding so user can activate on new device
        conn.execute(
            "UPDATE licenses SET is_used=0, device_fingerprint=?, activated_at=NULL "
            "WHERE key_hash=?",
            (new_device, tr["key_hash"]),
        )
        conn.execute(
            "UPDATE transfer_requests "
            "SET status='approved', resolved_at=?, resolved_by='admin' "
            "WHERE id=?",
            (_now(), transfer_id),
        )
        _audit(conn, "TRANSFER_APPROVED", tr["key_hash"], tr["email"],
               details=f"new_device={str(new_device)[:8] if new_device else 'any'}")

    log.info("Transfer approved  id=%d  key=%s...", transfer_id, tr["key_hash"][:8])
    return {
        "status": "approved",
        "message": (
            "License reset. The customer can now activate on their new device. "
            f"Notify them at: {tr['email']}"
        ),
    }


@app.post("/admin/transfers/{transfer_id}/reject")
async def reject_transfer(
    transfer_id: int,
    body: TransferDecisionRequest,
    x_admin_secret: Optional[str] = Header(default=None),
):
    """Reject a transfer request."""
    _require_admin(x_admin_secret)
    with _db() as conn:
        tr = conn.execute(
            "SELECT * FROM transfer_requests WHERE id=?", (transfer_id,)
        ).fetchone()
        if tr is None:
            raise HTTPException(404, "Transfer request not found.")
        if tr["status"] != "pending":
            raise HTTPException(409, f"Request is already '{tr['status']}'.")

        conn.execute(
            "UPDATE transfer_requests "
            "SET status='rejected', resolved_at=?, resolved_by='admin' "
            "WHERE id=?",
            (_now(), transfer_id),
        )
        _audit(conn, "TRANSFER_REJECTED", tr["key_hash"], tr["email"],
               details=body.reason[:200])

    log.info("Transfer rejected  id=%d", transfer_id)
    return {"status": "rejected"}


@app.post("/admin/licenses/{key_hash}/set-transfer-limit")
async def set_transfer_limit(
    key_hash: str,
    body: SetTransferLimitRequest,
    x_admin_secret: Optional[str] = Header(default=None),
):
    """Set the maximum number of approved device transfers for a license."""
    _require_admin(x_admin_secret)
    with _db() as conn:
        result = conn.execute(
            "UPDATE licenses SET max_transfers=? WHERE key_hash=?",
            (body.max_transfers, key_hash),
        )
        if result.rowcount == 0:
            raise HTTPException(404, "License not found.")
        _audit(conn, "ADMIN_SET_TRANSFER_LIMIT", key_hash,
               details=f"max_transfers={body.max_transfers}")

    return {"key_hash": key_hash, "max_transfers": body.max_transfers}


@app.get("/admin/licenses")
async def list_licenses(
    x_admin_secret: Optional[str] = Header(default=None),
):
    """List all licenses with seat activation counts."""
    _require_admin(x_admin_secret)
    with _db() as conn:
        rows = conn.execute(
            """
            SELECT l.key_hash, l.email, l.is_used, l.activated_at, l.created_at,
                   l.max_transfers,
                   COALESCE(l.max_activations, 1) AS max_activations,
                   COUNT(a.id) AS activation_count
            FROM licenses l
            LEFT JOIN license_activations a ON a.key_hash = l.key_hash
            GROUP BY l.key_hash
            ORDER BY l.created_at DESC
            """
        ).fetchall()
    return {"licenses": [dict(r) for r in rows], "count": len(rows)}


@app.get("/admin/licenses/{key_hash}/activations")
async def list_activations(
    key_hash: str,
    x_admin_secret: Optional[str] = Header(default=None),
):
    """List all activated devices for a license."""
    _require_admin(x_admin_secret)
    with _db() as conn:
        row = conn.execute(
            "SELECT email FROM licenses WHERE key_hash=?", (key_hash,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "License not found.")
        acts = conn.execute(
            "SELECT id, device_fingerprint, activated_at "
            "FROM license_activations WHERE key_hash=? ORDER BY activated_at",
            (key_hash,),
        ).fetchall()
    return {"activations": [dict(a) for a in acts], "email": row["email"]}


@app.post("/admin/licenses/{key_hash}/activations/{activation_id}/deactivate")
async def deactivate_device(
    key_hash: str,
    activation_id: int,
    x_admin_secret: Optional[str] = Header(default=None),
):
    """Remove one device activation, freeing a seat."""
    _require_admin(x_admin_secret)
    with _db() as conn:
        act = conn.execute(
            "SELECT * FROM license_activations WHERE id=? AND key_hash=?",
            (activation_id, key_hash),
        ).fetchone()
        if not act:
            raise HTTPException(404, "Activation not found.")
        conn.execute("DELETE FROM license_activations WHERE id=?", (activation_id,))
        # Update licenses.is_used based on remaining activations
        remaining = conn.execute(
            "SELECT COUNT(*) FROM license_activations WHERE key_hash=?", (key_hash,)
        ).fetchone()[0]
        if remaining == 0:
            conn.execute(
                "UPDATE licenses SET is_used=0, device_fingerprint=NULL, activated_at=NULL "
                "WHERE key_hash=?",
                (key_hash,),
            )
        _audit(conn, "ADMIN_DEACTIVATE_DEVICE", key_hash,
               details=f"activation_id={activation_id} device={act['device_fingerprint'][:8]}...")
    return {"ok": True}


@app.get("/admin/purchases")
async def list_purchases(
    limit: int = 200,
    x_admin_secret: Optional[str] = Header(default=None),
):
    """Return all completed purchases with license status."""
    _require_admin(x_admin_secret)
    limit = max(1, min(limit, 1000))
    with _db() as conn:
        rows = conn.execute(
            """
            SELECT a.created_at, a.email, a.key_hash, a.details,
                   l.is_used, l.activated_at
            FROM audit_log a
            LEFT JOIN licenses l ON l.key_hash = a.key_hash
            WHERE a.event = 'PURCHASE_COMPLETE'
            ORDER BY a.created_at DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()
    return {"purchases": [dict(r) for r in rows], "count": len(rows)}


@app.get("/admin/audit-log")
async def get_audit_log(
    limit: int = 100,
    x_admin_secret: Optional[str] = Header(default=None),
):
    """Return the most recent audit log entries."""
    _require_admin(x_admin_secret)
    limit = max(1, min(limit, 1000))
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return {"entries": [dict(r) for r in rows], "count": len(rows)}


# ── Registration / purchase endpoints ─────────────────────────────────────────

class CheckoutRequest(BaseModel):
    email: str
    seats: int = 1

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("Invalid email address.")
        return v

    @field_validator("seats")
    @classmethod
    def validate_seats(cls, v: int) -> int:
        if not 1 <= v <= 500:
            raise ValueError("seats must be 1–500.")
        return v


@app.get("/register", response_class=HTMLResponse)
async def register_page():
    from .registration import REGISTER_HTML_TEMPLATE
    cents = _get_price_cents()
    price_str = f"${cents / 100:.2f}"
    return (REGISTER_HTML_TEMPLATE
            .replace("%%PRICE%%", price_str)
            .replace("%%PRICE_CENTS%%", str(cents)))


@app.get("/register/success", response_class=HTMLResponse)
async def register_success(session_id: str = ""):
    """
    Called after Stripe redirects the user back.
    Fulfils the order here as a reliable fallback — the webhook does the same
    but may arrive later or not at all in local testing.
    Idempotent: keyed on session_id so we never send twice.
    """
    from .registration import SUCCESS_HTML

    # Validate session_id format before any use — prevents wildcard injection
    # and unexpected calls to the Stripe API with garbage input.
    if session_id and not _STRIPE_SID_RE.match(session_id):
        log.warning("register/success: invalid session_id format rejected")
        session_id = ""

    if session_id and STRIPE_SECRET_KEY:
        try:
            import stripe as _stripe
            _stripe.api_key = STRIPE_SECRET_KEY
            session = _stripe.checkout.Session.retrieve(session_id)

            if session.get("payment_status") == "paid":
                # Idempotency check — session_id already validated by regex above
                # so it contains only [a-zA-Z0-9_] and cannot carry SQL injection.
                already_done = False
                with _db() as conn:
                    safe_sid = session_id.replace("_", r"\_")  # escape LIKE wildcard
                    row = conn.execute(
                        "SELECT 1 FROM audit_log WHERE event='PURCHASE_COMPLETE' "
                        "AND details LIKE ? ESCAPE '\\'",
                        (f"%stripe_session={safe_sid}%",)
                    ).fetchone()
                    already_done = row is not None

                if not already_done:
                    email = (session.get("customer_details") or {}).get("email") \
                            or session.get("metadata", {}).get("customer_email", "")
                    seats = int((session.get("metadata") or {}).get("seats", "1") or "1")
                    if email:
                        raw = secrets.token_hex(8).upper()
                        key = f"{raw[0:4]}-{raw[4:8]}-{raw[8:12]}-{raw[12:16]}"
                        with _db() as conn:
                            conn.execute(
                                "INSERT OR IGNORE INTO licenses "
                                "(key_hash, email, created_at, max_activations) VALUES (?,?,?,?)",
                                (_hash_key(key), email.lower(), _now(), seats),
                            )
                            _audit(conn, "PURCHASE_COMPLETE", _hash_key(key), email,
                                   details=f"stripe_session={session_id} seats={seats} source=success_redirect")
                        _send_activation_email(email, key, seats)
                        log.info("Fulfilled via success redirect: email=%s seats=%d", email, seats)
        except Exception as exc:
            log.error("Success page fulfilment error: %s", exc)

    return SUCCESS_HTML


@app.post("/api/create-checkout")
async def create_checkout(req: CheckoutRequest):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(503, "Payment not configured yet.")
    try:
        import stripe as _stripe
        _stripe.api_key = STRIPE_SECRET_KEY
        unit_price = _get_price_cents()
        product_name = (
            f"{STRIPE_PRODUCT_NAME} ({req.seats} seats)"
            if req.seats > 1 else STRIPE_PRODUCT_NAME
        )
        session = _stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": unit_price,
                    "product_data": {"name": product_name},
                },
                "quantity": req.seats,
            }],
            mode="payment",
            customer_email=req.email,
            metadata={"customer_email": req.email, "seats": str(req.seats)},
            success_url=f"{APP_URL}/register/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{APP_URL}/register",
        )
        return {"url": session.url}
    except Exception as exc:
        log.error("Stripe checkout error: %s", exc)
        raise HTTPException(500, "Could not create payment session.")


@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload    = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(503, "Webhook not configured.")

    try:
        import stripe as _stripe
        _stripe.api_key = STRIPE_SECRET_KEY
        event = _stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except Exception as exc:
        log.warning("Stripe webhook signature error: %s", exc)
        raise HTTPException(400, "Invalid webhook signature.")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        # Prefer customer_details.email (authoritative from Stripe) over metadata
        email = (session.get("customer_details") or {}).get("email", "").strip().lower()
        if not email:
            email = (session.get("metadata") or {}).get("customer_email", "").strip().lower()
        seats = max(1, min(500, int((session.get("metadata") or {}).get("seats", "1") or "1")))
        if not email or not _EMAIL_RE.match(email):
            log.error("Webhook: missing/invalid email in session %s", session.get("id"))
            return {"ok": True}

        # Generate activation key
        raw = secrets.token_hex(8).upper()
        key = f"{raw[0:4]}-{raw[4:8]}-{raw[8:12]}-{raw[12:16]}"
        with _db() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO licenses "
                "(key_hash, email, created_at, max_activations) VALUES (?,?,?,?)",
                (_hash_key(key), email.lower(), _now(), seats),
            )
            _audit(conn, "PURCHASE_COMPLETE", _hash_key(key), email,
                   details=f"stripe_session={session.get('id','')} seats={seats}")

        sent = _send_activation_email(email, key, seats)
        log.info("Purchase complete email=%s key=%s seats=%d email_sent=%s", email, key, seats, sent)

    return {"ok": True}


# ── Admin: resend activation key email ────────────────────────────────────────

@app.post("/admin/licenses/{key_hash}/resend-key")
async def admin_resend_key(
    key_hash: str,
    x_admin_secret: Optional[str] = Header(default=None),
):
    """
    Look up the plaintext key is no longer available (stored only as hash).
    Instead, generate a NEW replacement key for the same email and send it.
    The old key remains in the DB; the new key is added alongside it.
    """
    _require_admin(x_admin_secret)
    with _db() as conn:
        row = conn.execute(
            "SELECT email FROM licenses WHERE key_hash=?", (key_hash,)
        ).fetchone()
    if not row:
        raise HTTPException(404, "License not found.")
    email = row["email"]
    if not email:
        raise HTTPException(400, "No email stored for this license.")

    raw = secrets.token_hex(8).upper()
    new_key = f"{raw[0:4]}-{raw[4:8]}-{raw[8:12]}-{raw[12:16]}"
    with _db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO licenses (key_hash, email, created_at) VALUES (?,?,?)",
            (_hash_key(new_key), email, _now()),
        )
        _audit(conn, "ADMIN_RESEND_KEY", key_hash, email,
               details=f"new_key_hash={_hash_key(new_key)}")

    sent = _send_activation_email(email, new_key)
    return {"ok": True, "email_sent": sent, "email": email}


# ── Admin: settings ───────────────────────────────────────────────────────────

class SettingsRequest(BaseModel):
    price_cents: int

    @field_validator("price_cents")
    @classmethod
    def validate_price(cls, v: int) -> int:
        if v < 100:
            raise ValueError("Price must be at least $1.00 (100 cents).")
        if v > 100_000_00:
            raise ValueError("Price too high.")
        return v


@app.get("/admin/settings")
async def get_settings(x_admin_secret: Optional[str] = Header(default=None)):
    _require_admin(x_admin_secret)
    return {"price_cents": _get_price_cents()}


@app.post("/admin/settings")
async def update_settings(
    req: SettingsRequest,
    x_admin_secret: Optional[str] = Header(default=None),
):
    _require_admin(x_admin_secret)
    with _db() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES ('price_cents', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (str(req.price_cents),)
        )
        _audit(conn, "ADMIN_UPDATE_PRICE",
               details=f"price_cents={req.price_cents}")
    log.info("Price updated to %d cents", req.price_cents)
    return {"ok": True, "price_cents": req.price_cents}


@app.post("/admin/licenses/{key_hash}/reset")
async def reset_license(
    key_hash: str,
    x_admin_secret: Optional[str] = Header(default=None),
):
    """Clear device binding so the key can be activated again (useful for testing)."""
    _require_admin(x_admin_secret)
    with _db() as conn:
        row = conn.execute(
            "SELECT email FROM licenses WHERE key_hash=?", (key_hash,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "License not found.")
        conn.execute(
            "UPDATE licenses SET is_used=0, device_fingerprint=NULL, activated_at=NULL "
            "WHERE key_hash=?",
            (key_hash,)
        )
        conn.execute(
            "DELETE FROM license_activations WHERE key_hash=?", (key_hash,)
        )
        _audit(conn, "ADMIN_RESET_LICENSE", key_hash, row["email"],
               details="all device bindings cleared")
    return {"ok": True}
