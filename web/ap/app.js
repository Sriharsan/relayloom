"use strict";
// Relayloom accounts payable UI. Shows server state only; nothing on screen is invented.

const $ = (id) => document.getElementById(id);
const STEP_LABEL = { waiting: "Waiting", running: "Working", done: "Done", held: "Held", failed: "Failed", skipped: "Skipped" };
const STATE_PILL = {
  queued: ["Queued", "p-muted"], matched: ["Matched", "p-muted"], entered_checked: ["Entered and checked", "p-ok"],
  held_for_owner: ["Needs you", "p-needs"], held_offline: ["Held, offline", "p-off"], approved: ["Approved", "p-muted"],
  dispute_sent: ["Dispute sent", "p-ok"], closed_by_owner: ["Rejected by owner", "p-muted"],
  readback_failed: ["Readback failed", "p-bad"], failed: ["Stopped", "p-bad"],
};
let state = null;
let selected = 0;
let current = "today";
let caseId = null;
let receiptsFor = null;

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
const rupees = (n) => n == null ? "" : "Rs " + Number(n).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const secs = (s) => s == null ? "" : s < 1 ? `${Math.round(s * 1000)} ms` : s < 120 ? `${Number(s).toFixed(1)} s` : `${(s / 60).toFixed(1)} min`;
const pill = (stateName) => { const [label, cls] = STATE_PILL[stateName] || [stateName, "p-muted"]; return `<span class="pill ${cls}">${esc(label)}</span>`; };

async function post(path, body) {
  const response = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json", "X-Relayloom": "1" }, body: JSON.stringify(body || {}) });
  if (!response.ok) { const err = await response.json().catch(() => ({})); throw new Error(err.error || response.status); }
  return response.json();
}

async function refresh() {
  try {
    const response = await fetch("/api/state");
    state = await response.json();
    render();
  } catch (error) {
    $("runbar").textContent = "The local app is not answering. Is python -m relayloom.ap running?";
  }
}

function render() {
  const { run, counts, cases, online } = state;
  $("runbar").innerHTML = `Mode <b>${esc(run.mode)}</b> · Reader <b>${esc(run.reader)}</b> · Counter <b>${esc(run.counter)}</b> · Ledger <b>${esc(run.ledger)}</b> · Policy <b>${esc(run.policy_hash.slice(0, 12))}</b>`;
  $("net").textContent = online ? "Network on" : "Network cut";
  $("net").className = "net " + (online ? "on" : "off");
  $("netToggle").textContent = online ? "Cut network" : "Reconnect";
  const waiting = cases.filter((c) => c.state === "held_for_owner").length;
  $("approvalCount").hidden = !waiting;
  $("approvalCount").textContent = waiting;
  $("start").disabled = cases.length >= 7;
  $("tiles").innerHTML = [
    ["Entered and checked", counts.entered_checked, "ok"], ["Held for the owner", counts.held_for_owner, "needs"],
    ["Held, offline", counts.held_offline, "off"], ["Disputes sent", counts.disputes_sent, ""],
  ].map(([label, value, cls]) => `<div class="tile ${cls}"><b>${value}</b><span>${label}</span></div>`).join("");
  renderRows(cases);
  renderAutonomy();
  if (current === "case") renderCase();
  if (current === "approvals") renderQueue();
  if (current === "boundary") renderBoundary();
}

function stepCell(step) {
  return `<span class="step s-${step.state}"><i>${STEP_LABEL[step.state] || step.state}</i><small>${esc(secs(step.seconds))}</small></span>`;
}

function renderRows(cases) {
  if (!cases.length) return;
  $("rows").innerHTML = cases.map((c) => `<tr data-case="${esc(c.id)}">
    <td><a href="#case/${esc(c.id)}">${esc(c.bill_no)}</a><br><small class="meta">${esc(c.id)}</small></td>
    <td>${esc(c.supplier_id)}</td>
    ${["read", "count", "match", "enter", "check"].map((s) => `<td>${stepCell(c.steps[s])}</td>`).join("")}
    <td>${pill(c.state)}<br><small class="meta">${esc(c.status)}</small></td></tr>`).join("");
}

function renderAutonomy() {
  const ops = state.policy.operations;
  const group = (level) => Object.keys(ops).filter((k) => ops[k] === level).map((k) => `<li>${esc(k.replaceAll("_", " "))}</li>`).join("");
  $("autonomy").innerHTML = `
    <div class="lvl alone"><h2>Runs alone</h2><ul>${group("run_alone")}</ul></div>
    <div class="lvl approval"><h2>Waits for the owner</h2><ul>${group("run_with_approval")}</ul><p class="meta">Owner limit ${rupees(state.policy.limits.owner_amount_limit_inr)}</p></div>
    <div class="lvl never"><h2>Never</h2><ul>${group("never")}</ul></div>`;
}

function maskedText(text) {
  return esc(text).replace(/\[([A-Z_]+) MASKED\]/g, '<mark title="masked before any model saw it">[$1 MASKED]</mark>');
}

function matchTable(m) {
  if (!m) return "<p class='meta'>Not matched yet.</p>";
  const rows = m.rows.map((r) => `<tr><td>${esc(r.description)}</td><td class="num">${r.po_qty}</td><td class="num">${r.bill_qty ?? ""}</td>
    <td class="num">${r.counted ?? "not counted"}</td><td class="num">${rupees(r.po_rate)}</td><td class="num">${rupees(r.bill_rate)}</td>
    <td>${r.issues.length ? `<span class="issue">${esc(r.issues.join("; "))}</span>` : "matches"}</td></tr>`).join("");
  return `<div class="table-wrap"><table><thead><tr><th>Item</th><th>PO qty</th><th>Billed</th><th>Counted</th><th>PO rate</th><th>Bill rate</th><th>Result</th></tr></thead><tbody>${rows}</tbody></table></div>
    ${m.problems.length ? `<p class="issue">${esc(m.problems.join(". "))}</p>` : "<p class='meta'>Purchase order, bill and delivery agree within the policy tolerances.</p>"}`;
}

async function loadReceipts(id) {
  receiptsFor = id;
  const data = await (await fetch("/api/receipts?case=" + encodeURIComponent(id))).json();
  const box = $("receiptBox");
  if (!box || receiptsFor !== id) return;
  box.innerHTML = `<p class="meta">${data.verified ? "Every receipt in this run verifies: signatures, hashes and chain order." : "Verification failed: " + esc(data.problems.join("; "))}</p>
    <div class="table-wrap"><table class="receipts"><thead><tr><th>#</th><th>Agent</th><th>Step</th><th>Decision</th><th>Model</th><th>Hash</th></tr></thead><tbody>
    ${data.receipts.map((r) => `<tr><td>${r.body.seq}</td><td>${esc(r.body.agent)}</td><td>${esc(r.body.step)}</td><td>${esc(r.body.decision)}</td><td>${esc(r.body.model)}</td><td>${esc(r.hash.slice(0, 12))}</td></tr>`).join("")}
    </tbody></table></div>`;
}

function renderCase() {
  const c = state.cases.find((x) => x.id === caseId);
  if (!c) { $("caseBody").innerHTML = "<p class='meta'>This case has not started yet.</p>"; return; }
  $("caseTitle").textContent = `${c.bill_no} · ${c.supplier_id}`;
  const photo = c.counter.overlay ? c.counter.overlay : c.photo;
  const reader = c.reader.model ? `${esc(c.reader.model)} · ${esc(c.reader.route)} · ${secs(c.reader.seconds)}` : "not read yet";
  const counter = c.counter.model ? `${esc(c.counter.model)} · ${esc(c.counter.route)} · ${secs(c.counter.seconds)} · prompt "${esc(c.counter.prompt)}"` : "not counted yet";
  const decision = c.proposal ? `<dl class="kv"><dt>Agent proposes</dt><dd>${esc(c.proposal.action.replace("_", " "))}</dd><dt>Why</dt><dd>${esc(c.proposal.reason)}</dd>
      <dt>Policy</dt><dd>${esc(c.proposal.operation.replaceAll("_", " "))}: ${esc(c.proposal.policy_level.replaceAll("_", " "))}</dd>
      ${c.decision ? `<dt>Owner</dt><dd>${esc(c.decision.decision)} by ${esc(c.decision.by)} at ${esc(c.decision.at)}</dd>` : ""}</dl>`
    : `<p class="meta">${c.state === "entered_checked" ? "Matched within limits: the policy lets the agents enter it alone." : "No proposal needed yet."}</p>`;
  const readback = c.readback ? `<dl class="kv"><dt>Ledger</dt><dd>${esc(c.readback.ledger)} · ${esc(c.invoice_id)}</dd>
      <dt>Fields</dt><dd>${c.readback.differences.length ? `<span class="issue">${esc(c.readback.differences.join("; "))}</span>` : "every field matches the bill"}</dd>
      ${c.pay_to ? `<dt>Pay to</dt><dd>account ending ${esc(c.pay_to.account_last4)}, ${esc(c.pay_to.ifsc)}, from the ${esc(c.pay_to.source)}</dd>` : ""}</dl>`
    : "<p class='meta'>Nothing entered, so nothing to read back.</p>";
  const injection = c.injection ? `<div class="card warn"><h2>Hidden instruction found and ignored</h2><p>${c.injection.hidden_text ? "White text the owner cannot see on the printed bill" : "Instruction text in the bill"}:</p>
      <p class="billtext">${maskedText(c.injection.lines.join("\n"))}</p><p class="meta">${esc(c.injection.action)}. Recorded in the receipts.</p></div>` : "";
  const dispute = c.dispute ? `<div class="card"><h2>Dispute to the supplier</h2><p class="draft">${esc(c.dispute.text)}</p>
      <p class="meta">Text by ${esc(c.dispute.model)} (${esc(c.dispute.route)}, ${secs(c.dispute.seconds)}). ${c.dispute.sent ? `Sent through the supplier portal, form filled by ${esc(c.dispute.form_filled_by)}, reference ${esc(c.dispute.portal_ref)}.` : "Not sent. Sending needs the owner's approval."}</p>
      ${c.dispute.screenshot ? `<img src="/media/${esc(c.dispute.screenshot)}" alt="The supplier portal form filled with the dispute" style="max-width:100%;border-radius:8px">` : ""}</div>` : "";
  $("caseBody").innerHTML = `${injection}<div class="grid2">
    <div class="card"><h2>The bill, as the model saw it</h2><pre class="billtext">${maskedText(c.masked_text || "Not read yet.")}</pre>
      <p class="meta">Reader: ${reader}. ${c.masks.length} private numbers masked.</p></div>
    <div class="card photo"><h2>The delivery</h2><img src="/media/${esc(photo)}" alt="Delivery photo${c.counter.count != null ? ` with ${c.counter.count} items outlined and numbered` : ""}">
      <p class="meta">${c.counter.count != null ? `<b>${c.counter.count}</b> counted. ` : ""}Counter: ${counter}.</p></div></div>
    <div class="card"><h2>Three way match</h2>${matchTable(c.match)}</div>
    <div class="grid2"><div class="card"><h2>Proposal and policy</h2>${decision}</div><div class="card"><h2>Ledger readback</h2>${readback}</div></div>
    ${dispute}<div class="card"><h2>Receipts</h2><div id="receiptBox"><p class="meta">Loading receipts.</p></div></div>`;
  loadReceipts(c.id);
}

function renderQueue() {
  const items = state.cases.filter((c) => c.state === "held_for_owner");
  if (!items.length) { $("queue").innerHTML = "<p class='meta'>Nothing needs you right now.</p>"; return; }
  selected = Math.min(selected, items.length - 1);
  $("queue").innerHTML = items.map((c, i) => `<article class="qitem ${i === selected ? "sel" : ""}" data-case="${esc(c.id)}" aria-label="${esc(c.bill_no)}">
    <img src="/media/${esc(c.counter.overlay || c.photo)}" alt="Delivery photo, ${c.counter.count} counted">
    <div><h2>${esc(c.bill_no)} · ${esc(c.supplier_id)} · ${rupees(c.bill && c.bill.total_inr)}</h2>
      <p class="issue">${esc(c.proposal.reason)}</p>
      <p>Agent proposes: <b>${esc(c.proposal.action.replace("_", " "))}</b>. Nothing has been entered.</p>
      ${c.dispute ? `<p class="draft">${esc(c.dispute.text)}</p><p class="meta">Draft by ${esc(c.dispute.model)}, ${esc(c.dispute.route)}</p>` : ""}
      <div class="qactions"><button type="button" class="approve" data-act="approve" data-case="${esc(c.id)}">Approve (a)</button>
      <button type="button" class="reject" data-act="reject" data-case="${esc(c.id)}">Reject (r)</button>
      <a class="link ghost" href="#case/${esc(c.id)}">Open case</a></div></div></article>`).join("");
}

function renderBoundary() {
  const b = state.boundary;
  const log = b.gateway_log.length ? `<div class="table-wrap"><table><thead><tr><th>Time</th><th>Host</th><th>Decision</th><th>Bytes out</th><th>Model</th><th>Masked</th></tr></thead><tbody>
    ${b.gateway_log.slice().reverse().map((g) => `<tr><td class="num">${esc(g.time)}</td><td>${esc(g.host)}</td><td>${esc(g.decision)}</td><td class="num">${esc(g.bytes_out ?? "")}</td><td>${esc(g.model)}</td><td>${esc(g.masks)}</td></tr>`).join("")}
    </tbody></table></div>` : "<p>The gateway log is empty: no request left this machine during this run.</p>";
  const masks = b.masks.map((m) => `<li>${esc(m.case)}: ${esc(m.kinds.join(", "))}</li>`).join("");
  $("boundaryBody").innerHTML = `<div class="grid2"><div class="card"><h2>The boundary</h2>
    <p>Muse Glimmer and SAM 3.1 run on this machine. The ledger and the supplier portal are local too. The only way out is the gateway, which allows only: ${esc(Object.keys(state.policy.egress.allowed_hosts).join(", "))}. Everything else is refused and logged.</p>
    <p class="meta">Requests allowed out this run: <b>${b.model_calls_outside}</b></p></div>
    <div class="card"><h2>Masked before any model saw it</h2><ul>${masks || "<li>No bills read yet.</li>"}</ul></div></div>
    <div class="card"><h2>Gateway log</h2>${log}</div>`;
}

async function decide(id, decision) {
  try { await post("/api/decide", { case: id, decision }); } catch (error) { alert(error.message); }
  setTimeout(refresh, 300);
}

function route() {
  const hash = location.hash.slice(1) || "today";
  const [screen, id] = hash.split("/");
  current = ["today", "case", "approvals", "boundary"].includes(screen) ? screen : "today";
  caseId = id || null;
  document.querySelectorAll(".screen").forEach((s) => { s.hidden = s.id !== current; });
  document.querySelectorAll("nav a").forEach((a) => { if (a.dataset.tab === current) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
  if (state) render();
}

document.addEventListener("click", (event) => {
  const act = event.target.closest("[data-act]");
  if (act) return decide(act.dataset.case, act.dataset.act);
  const row = event.target.closest("tr[data-case]");
  if (row && !event.target.closest("a")) location.hash = "case/" + row.dataset.case;
});
document.addEventListener("keydown", (event) => {
  if (current !== "approvals" || event.target.closest("input, textarea") || event.ctrlKey || event.metaKey || event.altKey) return;
  const items = state ? state.cases.filter((c) => c.state === "held_for_owner") : [];
  if (!items.length) return;
  if (event.key === "j") { selected = Math.min(selected + 1, items.length - 1); renderQueue(); }
  if (event.key === "k") { selected = Math.max(selected - 1, 0); renderQueue(); }
  if (event.key === "a") decide(items[selected].id, "approve");
  if (event.key === "r") decide(items[selected].id, "reject");
});
$("start").addEventListener("click", async () => { $("start").disabled = true; await post("/api/batch", {}); refresh(); });
$("netToggle").addEventListener("click", async () => { await post("/api/network", { online: !state.online }); setTimeout(refresh, 300); });
$("theme").addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  $("theme").textContent = next === "dark" ? "Light" : "Dark";
  try { localStorage.setItem("relayloom-theme", next); } catch (error) { /* storage may be blocked */ }
});
try { const saved = localStorage.getItem("relayloom-theme"); if (saved) { document.documentElement.dataset.theme = saved; $("theme").textContent = saved === "dark" ? "Light" : "Dark"; } } catch (error) { /* ignore */ }
window.addEventListener("hashchange", route);
route();
refresh();
setInterval(refresh, 1000);
