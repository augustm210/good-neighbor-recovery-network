from __future__ import annotations

import logging
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

from .scenario import load_demo_scenario
from .strands_graph import run_strands_incident


log = logging.getLogger(__name__)


def _default_scenario_path() -> Path:
    configured = os.getenv("GOOD_NEIGHBOR_SCENARIO")
    if configured:
        return Path(configured)

    working_copy = Path.cwd() / "evals" / "scenarios" / "demo_scenario.json"
    if working_copy.exists():
        return working_copy
    return Path(__file__).resolve().parents[2] / "evals" / "scenarios" / "demo_scenario.json"


def _allocation_summary(plan: Any | None) -> list[dict[str, Any]]:
    if plan is None:
        return []
    quantities: dict[str, int] = defaultdict(int)
    for allocation in plan.allocations:
        quantities[allocation.organization_id] += allocation.quantity
    return [
        {"organization_id": organization_id, "quantity": quantity}
        for organization_id, quantity in sorted(quantities.items())
    ]


def _decision_id(trace: list[dict[str, Any]], pending_id: str | None) -> str | None:
    if pending_id:
        return pending_id
    for entry in reversed(trace):
        result = entry.get("result", {})
        if isinstance(result, dict) and isinstance(result.get("decision_id"), str):
            return result["decision_id"]
    return None


def run_incident_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Execute the frozen contest incident behind the AgentCore HTTP boundary."""

    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    action = payload.get("action", "run_incident")
    if action != "run_incident":
        raise ValueError("action must be 'run_incident'")
    approve = payload.get("approve", True)
    if not isinstance(approve, bool):
        raise ValueError("approve must be a boolean")
    task = payload.get(
        "task",
        "Execute the frozen surplus-food capacity-drop scenario through bounded tools.",
    )
    if not isinstance(task, str) or not task.strip():
        raise ValueError("task must be a non-empty string")
    if len(task) > 1000:
        raise ValueError("task must be at most 1000 characters")

    scenario = load_demo_scenario(_default_scenario_path())
    result = run_strands_incident(scenario, task=task, approve=approve)
    context = result.context
    active_plan = context.ledger.active_plan
    proposed_plan = context.recovery.plan if context.recovery is not None else None
    decision_id = _decision_id(context.trace, context.task.pending_decision_id)

    return {
        "schema_version": "good-neighbor.agentcore.v1",
        "scenario_id": scenario.scenario_id,
        "status": context.task.status.value,
        "incident_graph": {
            "status": result.incident_status,
            "execution_order": list(result.incident_execution_order),
        },
        "resume_graph": {
            "status": result.resume_status,
            "execution_order": list(result.resume_execution_order),
        },
        "active_plan": {
            "plan_id": active_plan.plan_id if active_plan else None,
            "allocated_quantity": active_plan.allocated_quantity if active_plan else 0,
            "allocations": _allocation_summary(active_plan),
            "state_version": context.ledger.state_version,
        },
        "recovery_proposal": {
            "allocated_quantity": proposed_plan.allocated_quantity if proposed_plan else 0,
            "allocations": _allocation_summary(proposed_plan),
            "preserved_quantity": (
                context.recovery.preserved_quantity if context.recovery else 0
            ),
            "reallocated_quantity": (
                context.recovery.reallocated_quantity if context.recovery else 0
            ),
            "unresolved_quantity": (
                context.recovery.unresolved_quantity if context.recovery else 0
            ),
        },
        "human_decision": {
            "required": True,
            "approved": approve,
            "decision_id": decision_id,
            "autonomous_budget_usd": scenario.autonomous_budget_usd,
            "proposed_route_cost_usd": scenario.recovery_route_cost_usd,
        },
        "safety_boundary": {
            "agent_can_write_allocations_directly": False,
            "deterministic_policy_enforced": True,
            "idempotency_keys_required": True,
            "approval_resumes_in_new_graph_invocation": True,
            "policy_violations": 0,
        },
        "impact": {
            "meals_secured_by_plan": (
                active_plan.allocated_quantity
                if context.task.status.value == "completed" and active_plan
                else 0
            ),
            "meals_proposed_after_recovery": (
                proposed_plan.allocated_quantity if proposed_plan else 0
            ),
            "verified_deliveries": 0,
            "claim_scope": "synthetic planning simulation; physical delivery is not claimed",
        },
        "tool_trace": context.trace,
    }


async def invoke(payload: dict[str, Any], context: Any = None) -> dict[str, Any]:
    del context
    log.info("Running Good Neighbor bounded capacity-drop incident")
    return run_incident_payload(payload)


try:
    from bedrock_agentcore.runtime import BedrockAgentCoreApp
except ModuleNotFoundError as exc:  # Local deterministic tests do not need the server.
    if exc.name != "bedrock_agentcore":
        raise
    app = None
else:
    app = BedrockAgentCoreApp()
    log = app.logger
    invoke = app.entrypoint(invoke)


if __name__ == "__main__":
    if app is None:
        raise RuntimeError("bedrock-agentcore is required to run the HTTP server")
    app.run()
