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
  $("boundaryLine").textContent = data.boundary.line;
  $("gatewayLog").textContent = data.boundary.log.map((e) => JSON.stringify(e)).join("\n") || "No request left the machine.";
  if (data.video) { $("videoLink").href = data.video; $("videoText").innerHTML = `<a href="${esc(data.video)}">Watch the video</a>`; }
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
