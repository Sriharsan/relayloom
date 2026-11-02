"use strict";
// Relayloom accounts payable UI. Shows server state only; nothing on screen is synthetic.

const $ = (id) => document.getElementById(id);
const STEPS = ["read", "count", "match", "investigate", "enter", "check"];
const STEP_LABEL = { waiting: "Waiting", running: "Working", done: "Done", held: "Held", failed: "Failed", skipped: "Skipped" };
const STATE_PILL = {
  queued: ["Queued", "p-muted"], matched: ["Matched", "p-muted"], entered_checked: ["Entered and checked", "p-ok"],
  held_for_owner: ["Needs you", "p-needs"], held_offline: ["Held, offline", "p-off"], approved: ["Approved", "p-muted"],
  dispute_sent: ["Dispute sent", "p-ok"], closed_by_owner: ["Closed by owner", "p-muted"],
  readback_failed: ["Readback failed", "p-bad"], failed: ["Stopped", "p-bad"],
};
const ACTION_LABEL = { send_dispute: "send a dispute to the supplier", enter_bill: "enter the bill", reject_duplicate: "reject the duplicate bill",
  hold_for_recount: "hold for a person to recount", enter_bill_for_received_quantity: "enter the bill for the received quantity" };
let state = null;
let selected = 0;
let current = "today";
let caseId = null;
let receiptsFor = null;
let openCite = null;
let benchmark = undefined;

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
const rupees = (n) => n == null ? "" : "Rs " + Number(n).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const secs = (s) => s == null ? "" : s < 1 ? `${Math.round(s * 1000)} ms` : s < 120 ? `${Number(s).toFixed(1)} s` : `${(s / 60).toFixed(1)} min`;
const pill = (stateName) => { const [label, cls] = STATE_PILL[stateName] || [stateName, "p-muted"]; return `<span class="pill ${cls}">${esc(label)}</span>`; };
const allPhotos = (c) => (c.counter.events || []).flatMap((e) => e.photos);
const firstPhoto = (c) => { const p = allPhotos(c).find((x) => x.counted); return p ? (p.overlay || p.photo + ".jpg") : ""; };

async function post(path, body) {
  const response = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json", "X-Relayloom": "1" }, body: JSON.stringify(body || {}) });
  if (!response.ok) { const err = await response.json().catch(() => ({})); throw new Error(err.error || response.status); }
  return response.json();
}

async function refresh() {
  try {
    state = await (await fetch("/api/state")).json();
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
  $("start").disabled = cases.length >= state.total_cases;
  $("tiles").innerHTML = [
    ["Entered and checked", counts.entered_checked, "ok"], ["Held for the owner", counts.held_for_owner, "needs"],
    ["Held, offline", counts.held_offline, "off"], ["Disputes sent", counts.disputes_sent, ""],
  ].map(([label, value, cls]) => `<div class="tile ${cls}"><b>${value}</b><span>${label}</span></div>`).join("");
  renderRows(cases);
  renderAutonomy();
  if (current === "case") renderCase();
  if (current === "approvals") renderQueue();
  if (current === "boundary") renderBoundary();
  if (current === "benchmark") renderBenchmark();
}

function stepCell(step) {
  return `<span class="step s-${step.state}"><i>${STEP_LABEL[step.state] || step.state}</i><small>${esc(secs(step.seconds))}</small></span>`;
}

function renderRows(cases) {
  if (!cases.length) return;
  $("rows").innerHTML = cases.map((c) => `<tr data-case="${esc(c.id)}">
    <td><a href="#case/${esc(c.id)}">${esc(c.bill_no)}</a><br><small class="meta">${esc(c.id)}</small></td>
    <td>${esc(c.supplier_id)}</td>
    ${STEPS.map((s) => `<td data-label="${s}">${stepCell(c.steps[s])}</td>`).join("")}
    <td class="status">${pill(c.state)}<br><small class="meta">${esc(c.status)}</small></td></tr>`).join("");
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
    <td class="num">${r.billed_before}</td><td class="num">${r.received ?? "not counted"}</td><td class="num">${rupees(r.po_rate)}</td><td class="num">${rupees(r.bill_rate)}</td>
    <td>${r.issues.length ? `<span class="issue">${esc(r.issues.join("; "))}</span>` : "matches"}</td></tr>`).join("");
  return `<div class="table-wrap"><table><thead><tr><th>Item</th><th>Ordered</th><th>Billed</th><th>Billed before</th><th>Received</th><th>Order rate</th><th>Bill rate</th><th>Result</th></tr></thead><tbody>${rows}</tbody></table></div>
    ${m.problems.length ? `<p class="issue">${esc(m.problems.join(". "))}</p>` : "<p class='meta'>Order, bill and goods received agree within the policy tolerances.</p>"}`;
}

function gallery(c) {
  const events = c.counter.events || [];
  if (!events.length) return "<p class='meta'>Not counted yet.</p>";
  return events.map((e) => `<div class="event"><h3>${esc(e.event_id)} · ${esc(e.date)} · <b class="num">${e.total}</b> counted in ${e.unique_photos} unique photo${e.unique_photos === 1 ? "" : "s"}${e.duplicate_photos ? `, ${e.duplicate_photos} repeated photo ignored` : ""}</h3>
    <div class="shots">${e.photos.map((p) => `<figure class="${p.counted ? "" : "dup"}"><img src="/media/${esc(p.counted ? (p.overlay || p.photo + ".jpg") : p.photo + ".jpg")}" alt="${esc(p.photo)}${p.counted ? `, ${p.count} counted and numbered` : ", repeated photo, not counted"}" loading="lazy">
      <figcaption>${esc(p.photo)}: ${p.counted ? `<b class="num">${p.count}</b> counted` : `repeats ${esc(p.duplicate_of)}, not counted`}</figcaption></figure>`).join("")}</div></div>`).join("");
}

function citeChip(id) { return `<button type="button" class="cite" data-cite="${esc(id)}" aria-pressed="${openCite === id}">${esc(id)}</button>`; }

function investigation(c) {
  const inv = c.investigation;
  if (!inv) return `<div class="card"><h2>Investigation</h2><p class="meta">${c.match && c.match.matched ? "Nothing to investigate: the goods and the paperwork agree." : "Not started."}</p></div>`;
  const f = inv.finding;
  const by = f.written_by === "model" ? `Written by ${esc(f.model.split("/").pop())}, ${esc(f.route)}, ${secs(f.seconds)}.` : "Written by code from the evidence. Every citation was checked by code.";
  let detail = "";
  if (openCite && inv.evidence[openCite]) {
    const item = inv.evidence[openCite];
    const img = item.kind === "photo" ? `<img src="/media/${esc(item.overlay || item.photo + ".jpg")}" alt="${esc(item.photo)}" class="evimg">` : "";
    detail = `<div class="evidence" role="region" aria-live="polite"><b>${esc(item.id)}</b><p>${esc(item.text)}</p>${img}</div>`;
  }
  const level = c.proposal ? c.proposal.policy_level.replaceAll("_", " ") : "";
  return `<div class="card inv"><h2>Investigation</h2>
    <p class="meta">${by} ${f.verified ? "All citations are real records." : "Citations failed the check."}</p>
    <ol class="finding">${f.statements.map((s) => `<li>${esc(s.text)} <span class="cites">${s.cites.map(citeChip).join(" ")}</span></li>`).join("")}</ol>${detail}
    ${c.proposal ? `<div class="proposal"><div><span class="meta">The agent proposes</span><br><b>${esc(ACTION_LABEL[c.proposal.action] || c.proposal.action)}</b><br><span class="issue">${esc(c.proposal.reason)}</span></div>
      <div><span class="meta">The policy says</span><br><span class="pill ${c.proposal.policy_level === "run_alone" ? "p-ok" : "p-needs"}">${esc(level)}</span>${c.decision ? `<br><span class="meta">Owner: ${esc(c.decision.decision)} at ${esc(c.decision.at)}</span>` : ""}</div></div>` : ""}</div>`;
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
  const key = c.id + JSON.stringify([c.state, c.status, openCite, c.counter.total, !!c.investigation, !!c.dispute && c.dispute.sent, c.masked_text.length]);
  if ($("caseBody").dataset.key === key) return;  // nothing changed: keep scroll and the open citation as they are
  $("caseBody").dataset.key = key;
  const reader = c.reader.model ? `${esc(c.reader.model)} · ${esc(c.reader.route)} · ${secs(c.reader.seconds)}` : "not read yet";
  const counter = c.counter.model ? `${esc(c.counter.model)} · ${esc(c.counter.route)} · ${secs(c.counter.seconds)}` : "not counted yet";
  const readback = c.readback ? `<dl class="kv"><dt>Ledger</dt><dd>${esc(c.readback.ledger)} · ${esc(c.invoice_id)}</dd>
      <dt>Fields</dt><dd>${c.readback.differences.length ? `<span class="issue">${esc(c.readback.differences.join("; "))}</span>` : "every field matches the bill"}</dd>
      ${c.pay_to ? `<dt>Pay to</dt><dd>account ending ${esc(c.pay_to.account_last4)}, ${esc(c.pay_to.ifsc)}, from the ${esc(c.pay_to.source)}</dd>` : ""}</dl>`
    : "<p class='meta'>Nothing entered, so nothing to read back.</p>";
  const injection = c.injection ? `<div class="card warn"><h2>Hidden instruction found and ignored</h2><p>${c.injection.hidden_text ? "White text the owner cannot see on the printed bill" : "Instruction text in the bill"}:</p>
      <p class="billtext">${maskedText(c.injection.lines.join("\n"))}</p><p class="meta">${esc(c.injection.action)}. Recorded in the receipts.</p></div>` : "";
  const dispute = c.dispute ? `<div class="card"><h2>Dispute to the supplier</h2><p class="draft">${esc(c.dispute.text)}</p>
      <p class="meta">Text by ${esc(c.dispute.model)} (${esc(c.dispute.route)}, ${secs(c.dispute.seconds)}). ${c.dispute.sent ? `Sent through the supplier portal, form filled by ${esc(c.dispute.form_filled_by)}, reference ${esc(c.dispute.portal_ref)}.` : "Not sent. Sending needs the owner's approval."}</p>
      ${c.dispute.screenshot ? `<img src="/media/${esc(c.dispute.screenshot)}" alt="The supplier portal form filled with the dispute" style="max-width:100%;border-radius:8px">` : ""}</div>` : "";
  $("caseBody").innerHTML = `${injection}${investigation(c)}
    <div class="grid2"><div class="card"><h2>The bill, as the model saw it</h2><pre class="billtext">${maskedText(c.masked_text || "Not read yet.")}</pre>
      <p class="meta">Reader: ${reader}. ${c.masks.length} private numbers masked.</p></div>
    <div class="card photo"><h2>The dock</h2>${gallery(c)}<p class="meta">Counter: ${counter}.</p></div></div>
    <div class="card"><h2>Three way match, as a running total on the order</h2>${matchTable(c.match)}</div>
    <div class="card"><h2>Ledger readback</h2>${readback}</div>
    ${dispute}<div class="card"><h2>Receipts</h2><div id="receiptBox"><p class="meta">Loading receipts.</p></div></div>`;
  loadReceipts(c.id);
}

function renderQueue() {
  const items = state.cases.filter((c) => c.state === "held_for_owner");
  if (!items.length) { $("queue").innerHTML = "<p class='meta'>Nothing needs you right now.</p>"; return; }
  selected = Math.min(selected, items.length - 1);
  $("queue").innerHTML = items.map((c, i) => `<article class="qitem ${i === selected ? "sel" : ""}" data-case="${esc(c.id)}" aria-label="${esc(c.bill_no)}">
    <img src="/media/${esc(firstPhoto(c))}" alt="Delivery photo, counted">
    <div><h2>${esc(c.bill_no)} · ${esc(c.supplier_id)} · ${rupees(c.bill && c.bill.total_inr)}</h2>
      <p class="issue">${esc(c.proposal.reason)}</p>
      ${c.investigation ? `<p class="meta">${c.investigation.finding.statements.length} statements, each citing a record or photo. <a href="#case/${esc(c.id)}">Open the investigation</a></p>` : ""}
      <p>Agent proposes: <b>${esc(ACTION_LABEL[c.proposal.action] || c.proposal.action)}</b>. Nothing has been entered.</p>
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

async function renderBenchmark() {
  if (benchmark === undefined) {
    benchmark = null;
    try { const r = await fetch("/api/benchmark"); benchmark = r.ok ? await r.json() : null; } catch (error) { benchmark = null; }
  }
  const box = $("benchmarkBody");
  if (!benchmark) { box.innerHTML = "<p class='meta'>No benchmark results yet. Run <code>python -m relayloom.ap.benchmark</code>.</p>"; return; }
  const a = benchmark.pipeline_a, b = benchmark.pipeline_b;
  const row = (label, x, y) => `<tr><th scope="row">${label}</th><td class="num">${x}</td><td class="num">${y}</td></tr>`;
  box.innerHTML = `<p class="caveat"><b>Synthetic set built by us.</b> ${a.deliveries} synthetic deliveries with known answers, run through two pipelines on ${esc(benchmark.date)}. ${esc(benchmark.counter_mode)}.</p>
    <div class="table-wrap"><table><thead><tr><th></th><th>A: paperwork only</th><th>B: paperwork plus goods</th></tr></thead><tbody>
      ${row("Bad bills in the set", a.should_hold, b.should_hold)}${row("Errors caught", a.errors_caught, b.errors_caught)}${row("Errors missed", a.errors_missed, b.errors_missed)}
      ${row("Wrong payments avoided", rupees(a.wrong_payments_avoided_inr), rupees(b.wrong_payments_avoided_inr))}${row("Wrong payments made", rupees(a.wrong_payments_made_inr), rupees(b.wrong_payments_made_inr))}
      ${row("False holds", a.false_holds, b.false_holds)}${row("Good bills entered", `${a.correctly_entered} of ${a.should_enter}`, `${b.correctly_entered} of ${b.should_enter}`)}
      ${row("Mean time per delivery, this run", secs(a.mean_seconds_per_case), secs(b.mean_seconds_per_case))}
    </tbody></table></div>
    <p class="meta">SAM 3.1 counted ${benchmark.sam.exactly_right} of ${benchmark.sam.photos} unique photos exactly right. Recorded inference time behind B: ${secs(benchmark.sam_seconds_total)} over the set, about ${secs(benchmark.sam_seconds_per_delivery)} per delivery.</p>
    <h2>By category</h2><div class="table-wrap"><table><thead><tr><th>Category</th><th>Deliveries</th><th>Should enter</th><th>A entered</th><th>B entered</th></tr></thead><tbody>
      ${Object.entries(benchmark.by_category).map(([k, v]) => `<tr><td>${esc(k.replaceAll("_", " "))}</td><td class="num">${v.deliveries}</td><td>${v.should_enter ? "yes" : "no"}</td><td class="num">${v.a_entered}</td><td class="num">${v.b_entered}</td></tr>`).join("")}</tbody></table></div>
    <h2>Every delivery</h2><div class="table-wrap"><table><thead><tr><th>Id</th><th>Category</th><th>Total</th><th>Should enter</th><th>A</th><th>B</th><th>B counted</th></tr></thead><tbody>
      ${benchmark.rows_a.map((ra, i) => { const rb = benchmark.rows_b[i]; return `<tr><td>${esc(ra.id)}</td><td>${esc(ra.category.replaceAll("_", " "))}</td><td class="num">${rupees(ra.total_inr)}</td><td>${ra.should_enter ? "yes" : "no"}</td><td>${ra.entered ? "entered" : "held"}</td><td>${rb.entered ? "entered" : "held"}</td><td class="num">${rb.counted ?? ""}</td></tr>`; }).join("")}</tbody></table></div>`;
}

async function decide(id, decision) {
  try { await post("/api/decide", { case: id, decision }); } catch (error) { alert(error.message); }
  setTimeout(refresh, 300);
}

function route() {
  const hash = location.hash.slice(1) || "today";
  const [screen, id] = hash.split("/");
  current = ["today", "case", "approvals", "boundary", "benchmark"].includes(screen) ? screen : "today";
  caseId = id || null;
  openCite = null;
  if ($("caseBody")) $("caseBody").dataset.key = "";
  document.querySelectorAll(".screen").forEach((s) => { s.hidden = s.id !== current; });
  document.querySelectorAll("nav a").forEach((a) => { if (a.dataset.tab === current) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
  if (state) render();
}

document.addEventListener("click", (event) => {
  const cite = event.target.closest("[data-cite]");
  if (cite) { openCite = openCite === cite.dataset.cite ? null : cite.dataset.cite; renderCase(); return; }
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
