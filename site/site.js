"use strict";
// Fills the page from data/results.json, which scripts/build_site.py makes from our recorded runs.
const $ = (id) => document.getElementById(id);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
let data = null;

async function load() {
  data = await (await fetch("data/results.json")).json();
  $("runline").textContent = data.runline;
  const groups = { run_alone: ["alone", "Runs alone"], run_with_approval: ["approval", "Waits for the owner"], never: ["never", "Never"] };
  $("levels").innerHTML = Object.entries(groups).map(([level, [cls, title]]) => `<div class="card ${cls}"><h3>${title}</h3><ul>${
    Object.entries(data.policy).filter(([, l]) => l === level).map(([op]) => `<li>${esc(op.replaceAll("_", " "))}</li>`).join("")}</ul></div>`).join("");
  $("caseList").innerHTML = data.cases.map((c) => `<article class="card case">
      <div>${c.image ? `<img src="${esc(c.image)}" alt="${esc(c.alt)}" loading="lazy">` : ""}</div>
      <div><h3>${esc(c.title)} <span class="${c.result === "PASS" ? "pass" : "fail"}">${esc(c.result)}</span><span class="tag">${esc(c.label)}</span></h3>
        <p>${esc(c.story)}</p><ul>${c.facts.map((f) => `<li>${esc(f)}</li>`).join("")}</ul>
        <p class="meta"><code>${esc(c.command)}</code></p></div></article>`).join("");
  renderFinding();
  renderBenchmark();
  $("boundaryLine").textContent = data.boundary.line;
  $("gatewayLog").textContent = data.boundary.log.map((e) => JSON.stringify(e)).join("\n") || "No request left the machine.";
  if (data.video) { $("videoLink").href = data.video; $("videoText").innerHTML = `<a href="${esc(data.video)}">Watch the video</a>`; }
}

const rupees = (n) => "Rs " + Number(n).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const secs = (n) => n < 120 ? `${Number(n).toFixed(1)} s` : `${(n / 60).toFixed(1)} min`;

function renderFinding() {
  const f = data.finding;
  if (!f) { $("finding").innerHTML = "<p class='meta'>No investigation recorded yet.</p>"; return; }
  const by = f.written_by === "model" ? `Written by ${esc(f.model)}, ${esc(f.route)}.` : "Written by code from the evidence.";
  $("finding").innerHTML = `<h3>${esc(f.title)}</h3><p class="meta">${by} Every citation below was checked by code against the records of this run.</p>
    <ol class="finding">${f.statements.map((s) => `<li>${esc(s.text)} <span class="cites">${s.cites.map((c) => `<button type="button" class="cite" data-cite="${esc(c)}">${esc(c)}</button>`).join(" ")}</span></li>`).join("")}</ol>
    <div class="evidence" id="evidence" aria-live="polite"><p class="meta">Select a citation to see the record it points to.</p></div>
    <p><b>Proposed:</b> ${esc(f.proposal)} <span class="meta">Policy: ${esc(f.policy)}.</span></p>
    ${f.images.length ? `<div class="shots">${f.images.map((i) => `<figure><img src="${esc(i.src)}" alt="${esc(i.alt)}" loading="lazy"><figcaption>${esc(i.caption)}</figcaption></figure>`).join("")}</div>` : ""}`;
  $("finding").addEventListener("click", (event) => {
    const chip = event.target.closest("[data-cite]");
    if (!chip) return;
    const item = f.evidence[chip.dataset.cite];
    $("evidence").innerHTML = item ? `<b>${esc(chip.dataset.cite)}</b><p>${esc(item)}</p>` : "<p class='fail'>Not a record.</p>";
  });
}

function renderBenchmark() {
  const b = data.benchmark;
  if (!b) { $("benchmarkTable").innerHTML = "<p class='meta'>Benchmark results are not available yet.</p>"; return; }
  const a = b.pipeline_a, p = b.pipeline_b;
  const row = (label, x, y) => `<tr><th scope="row">${label}</th><td class="num">${x}</td><td class="num">${y}</td></tr>`;
  $("benchmarkTable").innerHTML = `<p class="meta">${a.deliveries} deliveries, run ${esc(b.date)}. ${esc(b.counter_mode)}.</p>
    <div class="tablewrap"><table><thead><tr><th></th><th>A: paperwork only</th><th>B: paperwork plus goods</th></tr></thead><tbody>
    ${row("Bad bills in the set", a.should_hold, p.should_hold)}${row("Errors caught", a.errors_caught, p.errors_caught)}${row("Errors missed", a.errors_missed, p.errors_missed)}
    ${row("Wrong payments avoided (synthetic Rs)", rupees(a.wrong_payments_avoided_inr), rupees(p.wrong_payments_avoided_inr))}
    ${row("Wrong payments made (synthetic Rs)", rupees(a.wrong_payments_made_inr), rupees(p.wrong_payments_made_inr))}
    ${row("False holds", a.false_holds, p.false_holds)}${row("Good bills entered", `${a.correctly_entered} of ${a.should_enter}`, `${p.correctly_entered} of ${p.should_enter}`)}
    </tbody></table></div>
    <p class="meta">SAM 3.1 counted ${b.sam.exactly_right} of ${b.sam.photos} unique photos exactly right. Recorded SAM 3.1 inference behind B: ${secs(b.sam_seconds_total)} over the set, about ${secs(b.sam_seconds_per_delivery)} per delivery on a laptop CPU.</p>
    <details><summary>Every delivery</summary><div class="tablewrap"><table><thead><tr><th>Id</th><th>Category</th><th>Should enter</th><th>A</th><th>B</th></tr></thead><tbody>
    ${b.rows_a.map((ra, i) => `<tr><td>${esc(ra.id)}</td><td>${esc(ra.category.replaceAll("_", " "))}</td><td>${ra.should_enter ? "yes" : "no"}</td><td>${ra.entered ? "entered" : "held"}</td><td>${b.rows_b[i].entered ? "entered" : "held"}</td></tr>`).join("")}
    </tbody></table></div></details>`;
}

async function check(tamper) {
  const receipts = JSON.parse(JSON.stringify(data.receipts.receipts));
  if (tamper) receipts[Math.floor(receipts.length / 2)].body.decision = "changed after signing";
  $("verifyOut").textContent = "Checking.";
  try {
    const result = await verifyReceipts(receipts, data.receipts.public_key);
    $("verifyOut").className = "out " + (result.ok ? "pass" : "fail");
    $("verifyOut").textContent = result.ok
      ? `All ${result.count} receipts across ${result.cases} cases verify: signature, hash and chain order.`
      : `Verification failed: ${result.problems.slice(0, 3).join("; ")}`;
  } catch (error) {
    $("verifyOut").textContent = "This browser cannot check Ed25519 signatures. Try a current Chrome, Edge, Firefox or Safari.";
  }
}

$("verifyBtn").addEventListener("click", () => check(false));
$("tamperBtn").addEventListener("click", () => check(true));
$("theme").addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  $("theme").textContent = next === "dark" ? "Light" : "Dark";
});
load();
