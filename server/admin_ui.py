"""
Admin dashboard HTML — served at GET /admin by the FastAPI app.
Pure HTML + vanilla JS, no extra dependencies.
The admin secret is entered once and stored in sessionStorage.
"""

ADMIN_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PDF Merger — Admin</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #0f1117; --surface: #1a1d27; --border: #2a2d3a;
    --accent: #4f7ef7; --accent2: #22c55e; --danger: #ef4444;
    --warn: #f59e0b; --text: #e2e8f0; --muted: #8892a4;
    --radius: 8px; --font: 'Inter', system-ui, sans-serif;
  }
  body { background: var(--bg); color: var(--text); font-family: var(--font);
         font-size: 14px; min-height: 100vh; }

  /* ── Login ── */
  #login-screen { display: flex; align-items: center; justify-content: center;
                  min-height: 100vh; }
  .login-card { background: var(--surface); border: 1px solid var(--border);
                border-radius: 12px; padding: 40px; width: 360px; text-align: center; }
  .login-card h1 { font-size: 22px; margin-bottom: 6px; }
  .login-card p  { color: var(--muted); margin-bottom: 24px; font-size: 13px; }
  input[type=password], input[type=text], input[type=email], input[type=number],
  select, textarea {
    width: 100%; padding: 10px 12px; background: var(--bg);
    border: 1px solid var(--border); border-radius: var(--radius);
    color: var(--text); font-size: 14px; font-family: inherit;
    outline: none; transition: border .15s;
  }
  input:focus, select:focus, textarea:focus { border-color: var(--accent); }
  textarea { resize: vertical; }

  /* ── Buttons ── */
  .btn { display: inline-flex; align-items: center; gap: 6px; cursor: pointer;
         border: none; border-radius: var(--radius); font-size: 13px;
         font-weight: 600; padding: 8px 16px; transition: opacity .15s; }
  .btn:hover { opacity: .85; }
  .btn-primary { background: var(--accent); color: #fff; }
  .btn-success { background: var(--accent2); color: #fff; }
  .btn-danger  { background: var(--danger);  color: #fff; }
  .btn-warn    { background: var(--warn);    color: #000; }
  .btn-ghost   { background: var(--border);  color: var(--text); }
  .btn-sm { padding: 5px 10px; font-size: 12px; }
  .btn-full { width: 100%; justify-content: center; margin-top: 12px; }

  /* ── Layout ── */
  #app { display: none; }
  .topbar { background: var(--surface); border-bottom: 1px solid var(--border);
            padding: 14px 28px; display: flex; align-items: center;
            justify-content: space-between; position: sticky; top: 0; z-index: 10; }
  .topbar h1 { font-size: 18px; }
  .topbar span { color: var(--muted); font-size: 12px; }
  .content { padding: 28px; max-width: 1200px; margin: 0 auto; }

  /* ── Tabs ── */
  .tabs { display: flex; gap: 4px; margin-bottom: 24px; border-bottom: 1px solid var(--border); }
  .tab { padding: 10px 20px; cursor: pointer; color: var(--muted);
         font-weight: 600; font-size: 13px; border-bottom: 2px solid transparent;
         transition: color .15s, border-color .15s; }
  .tab.active { color: var(--accent); border-color: var(--accent); }
  .tab-panel { display: none; }
  .tab-panel.active { display: block; }

  /* ── Stats bar ── */
  .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
           gap: 16px; margin-bottom: 28px; }
  .stat { background: var(--surface); border: 1px solid var(--border);
          border-radius: var(--radius); padding: 20px; }
  .stat .val { font-size: 28px; font-weight: 700; margin-bottom: 4px; }
  .stat .lbl { color: var(--muted); font-size: 12px; text-transform: uppercase;
               letter-spacing: .5px; }

  /* ── Cards ── */
  .card { background: var(--surface); border: 1px solid var(--border);
          border-radius: var(--radius); margin-bottom: 20px; overflow: hidden; }
  .card-head { padding: 14px 18px; border-bottom: 1px solid var(--border);
               display: flex; align-items: center; justify-content: space-between; }
  .card-head h2 { font-size: 14px; font-weight: 600; }
  .card-body { padding: 18px; }

  /* ── Tables ── */
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { text-align: left; padding: 10px 12px; color: var(--muted);
       font-size: 11px; text-transform: uppercase; letter-spacing: .5px;
       border-bottom: 1px solid var(--border); }
  td { padding: 10px 12px; border-bottom: 1px solid var(--border);
       vertical-align: middle; max-width: 260px; overflow: hidden;
       text-overflow: ellipsis; white-space: nowrap; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(255,255,255,.02); }

  /* ── Badges ── */
  .badge { display: inline-block; padding: 2px 8px; border-radius: 20px;
           font-size: 11px; font-weight: 600; }
  .badge-green  { background: rgba(34,197,94,.15);  color: #22c55e; }
  .badge-red    { background: rgba(239,68,68,.15);   color: #ef4444; }
  .badge-yellow { background: rgba(245,158,11,.15);  color: #f59e0b; }
  .badge-blue   { background: rgba(79,126,247,.15);  color: #4f7ef7; }
  .badge-gray   { background: rgba(136,146,164,.15); color: #8892a4; }

  /* ── Form row ── */
  .form-row { display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap; }
  .form-group { display: flex; flex-direction: column; gap: 6px; }
  .form-group label { font-size: 12px; color: var(--muted); font-weight: 600;
                      text-transform: uppercase; letter-spacing: .4px; }

  /* ── Misc ── */
  .mono { font-family: monospace; font-size: 12px; }
  .muted { color: var(--muted); }
  .mt { margin-top: 12px; }
  .key-list { background: var(--bg); border: 1px solid var(--border);
              border-radius: var(--radius); padding: 14px;
              font-family: monospace; font-size: 13px; line-height: 2; margin-top: 14px; }
  #toast { position: fixed; bottom: 24px; right: 24px; padding: 12px 20px;
           background: #22c55e; color: #fff; border-radius: var(--radius);
           font-weight: 600; font-size: 13px; display: none; z-index: 999; }
  #toast.err { background: var(--danger); }
  .empty { color: var(--muted); font-size: 13px; padding: 20px 0; text-align: center; }
  .spin { animation: spin 1s linear infinite; display: inline-block; }
  @keyframes spin { to { transform: rotate(360deg); } }
  /* ── Device rows ── */
  .devices-row td { background: rgba(79,126,247,.04); padding: 0; }
  .devices-inner { padding: 10px 16px 14px 40px; }
  .devices-inner table { background: transparent; }
  .devices-inner th { color: var(--muted); font-size: 10px; }
  .devices-inner td { font-size: 12px; border-bottom: 1px solid rgba(255,255,255,.04); }
</style>
</head>
<body>

<!-- ── Login ───────────────────────────────────────────────────────────────── -->
<div id="login-screen">
  <div class="login-card">
    <h1>PDF Merger Admin</h1>
    <p>Enter your admin secret to continue</p>
    <input type="password" id="secret-input" placeholder="Admin secret"
           onkeydown="if(event.key==='Enter')login()">
    <button class="btn btn-primary btn-full" onclick="login()">Sign In</button>
    <p id="login-err" style="color:var(--danger);margin-top:12px;font-size:13px"></p>
  </div>
</div>

<!-- ── App ─────────────────────────────────────────────────────────────────── -->
<div id="app">
  <div class="topbar">
    <h1>PDF Merger Admin</h1>
    <div style="display:flex;gap:12px;align-items:center">
      <span id="server-url-label"></span>
      <button class="btn btn-ghost btn-sm" onclick="logout()">Sign Out</button>
    </div>
  </div>

  <div class="content">
    <!-- Stats -->
    <div class="stats" id="stats">
      <div class="stat"><div class="val" id="s-purchases" style="color:var(--accent)">-</div><div class="lbl">Total Purchases</div></div>
      <div class="stat"><div class="val" id="s-total">-</div><div class="lbl">Total Licenses</div></div>
      <div class="stat"><div class="val" id="s-active" style="color:var(--accent2)">-</div><div class="lbl">Activated</div></div>
      <div class="stat"><div class="val" id="s-unused" style="color:var(--muted)">-</div><div class="lbl">Unused</div></div>
      <div class="stat"><div class="val" id="s-pending" style="color:var(--warn)">-</div><div class="lbl">Pending Transfers</div></div>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <div class="tab active" onclick="switchTab('transfers')">Transfer Requests</div>
      <div class="tab" onclick="switchTab('purchases')">Purchases</div>
      <div class="tab" onclick="switchTab('licenses')">All Licenses</div>
      <div class="tab" onclick="switchTab('generate')">Generate Keys</div>
      <div class="tab" onclick="switchTab('audit')">Audit Log</div>
      <div class="tab" onclick="switchTab('settings')">Settings</div>
    </div>

    <!-- Transfers tab -->
    <div class="tab-panel active" id="panel-transfers">
      <div class="card">
        <div class="card-head">
          <h2>Transfer Requests</h2>
          <div style="display:flex;gap:8px">
            <select id="filter-status" onchange="loadTransfers()" style="width:140px">
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
              <option value="all">All</option>
            </select>
            <button class="btn btn-ghost btn-sm" onclick="loadTransfers()">Refresh</button>
          </div>
        </div>
        <div id="transfers-body"></div>
      </div>
    </div>

    <!-- Purchases tab -->
    <div class="tab-panel" id="panel-purchases">
      <div class="card">
        <div class="card-head">
          <h2>Purchases</h2>
          <button class="btn btn-ghost btn-sm" onclick="loadPurchases()">Refresh</button>
        </div>
        <div id="purchases-body"></div>
      </div>
    </div>

    <!-- Licenses tab -->
    <div class="tab-panel" id="panel-licenses">
      <div class="card">
        <div class="card-head">
          <h2>All Licenses</h2>
          <button class="btn btn-ghost btn-sm" onclick="loadLicenses()">Refresh</button>
        </div>
        <div id="licenses-body"></div>
      </div>
    </div>

    <!-- Generate tab -->
    <div class="tab-panel" id="panel-generate">
      <div class="card">
        <div class="card-head"><h2>Generate Activation Keys</h2></div>
        <div class="card-body">
          <p class="muted" style="margin-bottom:18px">
            Keys are returned once in plaintext — copy them immediately.
            They are stored only as hashes in the database.
          </p>
          <div class="form-row">
            <div class="form-group">
              <label>Customer Email (optional)</label>
              <input type="email" id="gen-email" placeholder="customer@example.com" style="width:240px">
            </div>
            <div class="form-group">
              <label>Number of Keys</label>
              <input type="number" id="gen-count" value="1" min="1" max="100" style="width:90px">
            </div>
            <div class="form-group">
              <label>Seats per Key</label>
              <input type="number" id="gen-seats" value="1" min="1" max="1000" style="width:90px"
                     title="How many devices each key can activate">
            </div>
            <button class="btn btn-primary" onclick="generateKeys()">Generate Keys</button>
          </div>
          <div id="gen-result"></div>
        </div>
      </div>
    </div>

    <!-- Settings tab -->
    <div class="tab-panel" id="panel-settings">
      <div class="card">
        <div class="card-head"><h2>Settings</h2></div>
        <div class="card-body">
          <div class="form-row" style="align-items:flex-end;gap:16px;flex-wrap:wrap">
            <div class="form-group">
              <label>License Price (USD)</label>
              <div style="display:flex;align-items:center;gap:8px">
                <span style="color:var(--muted);font-size:16px">$</span>
                <input type="number" id="price-input" min="1" step="0.01"
                       style="width:120px" placeholder="29.00">
              </div>
            </div>
            <button class="btn btn-primary" onclick="savePrice()">Save Price</button>
          </div>
          <p id="price-status" style="margin-top:12px;font-size:13px;min-height:20px"></p>
          <p class="muted" style="margin-top:16px;font-size:12px;line-height:1.7">
            This price is used for all new purchases via the app and the /register page.<br>
            Changes take effect immediately — no restart required.
          </p>
        </div>
      </div>
    </div>

    <!-- Audit tab -->
    <div class="tab-panel" id="panel-audit">
      <div class="card">
        <div class="card-head">
          <h2>Audit Log</h2>
          <div style="display:flex;gap:8px;align-items:center">
            <select id="audit-limit" onchange="loadAudit()" style="width:100px">
              <option value="50">Last 50</option>
              <option value="100" selected>Last 100</option>
              <option value="500">Last 500</option>
            </select>
            <button class="btn btn-ghost btn-sm" onclick="loadAudit()">Refresh</button>
          </div>
        </div>
        <div id="audit-body"></div>
      </div>
    </div>
  </div>
</div>

<div id="toast"></div>

<script>
// ── State ──────────────────────────────────────────────────────────────────
let ADMIN_SECRET = '';
const BASE = window.location.origin;

// ── Auth ───────────────────────────────────────────────────────────────────
async function login() {
  const secret = document.getElementById('secret-input').value.trim();
  if (!secret) return;
  // Test the secret against /admin/licenses
  const resp = await fetch(`${BASE}/admin/licenses`, {
    headers: { 'X-Admin-Secret': secret }
  });
  if (resp.status === 403) {
    document.getElementById('login-err').textContent = 'Incorrect admin secret.';
    return;
  }
  ADMIN_SECRET = secret;
  sessionStorage.setItem('admin_secret', secret);
  document.getElementById('login-screen').style.display = 'none';
  document.getElementById('app').style.display = 'block';
  document.getElementById('server-url-label').textContent = BASE;
  loadAll();
}

function logout() {
  sessionStorage.removeItem('admin_secret');
  ADMIN_SECRET = '';
  document.getElementById('login-screen').style.display = 'flex';
  document.getElementById('app').style.display = 'none';
  document.getElementById('secret-input').value = '';
}

// Auto-login if secret is in sessionStorage
window.addEventListener('DOMContentLoaded', () => {
  const saved = sessionStorage.getItem('admin_secret');
  if (saved) {
    document.getElementById('secret-input').value = saved;
    login();
  }
});

// ── API helper ─────────────────────────────────────────────────────────────
async function api(method, path, body) {
  const opts = {
    method,
    headers: { 'X-Admin-Secret': ADMIN_SECRET, 'Content-Type': 'application/json' }
  };
  if (body) opts.body = JSON.stringify(body);
  const resp = await fetch(BASE + path, opts);
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || resp.statusText);
  }
  return resp.json();
}

// ── Toast ──────────────────────────────────────────────────────────────────
function toast(msg, err = false) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = err ? 'err' : '';
  t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 3500);
}

// ── Tabs ───────────────────────────────────────────────────────────────────
function switchTab(name) {
  document.querySelectorAll('.tab').forEach((el, i) => {
    const panels = ['transfers','purchases','licenses','generate','audit','settings'];
    el.classList.toggle('active', panels[i] === name);
  });
  document.querySelectorAll('.tab-panel').forEach(el => {
    el.classList.toggle('active', el.id === 'panel-' + name);
  });
  if (name === 'transfers') loadTransfers();
  if (name === 'purchases') loadPurchases();
  if (name === 'licenses')  loadLicenses();
  if (name === 'audit')     loadAudit();
  if (name === 'settings')  loadSettings();
}

// ── Load all ───────────────────────────────────────────────────────────────
function loadAll() { loadStats(); loadTransfers(); }

async function loadStats() {
  try {
    const [lic, tr, pur] = await Promise.all([
      api('GET', '/admin/licenses'),
      api('GET', '/admin/transfers?status=pending'),
      api('GET', '/admin/purchases'),
    ]);
    const total      = lic.count;
    const active     = lic.licenses.filter(l => l.is_used).length;
    const totalSeats = lic.licenses.reduce((s, l) => s + (l.activation_count || 0), 0);
    document.getElementById('s-purchases').textContent = pur.count;
    document.getElementById('s-total').textContent     = total;
    document.getElementById('s-active').textContent    = `${active} (${totalSeats} seats)`;
    document.getElementById('s-unused').textContent    = total - active;
    document.getElementById('s-pending').textContent   = tr.count;
  } catch(e) { toast(e.message, true); }
}

// ── Purchases ──────────────────────────────────────────────────────────────
async function loadPurchases() {
  const el = document.getElementById('purchases-body');
  el.innerHTML = '<div class="empty">Loading...</div>';
  try {
    const data = await api('GET', '/admin/purchases');
    if (!data.purchases.length) {
      el.innerHTML = '<div class="empty">No purchases yet.</div>';
      return;
    }
    el.innerHTML = `<table>
      <thead><tr>
        <th>Date</th><th>Email</th><th>Key Hash</th>
        <th>License Status</th><th>Activated</th><th>Source</th>
      </tr></thead>
      <tbody>${data.purchases.map(p => `
        <tr>
          <td class="mono" style="white-space:nowrap">${fmtDate(p.created_at)}</td>
          <td>${p.email || '<span class="muted">—</span>'}</td>
          <td class="mono" title="${p.key_hash||''}">${p.key_hash ? p.key_hash.slice(0,14)+'…' : '—'}</td>
          <td>${p.is_used
            ? '<span class="badge badge-green">Activated</span>'
            : '<span class="badge badge-yellow">Not yet activated</span>'}</td>
          <td>${p.activated_at ? fmtDate(p.activated_at) : '<span class="muted">—</span>'}</td>
          <td class="muted" style="font-size:11px">${
            (p.details||'').includes('success_redirect') ? 'checkout redirect' : 'webhook'
          }</td>
        </tr>`).join('')}
      </tbody>
    </table>`;
  } catch(e) { el.innerHTML = `<div class="empty" style="color:var(--danger)">${e.message}</div>`; }
}

// ── Transfers ──────────────────────────────────────────────────────────────
async function loadTransfers() {
  const status = document.getElementById('filter-status').value;
  const el = document.getElementById('transfers-body');
  el.innerHTML = '<div class="empty">Loading...</div>';
  try {
    const data = await api('GET', `/admin/transfers?status=${status}`);
    if (!data.requests.length) {
      el.innerHTML = `<div class="empty">No ${status} transfer requests.</div>`;
      return;
    }
    el.innerHTML = `<table>
      <thead><tr>
        <th>#</th><th>Email</th><th>Key (hash)</th>
        <th>Reason</th><th>Requested</th><th>Status</th><th>Actions</th>
      </tr></thead>
      <tbody>${data.requests.map(r => `
        <tr>
          <td>${r.id}</td>
          <td>${r.email}</td>
          <td class="mono" title="${r.key_hash}">${r.key_hash.slice(0,12)}…</td>
          <td title="${r.reason||''}">${(r.reason||'—').slice(0,40)}</td>
          <td>${fmtDate(r.requested_at)}</td>
          <td>${statusBadge(r.status)}</td>
          <td>${r.status === 'pending' ? `
            <button class="btn btn-success btn-sm" onclick="approveTransfer(${r.id})">Approve</button>
            <button class="btn btn-danger btn-sm" style="margin-left:4px" onclick="rejectTransfer(${r.id})">Reject</button>
          ` : `<span class="muted">${r.resolved_at ? fmtDate(r.resolved_at) : '—'}</span>`}
          </td>
        </tr>`).join('')}
      </tbody>
    </table>`;
  } catch(e) { el.innerHTML = `<div class="empty" style="color:var(--danger)">${e.message}</div>`; }
}

async function approveTransfer(id) {
  if (!confirm(`Approve transfer request #${id}?\n\nThis will reset the license so the customer can activate on a new device.`)) return;
  try {
    const r = await api('POST', `/admin/transfers/${id}/approve`);
    toast('Transfer approved. Notify the customer they can now activate.');
    loadTransfers(); loadStats();
  } catch(e) { toast(e.message, true); }
}

async function rejectTransfer(id) {
  const reason = prompt('Reason for rejection (shown in audit log):');
  if (reason === null) return;
  try {
    await api('POST', `/admin/transfers/${id}/reject`, { reason });
    toast('Transfer rejected.');
    loadTransfers(); loadStats();
  } catch(e) { toast(e.message, true); }
}

// ── Licenses ───────────────────────────────────────────────────────────────
async function loadLicenses() {
  const el = document.getElementById('licenses-body');
  el.innerHTML = '<div class="empty">Loading...</div>';
  try {
    const data = await api('GET', '/admin/licenses');
    if (!data.licenses.length) {
      el.innerHTML = '<div class="empty">No licenses yet.</div>';
      return;
    }
    const rows = data.licenses.map((l, idx) => {
      const used   = l.activation_count || 0;
      const maxAct = l.max_activations  || 1;
      const seatsBadge = used >= maxAct
        ? `<span class="badge badge-red">${used}/${maxAct}</span>`
        : used > 0
          ? `<span class="badge badge-green">${used}/${maxAct}</span>`
          : `<span class="badge badge-gray">0/${maxAct}</span>`;
      return `
        <tr id="lic-row-${idx}">
          <td class="mono" title="${l.key_hash}">${l.key_hash.slice(0,14)}…</td>
          <td>${l.email || '<span class="muted">—</span>'}</td>
          <td>${l.is_used
            ? '<span class="badge badge-green">Activated</span>'
            : '<span class="badge badge-gray">Unused</span>'}</td>
          <td style="text-align:center">${seatsBadge}</td>
          <td>${l.activated_at ? fmtDate(l.activated_at) : '<span class="muted">—</span>'}</td>
          <td style="display:flex;gap:6px;flex-wrap:wrap">
            ${used > 0 ? `<button class="btn btn-ghost btn-sm"
              onclick="toggleDevices('${l.key_hash}', ${idx})">Devices</button>` : ''}
            ${l.email ? `<button class="btn btn-warn btn-sm"
              onclick="resendKey('${l.key_hash}', '${l.email}')">Resend Key</button>` : ''}
            ${l.is_used ? `<button class="btn btn-danger btn-sm"
              onclick="resetLicense('${l.key_hash}')">Reset All</button>` : ''}
          </td>
        </tr>
        <tr id="devices-row-${idx}" class="devices-row" style="display:none">
          <td colspan="6"><div class="devices-inner" id="devices-inner-${idx}">Loading…</div></td>
        </tr>`;
    }).join('');
    el.innerHTML = `<table>
      <thead><tr>
        <th>Key Hash</th><th>Email</th><th>Status</th>
        <th>Seats Used</th><th>First Activated</th><th>Actions</th>
      </tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
  } catch(e) { el.innerHTML = `<div class="empty" style="color:var(--danger)">${e.message}</div>`; }
}

const _deviceOpen = {};
async function toggleDevices(keyHash, idx) {
  const row   = document.getElementById(`devices-row-${idx}`);
  const inner = document.getElementById(`devices-inner-${idx}`);
  if (_deviceOpen[idx]) {
    row.style.display = 'none';
    _deviceOpen[idx] = false;
    return;
  }
  row.style.display = '';
  _deviceOpen[idx] = true;
  inner.textContent = 'Loading…';
  try {
    const data = await api('GET', `/admin/licenses/${keyHash}/activations`);
    if (!data.activations.length) {
      inner.innerHTML = '<span class="muted">No activations recorded.</span>';
      return;
    }
    inner.innerHTML = `<table>
      <thead><tr><th>#</th><th>Device (fingerprint)</th><th>Activated</th><th></th></tr></thead>
      <tbody>${data.activations.map((a, i) => `
        <tr>
          <td class="muted">${i+1}</td>
          <td class="mono">${a.device_fingerprint.slice(0,16)}…</td>
          <td>${fmtDate(a.activated_at)}</td>
          <td><button class="btn btn-danger btn-sm"
            onclick="deactivateDevice('${keyHash}', ${a.id}, ${idx})">Deactivate</button></td>
        </tr>`).join('')}
      </tbody>
    </table>`;
  } catch(e) { inner.innerHTML = `<span style="color:var(--danger)">${e.message}</span>`; }
}

async function deactivateDevice(keyHash, activationId, idx) {
  if (!confirm('Deactivate this device?\n\nThis frees one seat so another computer can activate.')) return;
  try {
    await api('POST', `/admin/licenses/${keyHash}/activations/${activationId}/deactivate`);
    toast('Device deactivated. Seat is now free.');
    _deviceOpen[idx] = false;
    loadLicenses(); loadStats();
  } catch(e) { toast(e.message, true); }
}

async function resetLicense(keyHash) {
  if (!confirm('Reset this license?\n\nThis clears the device binding so the key can be activated again. Use this for testing or when a transfer is needed urgently.')) return;
  try {
    await api('POST', `/admin/licenses/${keyHash}/reset`);
    toast('License reset. The key can now be activated on a new device.');
    loadLicenses(); loadStats();
  } catch(e) { toast(e.message, true); }
}

async function resendKey(keyHash, email) {
  if (!confirm(`Generate a new replacement key for ${email} and send it by email?`)) return;
  try {
    const r = await api('POST', `/admin/licenses/${keyHash}/resend-key`);
    toast(r.email_sent
      ? `New key emailed to ${r.email}.`
      : `Key generated but email failed — check server logs.`,
      !r.email_sent);
    loadLicenses();
  } catch(e) { toast(e.message, true); }
}

async function setLimit(keyHash, current) {
  const val = prompt(`Set max transfers for this license:\n(current: ${current})`, current);
  if (val === null) return;
  const n = parseInt(val);
  if (isNaN(n) || n < 0) return toast('Enter a valid number >= 0.', true);
  try {
    await api('POST', `/admin/licenses/${keyHash}/set-transfer-limit`, { max_transfers: n });
    toast(`Transfer limit set to ${n}.`);
    loadLicenses();
  } catch(e) { toast(e.message, true); }
}

// ── Generate keys ──────────────────────────────────────────────────────────
async function generateKeys() {
  const email           = document.getElementById('gen-email').value.trim();
  const count           = parseInt(document.getElementById('gen-count').value)  || 1;
  const max_activations = parseInt(document.getElementById('gen-seats').value)  || 1;
  try {
    const data = await api('POST', '/admin/generate-keys', { count, email, max_activations });
    const seatsNote = max_activations > 1 ? ` (${max_activations} seats each)` : '';
    document.getElementById('gen-result').innerHTML = `
      <p style="margin-top:14px;color:var(--accent2);font-weight:600">
        ${data.count} key(s) generated${seatsNote}. Copy them now — they will not be shown again.
      </p>
      <div class="key-list">${data.keys.join('<br>')}</div>
      <button class="btn btn-ghost btn-sm mt" onclick="copyKeys(${JSON.stringify(data.keys)})">
        Copy All
      </button>`;
    loadStats();
  } catch(e) { toast(e.message, true); }
}

function copyKeys(keys) {
  navigator.clipboard.writeText(keys.join('\n'));
  toast('Keys copied to clipboard.');
}

// ── Audit log ──────────────────────────────────────────────────────────────
async function loadAudit() {
  const limit = document.getElementById('audit-limit').value;
  const el = document.getElementById('audit-body');
  el.innerHTML = '<div class="empty">Loading...</div>';
  try {
    const data = await api('GET', `/admin/audit-log?limit=${limit}`);
    if (!data.entries.length) {
      el.innerHTML = '<div class="empty">No audit log entries.</div>';
      return;
    }
    el.innerHTML = `<table>
      <thead><tr>
        <th>Time</th><th>Event</th><th>Email</th><th>Key Hash</th>
        <th>IP</th><th>Details</th>
      </tr></thead>
      <tbody>${data.entries.map(e => `
        <tr>
          <td class="mono" style="white-space:nowrap">${fmtDate(e.created_at)}</td>
          <td>${eventBadge(e.event)}</td>
          <td>${e.email || '<span class="muted">—</span>'}</td>
          <td class="mono" title="${e.key_hash||''}">${e.key_hash ? e.key_hash.slice(0,10)+'…' : '—'}</td>
          <td class="mono">${e.ip_address || '—'}</td>
          <td title="${e.details||''}" style="color:var(--muted)">${(e.details||'').slice(0,60)}</td>
        </tr>`).join('')}
      </tbody>
    </table>`;
  } catch(e) { el.innerHTML = `<div class="empty" style="color:var(--danger)">${e.message}</div>`; }
}

// ── Settings ───────────────────────────────────────────────────────────────
async function loadSettings() {
  try {
    const data = await api('GET', '/admin/settings');
    document.getElementById('price-input').value = (data.price_cents / 100).toFixed(2);
    document.getElementById('price-status').textContent = '';
  } catch(e) { toast(e.message, true); }
}

async function savePrice() {
  const raw = parseFloat(document.getElementById('price-input').value);
  if (isNaN(raw) || raw < 1) {
    document.getElementById('price-status').style.color = 'var(--danger)';
    document.getElementById('price-status').textContent = 'Price must be at least $1.00.';
    return;
  }
  const cents = Math.round(raw * 100);
  try {
    await api('POST', '/admin/settings', { price_cents: cents });
    document.getElementById('price-status').style.color = 'var(--accent2)';
    document.getElementById('price-status').textContent =
      `Price updated to $${(cents/100).toFixed(2)}. New purchases will use this price immediately.`;
    toast(`Price set to $${(cents/100).toFixed(2)}.`);
  } catch(e) {
    document.getElementById('price-status').style.color = 'var(--danger)';
    document.getElementById('price-status').textContent = e.message;
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────
function fmtDate(s) {
  if (!s) return '—';
  try { return new Date(s).toLocaleString(); } catch { return s; }
}

function statusBadge(s) {
  const map = { pending:'yellow', approved:'green', rejected:'red' };
  return `<span class="badge badge-${map[s]||'gray'}">${s}</span>`;
}

function eventBadge(e) {
  if (e.includes('OK') || e.includes('APPROVED')) return `<span class="badge badge-green">${e}</span>`;
  if (e.includes('BLOCKED') || e.includes('REJECT') || e.includes('MISMATCH'))
    return `<span class="badge badge-red">${e}</span>`;
  if (e.includes('PENDING') || e.includes('REQUESTED'))
    return `<span class="badge badge-yellow">${e}</span>`;
  return `<span class="badge badge-blue">${e}</span>`;
}
</script>
</body>
</html>
"""
