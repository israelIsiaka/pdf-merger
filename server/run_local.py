#!/usr/bin/env python3
"""
Local test runner for the PDF Merger activation server.

Run from the project root:
    python server/run_local.py

What this does:
  1. Generates temporary Ed25519 + X25519 key pairs (in-memory, for this session)
  2. Prints the public keys so you can paste them into src/license.py
  3. Starts the server on http://localhost:8765
  4. Sets LOCAL_TEST_MODE=1 so plain HTTP is accepted
  5. Pre-seeds one test activation key: TEST-1234-ABCD-5678

The server uses a local SQLite database at server/licenses_test.db.
Delete that file to reset between test sessions.

In src/license.py set:
    ACTIVATION_SERVER_URL = "http://localhost:8765"
    LOCAL_TEST_MODE = True          # allows HTTP
and paste the public keys printed below.

IMPORTANT: These test keys are regenerated every time you run this script.
           Use keygen_keys.py once to generate permanent keys for production.
"""

import os
import sys

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load server/.env.local if it exists (local secrets, never committed)
_env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env.local")
if os.path.exists(_env_file):
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

from base64 import b64encode
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding, NoEncryption, PrivateFormat, PublicFormat,
)


def main():
    # ── Generate ephemeral test key pairs ────────────────────────────────────
    sign_priv   = Ed25519PrivateKey.generate()
    enc_priv    = X25519PrivateKey.generate()

    sign_priv_b64 = b64encode(sign_priv.private_bytes(
        Encoding.Raw, PrivateFormat.Raw, NoEncryption())).decode()
    enc_priv_b64  = b64encode(enc_priv.private_bytes(
        Encoding.Raw, PrivateFormat.Raw, NoEncryption())).decode()
    sign_pub_b64  = b64encode(
        sign_priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)).decode()
    enc_pub_b64   = b64encode(
        enc_priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)).decode()

    # ── Set environment variables for the server process ─────────────────────
    os.environ["SECRET_KEY_B64"]        = sign_priv_b64
    os.environ["ENCRYPT_KEY_B64"]       = enc_priv_b64
    os.environ["ADMIN_SECRET"]          = "local-admin-secret"
    os.environ["DATABASE_URL"]          = "server/licenses_test.db"
    os.environ["LOCAL_TEST_MODE"]       = "1"
    os.environ["APP_URL"]               = "http://localhost:8765"
    # Stripe — set your test keys here for local testing
    os.environ.setdefault("STRIPE_SECRET_KEY",     "sk_test_REPLACE_ME")
    os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_REPLACE_ME")
    os.environ.setdefault("STRIPE_PRICE_CENTS",    "2900")
    # Resend — set your API key here for local testing
    os.environ.setdefault("RESEND_API_KEY", "re_REPLACE_ME")
    os.environ.setdefault("FROM_EMAIL",     "onboarding@resend.dev")

    sep = "=" * 64
    print(sep)
    print("  PDF Merger — Local Test Server")
    print(sep)
    print()
    print("Paste these into  src/license.py  for local testing:")
    print()
    print(f'  _SIGN_PUBLIC_KEY_B64    = "{sign_pub_b64}"')
    print(f'  _ENCRYPT_PUBLIC_KEY_B64 = "{enc_pub_b64}"')
    print(f'  ACTIVATION_SERVER_URL   = "http://localhost:8765"')
    print()
    print("Admin secret (for curl commands below): local-admin-secret")
    print()
    print("Test activation key pre-seeded: TEST-1234-ABCD-5678")
    print("Use email: test@example.com  when activating")
    print()
    print(sep)
    print("Server: http://localhost:8765")
    print(sep)
    print()

    # ── Seed test key into the database ──────────────────────────────────────
    import hashlib, sqlite3, datetime, pathlib
    pathlib.Path("server").mkdir(exist_ok=True)
    db = sqlite3.connect("server/licenses_test.db")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            key_hash TEXT PRIMARY KEY, email TEXT NOT NULL DEFAULT '',
            device_fingerprint TEXT, activated_at TEXT,
            is_used INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            max_transfers INTEGER NOT NULL DEFAULT 3
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS transfer_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_hash TEXT NOT NULL, email TEXT NOT NULL,
            old_device TEXT, new_device TEXT, reason TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            requested_at TEXT, resolved_at TEXT,
            resolved_by TEXT, transfer_count INTEGER NOT NULL DEFAULT 0
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL, key_hash TEXT, email TEXT,
            ip_address TEXT, details TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    test_hash = hashlib.sha256(b"TEST-1234-ABCD-5678").hexdigest()
    db.execute(
        "INSERT OR IGNORE INTO licenses (key_hash, email, created_at) VALUES (?,?,?)",
        (test_hash, "test@example.com",
         datetime.datetime.now(datetime.timezone.utc).isoformat()),
    )
    db.commit()
    db.close()

    # ── Start uvicorn ─────────────────────────────────────────────────────────
    import uvicorn
    uvicorn.run(
        "server.main:app",
        host="127.0.0.1",
        port=8765,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
