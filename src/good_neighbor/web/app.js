const state = { snapshot: null, view: "operations", busy: false };
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

function key(prefix) {
  return `${prefix}:${crypto.randomUUID()}`;
}

function toast(message) {
  const node = $("#toast");
  node.textContent = message;
  node.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => node.classList.remove("show"), 2600);
}

async function api(path, payload) {
  state.busy = true;
  render();
  try {
    const response = await fetch(path, {
      method: payload ? "POST" : "GET",
      headers: payload ? { "Content-Type": "application/json" } : {},
      body: payload ? JSON.stringify(payload) : undefined,
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || "Request failed");
    state.snapshot = body;
  } catch (error) {
    toast(error.message);
  } finally {
    state.busy = false;
    render();
  }
}

function setView(view) {
  state.view = view;
  $$(".view").forEach((node) => node.classList.toggle("active", node.id === `${view}-view`));
  $$(".nav-item").forEach((node) => node.classList.toggle("active", node.dataset.view === view));
  $("#page-title").textContent = {
    operations: "Recovery operations",
    activity: "Agent activity",
    decisions: "Human decisions",
  }[view];
}

function allocations(report) {
  const items = report?.active_plan?.allocations || [];
  const labels = { "org-a": "Harbor Shelter", "org-b": "Westside Pantry", "org-c": "Family Table", "org-d": "Night Kitchen" };
  if (!items.length) return `<div class="empty-state">Run the incident to see the safe allocation move through the network.</div>`;
  return items.map((item) => `
    <div class="allocation-row">
      <div class="org-label"><strong>${labels[item.organization_id] || item.organization_id}</strong><small>${item.organization_id.toUpperCase()}</small></div>
      <div class="bar"><i style="width:${Math.min(100, item.quantity / 35 * 100)}%"></i></div>
      <b>${item.quantity} meals</b>
    </div>`).join("");
}

function traceRows(report) {
  const items = report?.tool_trace || [];
  if (!items.length) return `<div class="empty-state">No activity yet. Run the incident from Operations.</div>`;
  return items.map((item, index) => {
    const result = item.result || {};
    const summary = Object.entries(result).slice(0, 3).map(([k, v]) => `${k}=${typeof v === "object" ? "…" : v}`).join(" · ");
    return `<div class="trace-row"><span class="trace-index">${String(index + 1).padStart(2, "0")}</span><span class="trace-tool">${item.tool}</span><span class="trace-summary">${summary || "bounded tool result recorded"}</span><span class="trace-ok">verified</span></div>`;
  }).join("");
}

function renderDecision(snapshot) {
  const report = snapshot?.report;
  const pending = snapshot?.stage === "awaiting_decision";
  const complete = snapshot?.stage === "completed";
  const card = $("#decision-card");
  card.classList.toggle("pending", pending);
  $("#approve-button").disabled = !pending || state.busy;
  if (pending) {
    card.querySelector(".eyebrow").textContent = "DECISION REQUIRED · BUDGET";
    card.querySelector("h3").textContent = "Approve USD 32 to preserve all 80 meals?";
    card.querySelector(".decision-copy > p:last-child").textContent = "USD 12 above the autonomous limit. The proposed route is policy-safe but cannot execute without a human.";
  } else if (complete) {
    card.querySelector(".eyebrow").textContent = "DECISION RECORDED · APPROVED";
    card.querySelector("h3").textContent = "Recovery committed with zero unresolved meals.";
    card.querySelector(".decision-copy > p:last-child").textContent = `Decision ${report.human_decision.decision_id} resumed in a new graph invocation.`;
  } else {
    card.querySelector(".eyebrow").textContent = "NO PENDING DECISION";
    card.querySelector("h3").textContent = "Run the incident to trigger the budget boundary.";
    card.querySelector(".decision-copy > p:last-child").textContent = "The Recovery Agent will propose a safe route patch without executing it.";
  }
}

function render() {
  const snapshot = state.snapshot || { stage: "ready", report: null };
  const report = snapshot.report;
  const pending = snapshot.stage === "awaiting_decision";
  const complete = snapshot.stage === "completed";
  const stageLabel = { ready: "Ready", awaiting_decision: "Human decision", completed: "Recovered" }[snapshot.stage] || snapshot.stage;
  $("#stage-pill").textContent = stageLabel;
  $("#stage-pill").style.background = pending ? "var(--orange-soft)" : "var(--green-soft)";
  $("#stage-pill").style.color = pending ? "var(--orange)" : "var(--green)";
  $("#start-button").disabled = pending || state.busy;
  $("#start-button").textContent = complete ? "Replay capacity-drop incident →" : state.busy ? "Running bounded agents…" : "Run capacity-drop incident →";
  $("#decision-count").textContent = pending ? "1" : "0";
  $("#decisions-metric").textContent = pending || complete ? "1" : "0";
  const active = report?.active_plan?.allocated_quantity || 0;
  $("#meals-metric").textContent = `${complete ? active : 0} / 80`;
  $("#meals-caption").textContent = pending ? "Safe patch awaits approval" : complete ? "Recovery committed" : "Ready to coordinate";
  $("#preserved-metric").textContent = report ? `${report.recovery_proposal.preserved_quantity} / 80` : "—";
  $("#violations-metric").textContent = report?.safety_boundary?.policy_violations ?? 0;
  $("#orbit-number").textContent = complete ? active : pending ? report.recovery_proposal.allocated_quantity : 80;
  $("#allocation-list").innerHTML = allocations(report);
  $("#allocation-status").textContent = pending ? "Patch proposed" : complete ? "Committed" : "Awaiting run";
  $("#trace-list").innerHTML = traceRows(report);
  renderDecision(snapshot);
  setView(state.view);
}

$$('.nav-item').forEach((node) => node.addEventListener('click', () => setView(node.dataset.view)));
$("#start-button").addEventListener("click", () => api("/api/actions/start", { idempotency_key: key("start") }));
$("#approve-button").addEventListener("click", () => {
  const decisionId = state.snapshot?.report?.human_decision?.decision_id;
  api("/api/actions/approve", { idempotency_key: key("approve"), decision_id: decisionId });
});
$("#reset-button").addEventListener("click", () => api("/api/actions/reset", { idempotency_key: key("reset") }));

api("/api/state");
