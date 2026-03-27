"""
Generate the Ed25519 (signing) and X25519 (encryption) key pairs.

Run ONCE before deploying:
    python server/keygen_keys.py

Output:
  PUBLIC keys  → paste into src/license.py
  PRIVATE keys → set as environment variables on your server ONLY

NEVER commit private keys. NEVER share them.
"""

from base64 import b64encode
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding, NoEncryption, PrivateFormat, PublicFormat,
)


def generate():
    # Ed25519 — used to sign license tokens
    sign_priv   = Ed25519PrivateKey.generate()
    sign_pub    = sign_priv.public_key()
    sign_priv_b = b64encode(sign_priv.private_bytes(
        Encoding.Raw, PrivateFormat.Raw, NoEncryption())).decode()
    sign_pub_b  = b64encode(sign_pub.public_bytes(
        Encoding.Raw, PublicFormat.Raw)).decode()

    # X25519 — used to encrypt activation request payloads
    enc_priv   = X25519PrivateKey.generate()
    enc_pub    = enc_priv.public_key()
    enc_priv_b = b64encode(enc_priv.private_bytes(
        Encoding.Raw, PrivateFormat.Raw, NoEncryption())).decode()
    enc_pub_b  = b64encode(enc_pub.public_bytes(
        Encoding.Raw, PublicFormat.Raw)).decode()

    sep = "=" * 62
    print(sep)
    print("  PDF Merger — Key Pair Generation")
    print(sep)
    print()
    print("Paste these into  src/license.py  (PUBLIC keys — not secret):")
    print()
    print(f'  _SIGN_PUBLIC_KEY_B64    = "{sign_pub_b}"')
    print(f'  _ENCRYPT_PUBLIC_KEY_B64 = "{enc_pub_b}"')
    print()
    print(sep)
    print("Set these as environment variables on your SERVER ONLY (PRIVATE keys):")
    print()
    print(f'  SECRET_KEY_B64    = "{sign_priv_b}"')
    print(f'  ENCRYPT_KEY_B64   = "{enc_priv_b}"')
    print()
    print(sep)
    print("  KEEP PRIVATE KEYS SECRET. DO NOT COMMIT THEM.")
    print(sep)


if __name__ == "__main__":
    generate()
