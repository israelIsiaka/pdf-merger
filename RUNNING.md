# PDF Merger — How to Start and Stop

Two separate processes make up the full application:

| Process | What it does | Required for |
|---------|-------------|--------------|
| **Desktop app** | The PyQt6 GUI users interact with | PDF tools, activation dialog |
| **License server** | FastAPI backend (activation, payments, admin) | Activating licenses, selling new ones |

---

## Desktop App

### Start

```bash
cd /Users/user/pdf-merger
python -m src.app
```

The app opens as a window. On first launch it shows the activation dialog.

### Stop

Close the window, or press `Cmd+Q` (macOS) / `Alt+F4` (Windows/Linux).

To force-kill from terminal:

```bash
pkill -f "src.app"
```

---

## License Server (local development)

### Start

```bash
cd /Users/user/pdf-merger
python -m server.run_local
```

The server prints two public keys and a test activation key on startup. **Copy the public keys into `src/license.py` each time you restart** — new keys are generated on every run in local mode.

```
_SIGN_PUBLIC_KEY_B64    = "..."   # paste into src/license.py
_ENCRYPT_PUBLIC_KEY_B64 = "..."   # paste into src/license.py
```

Runs on **http://localhost:8765**

| URL | What it is |
|-----|-----------|
| http://localhost:8765/health | Health check |
| http://localhost:8765/register | Purchase page (seat picker + Stripe) |
| http://localhost:8765/admin | Admin dashboard |

Admin secret for local testing: `local-admin-secret`

### Stop

Press `Ctrl+C` in the terminal running the server, or:

```bash
lsof -ti :8765 | xargs kill -9
# or
pkill -f "server.run_local"
```

---

## Start Both Together (dev shortcut)

```bash
cd /Users/user/pdf-merger

# Terminal 1 — server
python -m server.run_local

# Terminal 2 — desktop app (after pasting keys from Terminal 1 output)
python -m src.app
```

---

## Production Server (Railway / Render / Fly.io)

### Start

Railway auto-starts on deploy using `railway.toml`:

```toml
[deploy]
startCommand = "uvicorn server.main:app --host 0.0.0.0 --port $PORT"
```

To deploy:

```bash
git push origin main   # Railway auto-deploys on push
```

To restart the deployed server:

```bash
railway service restart   # if using Railway CLI
```

### Stop

In the Railway dashboard: **Settings → Danger Zone → Sleep service** (or delete deployment).

---

## Environment Variables (production)

Set these in your hosting platform dashboard — never commit them:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY_B64` | Ed25519 private key (from `python server/keygen_keys.py`) |
| `ENCRYPT_KEY_B64` | X25519 private key (from `python server/keygen_keys.py`) |
| `ADMIN_SECRET` | Strong random string — protects `/admin` |
| `STRIPE_SECRET_KEY` | From Stripe dashboard (starts `sk_live_...`) |
| `STRIPE_WEBHOOK_SECRET` | From Stripe webhook settings (starts `whsec_...`) |
| `RESEND_API_KEY` | From Resend dashboard |
| `FROM_EMAIL` | Verified sender email on Resend |
| `APP_URL` | Your deployed server URL e.g. `https://pdf-merger.up.railway.app` |
| `TRUST_PROXY` | Set to `1` on Railway/Render so `X-Forwarded-For` is trusted for rate limiting |

### Generate production keys (run once)

```bash
python server/keygen_keys.py
```

Copy the **public** keys into `src/license.py` before distributing the desktop app.
Store the **private** keys as environment variables — never in code.

---

## Checking What Is Running

```bash
# Is the server running?
lsof -i :8765

# Is the desktop app running?
pgrep -fl "src.app"

# Server health check
curl http://localhost:8765/health
```
