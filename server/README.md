# PDF Merger — Activation Server

## First-time setup

```bash
# 1. Install dependencies
pip install -r server/requirements.txt

# 2. Generate your Ed25519 key pair (run ONCE)
python server/keygen_keys.py
#   → Copy the PUBLIC key into src/license.py (_PUBLIC_KEY_B64)
#   → Set the PRIVATE key as SECRET_KEY_B64 on your hosting platform

# 3. Set environment variables
export SECRET_KEY_B64="<your private key>"
export ADMIN_SECRET="<choose a strong secret>"

# 4. Run the server
uvicorn server.main:app --host 0.0.0.0 --port 8000
```

## Generating activation keys

```bash
# Generate 10 keys (requires ADMIN_SECRET header)
curl -X POST http://localhost:8000/admin/generate-keys \
     -H "Content-Type: application/json" \
     -H "X-Admin-Secret: your-admin-secret" \
     -d '{"count": 10}'
```

Each key looks like: `A1B2-C3D4-E5F6-G7H8`

Send keys to customers after payment (e.g. via Gumroad, Stripe, or manual email).

## Deploying (free tier options)

| Platform | Free tier | Deploy command |
|---|---|---|
| [Railway](https://railway.app) | 500 hrs/month | Connect GitHub repo |
| [Render](https://render.com) | 750 hrs/month | Connect GitHub repo |
| [Fly.io](https://fly.io) | 3 shared VMs | `fly launch` |

Set `SECRET_KEY_B64` and `ADMIN_SECRET` as environment variables in your
hosting platform's dashboard — never in code or committed files.

## Security notes

- Keys are stored as SHA-256 hashes in the database — never plaintext
- Each key is bound to one device fingerprint on first activation
- The signed token uses Ed25519 — impossible to forge without the private key
- Re-activation on the **same** device is allowed (app reinstall / token deleted)
- Re-activation on a **different** device is blocked (returns HTTP 409)
- To transfer a license (e.g. new computer), reset via the database manually
