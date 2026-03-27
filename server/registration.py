"""
Public-facing registration and purchase pages for PDF Merger.

Routes (registered in main.py):
  GET  /register               — purchase page
  POST /api/create-checkout    — create Stripe Checkout session
  GET  /register/success       — post-payment confirmation page
  POST /stripe/webhook         — Stripe webhook (key generation + email)
"""

REGISTER_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PDF Merger — Get Your License</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #0f1117; --surface: #1a1d27; --border: #2a2d3a;
    --accent: #4f7ef7; --text: #e2e8f0; --muted: #8892a4;
    --radius: 10px; --font: 'Inter', system-ui, sans-serif;
  }
  body { background: var(--bg); color: var(--text);
         font-family: var(--font); min-height: 100vh;
         display: flex; align-items: center; justify-content: center;
         padding: 24px; }
  .card { background: var(--surface); border: 1px solid var(--border);
          border-radius: 16px; padding: 48px 44px; width: 100%;
          max-width: 460px; }
  h1 { font-size: 26px; font-weight: 700; margin-bottom: 6px; }
  .sub { color: var(--accent); font-size: 14px; font-weight: 600;
         letter-spacing: .4px; margin-bottom: 28px; }
  .features { list-style: none; margin-bottom: 32px; }
  .features li { padding: 7px 0; font-size: 14px; color: var(--muted);
                 display: flex; align-items: center; gap: 10px; }
  .features li::before { content: ''; width: 18px; height: 18px; flex-shrink: 0;
    background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20' fill='%234f7ef7'%3E%3Cpath fill-rule='evenodd' d='M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z' clip-rule='evenodd'/%3E%3C/svg%3E") center/contain no-repeat; }
  .price-row { display: flex; align-items: baseline; gap: 8px; margin-bottom: 24px; }
  .price { font-size: 40px; font-weight: 800; }
  .price-note { color: var(--muted); font-size: 13px; }
  label { display: block; font-size: 12px; color: var(--muted);
          font-weight: 600; text-transform: uppercase; letter-spacing: .4px;
          margin-bottom: 6px; }
  input[type=email], select {
    width: 100%; padding: 12px 14px;
    background: var(--bg); border: 1px solid var(--border);
    border-radius: var(--radius); color: var(--text);
    font-size: 15px; font-family: inherit; outline: none;
    transition: border .15s;
  }
  input[type=email] { margin-bottom: 16px; }
  input[type=email]:focus, select:focus { border-color: var(--accent); }
  select { margin-bottom: 16px; cursor: pointer; }
  .seat-row { display: flex; gap: 12px; margin-bottom: 16px; align-items: flex-end; }
  .seat-row .field { flex: 1; }
  .total-box { background: rgba(79,126,247,.08); border: 1px solid rgba(79,126,247,.25);
               border-radius: var(--radius); padding: 12px 16px; margin-bottom: 20px;
               font-size: 14px; color: var(--text); }
  .total-box span { color: var(--accent); font-weight: 700; font-size: 18px; }
  .btn { width: 100%; padding: 14px; background: var(--accent);
         color: #fff; border: none; border-radius: var(--radius);
         font-size: 16px; font-weight: 700; cursor: pointer;
         transition: opacity .15s; font-family: inherit; }
  .btn:hover:not(:disabled) { opacity: .88; }
  .btn:disabled { opacity: .5; cursor: not-allowed; }
  .error { color: #ef4444; font-size: 13px; margin-top: 10px; min-height: 20px; }
  .footer { margin-top: 20px; text-align: center; }
  .footer p { font-size: 12px; color: var(--muted); line-height: 1.7; }
  .divider { height: 1px; background: var(--border); margin: 28px 0; }
</style>
</head>
<body>
<div class="card">
  <h1>PDF Merger</h1>
  <p class="sub">Lifetime License</p>

  <ul class="features">
    <li>Merge, split, compress and convert PDFs</li>
    <li>100% offline — your files never leave your device</li>
    <li>One-time payment, no subscription</li>
    <li>One key activates on multiple computers (choose seats below)</li>
  </ul>

  <div class="divider"></div>

  <div class="price-row">
    <span class="price" id="unit-price">%%PRICE%%</span>
    <span class="price-note">per seat · one-time · lifetime</span>
  </div>

  <label for="email">Email address</label>
  <input type="email" id="email" placeholder="you@example.com">

  <label for="seats" style="margin-top:4px">Number of seats (computers)</label>
  <select id="seats" onchange="updateTotal()">
    <option value="1">1 seat — single computer</option>
    <option value="2">2 seats — e.g. desktop + laptop</option>
    <option value="3">3 seats</option>
    <option value="5">5 seats — small team</option>
    <option value="10">10 seats</option>
    <option value="25">25 seats</option>
    <option value="50">50 seats</option>
  </select>

  <div class="total-box">
    Total: <span id="total-price">%%PRICE%%</span>
    &nbsp;<span style="color:var(--muted);font-size:13px;font-weight:400" id="seat-desc">for 1 seat</span>
  </div>

  <button class="btn" id="buy-btn" onclick="buy()">
    Buy Now — <span id="btn-price">%%PRICE%%</span>
  </button>

  <p class="error" id="err"></p>

  <div class="footer">
    <p>One key, shared with your team. Each machine activates with the same key and email.<br>
       Your activation key will be emailed immediately after payment.<br>
       Secure payment via Stripe. We never store card details.</p>
  </div>
</div>

<script>
const UNIT_CENTS = %%PRICE_CENTS%%;

function fmt(cents) {
  return '$' + (cents / 100).toFixed(2);
}

function updateTotal() {
  const seats = parseInt(document.getElementById('seats').value) || 1;
  const total = UNIT_CENTS * seats;
  document.getElementById('total-price').textContent = fmt(total);
  document.getElementById('btn-price').textContent   = fmt(total);
  document.getElementById('seat-desc').textContent   =
    seats === 1 ? 'for 1 seat' : `for ${seats} seats`;
}

async function buy() {
  const email = document.getElementById('email').value.trim();
  const seats = parseInt(document.getElementById('seats').value) || 1;
  const err   = document.getElementById('err');
  err.textContent = '';
  if (!email || !email.includes('@')) {
    err.textContent = 'Please enter a valid email address.';
    return;
  }
  const btn = document.getElementById('buy-btn');
  btn.disabled = true;
  btn.querySelector('span').textContent = 'Redirecting to payment...';
  try {
    const resp = await fetch('/api/create-checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, seats }),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || 'Server error.');
    // Validate redirect is to Stripe — never follow an unexpected URL
    if (!data.url || !data.url.startsWith('https://checkout.stripe.com/')) {
      throw new Error('Unexpected redirect target. Please contact support.');
    }
    window.location.href = data.url;
  } catch(e) {
    err.textContent = e.message;
    btn.disabled = false;
    btn.querySelector('span').textContent = fmt(UNIT_CENTS * seats);
  }
}
</script>
</body>
</html>
"""

SUCCESS_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PDF Merger — Thank You!</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root { --bg: #0f1117; --surface: #1a1d27; --border: #2a2d3a;
          --accent2: #22c55e; --text: #e2e8f0; --muted: #8892a4; }
  body { background: var(--bg); color: var(--text);
         font-family: 'Inter', system-ui, sans-serif;
         min-height: 100vh; display: flex;
         align-items: center; justify-content: center; padding: 24px; }
  .card { background: var(--surface); border: 1px solid var(--border);
          border-radius: 16px; padding: 52px 44px; max-width: 440px;
          width: 100%; text-align: center; }
  .check { width: 64px; height: 64px; background: rgba(34,197,94,.15);
           border-radius: 50%; display: flex; align-items: center;
           justify-content: center; margin: 0 auto 24px; }
  .check svg { width: 32px; height: 32px; }
  h1 { font-size: 24px; font-weight: 700; margin-bottom: 12px; }
  p  { color: var(--muted); font-size: 14px; line-height: 1.7; }
  .note { margin-top: 24px; background: var(--bg); border: 1px solid var(--border);
          border-radius: 8px; padding: 16px; font-size: 13px;
          color: var(--muted); line-height: 1.7; text-align: left; }
</style>
</head>
<body>
<div class="card">
  <div class="check">
    <svg viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5"
         stroke-linecap="round" stroke-linejoin="round">
      <polyline points="20 6 9 17 4 12"/>
    </svg>
  </div>
  <h1>Payment Successful!</h1>
  <p>Thank you for purchasing PDF Merger.<br>
     Your activation key has been sent to your email address.</p>
  <div class="note">
    <strong style="color:#e2e8f0">Next steps:</strong><br>
    1. Check your inbox (and spam folder) for an email from us.<br>
    2. Open PDF Merger — the activation dialog will appear.<br>
    3. Enter your email and the activation key from the email.<br>
    4. Done — you're activated for life on this device.
  </div>
</div>
</body>
</html>
"""
