from __future__ import annotations

import json
import argparse
from importlib.metadata import version
from pathlib import Path

from good_neighbor import load_demo_scenario, run_strands_incident


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    scenario = load_demo_scenario(ROOT / "evals" / "scenarios" / "demo_scenario.json")
    result = run_strands_incident(scenario)
    context = result.context
    active_plan = context.ledger.active_plan
    if active_plan is None:
        raise RuntimeError("Strands graph did not commit a final plan")

    report = {
        "scenario_id": scenario.scenario_id,
        "framework": "strands-agents",
        "framework_version": version("strands-agents"),
        "model": "frozen-tool-model",
        "model_purpose": "offline deterministic SDK integration fixture",
        "incident_graph": {
            "status": result.incident_status,
            "execution_order": result.incident_execution_order,
            "terminal_task_state": "pending_decision",
        },
        "resume_graph": {
            "status": result.resume_status,
            "execution_order": result.resume_execution_order,
            "terminal_task_state": context.task.status,
        },
        "ledger": {
            "state_version": context.ledger.state_version,
            "allocated_quantity": active_plan.allocated_quantity,
            "policy_violations": 0,
        },
        "safety_boundary": {
            "agent_can_write_allocations_directly": False,
            "budget_requires_persisted_decision": True,
            "approval_resumes_in_new_graph_invocation": True,
        },
        "tool_trace": context.trace,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
