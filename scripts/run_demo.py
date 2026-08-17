from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from good_neighbor import (  # noqa: E402
    InMemoryReservationLedger,
    TaskState,
    TaskStatus,
    greedy_allocate,
    load_demo_scenario,
    recover_after_capacity_change,
    validate_plan,
)


def allocation_rows(plan):
    return [
        {
            "allocation_id": item.allocation_id,
            "lot_id": item.lot_id,
            "organization_id": item.organization_id,
            "organization_version": item.organization_version,
            "quantity": item.quantity,
        }
        for item in plan.allocations
    ]


def main() -> None:
    scenario = load_demo_scenario(ROOT / "evals" / "scenarios" / "demo_scenario.json")
    ledger = InMemoryReservationLedger(
        scenario.donation,
        list(scenario.organizations),
    )
    task = TaskState(task_id=f"task:{scenario.scenario_id}")
    trace: list[dict[str, object]] = []

    initial_plan = greedy_allocate(
        scenario.donation,
        list(scenario.organizations),
        based_on_state_version=ledger.state_version,
        plan_id="initial-plan",
    )
    initial_policy = validate_plan(
        scenario.donation,
        scenario.organizations,
        initial_plan,
        autonomous_budget_usd=scenario.autonomous_budget_usd,
    )
    if not initial_policy.allowed:
        raise RuntimeError(f"initial plan rejected: {initial_policy.reasons}")
    task = task.transition(TaskStatus.PLANNED)
    initial_commit = ledger.commit_plan(
        initial_plan,
        autonomous_budget_usd=scenario.autonomous_budget_usd,
    )
    if not initial_commit.committed:
        raise RuntimeError(f"initial commit failed: {initial_commit.reasons}")
    task = task.transition(TaskStatus.RESERVED).transition(TaskStatus.IN_PROGRESS)
    trace.append(
        {
            "event": "initial_plan_committed",
            "task_version": task.version,
            "state_version": initial_commit.state_version,
            "quantity": initial_plan.allocated_quantity,
        }
    )

    capacity_result = ledger.apply_capacity_change(scenario.failure_event)
    if not capacity_result.applied:
        raise RuntimeError(f"capacity event failed: {capacity_result.reasons}")
    trace.append(
        {
            "event": "capacity_changed",
            "state_version": capacity_result.state_version,
            "organization_id": scenario.failure_event.organization_id,
            "overcommitted_quantity": capacity_result.overcommitted_quantity,
        }
    )

    recovery = recover_after_capacity_change(
        scenario.donation,
        ledger.organizations,
        initial_plan,
        scenario.failure_event,
        based_on_state_version=ledger.state_version,
        incremental_cost_usd=scenario.recovery_route_cost_usd,
    )
    unapproved_policy = validate_plan(
        scenario.donation,
        ledger.organizations,
        recovery.plan,
        autonomous_budget_usd=scenario.autonomous_budget_usd,
    )
    if unapproved_policy.reasons != ("budget_approval_required",):
        raise RuntimeError(
            f"recovery should require only budget approval: {unapproved_policy.reasons}"
        )
    task = task.transition(
        TaskStatus.PENDING_DECISION,
        pending_decision_id="decision:recovery-budget",
    )
    trace.append(
        {
            "event": "decision_required",
            "task_version": task.version,
            "reason": "budget_approval_required",
            "autonomous_budget_usd": scenario.autonomous_budget_usd,
            "proposed_cost_usd": recovery.plan.estimated_cost_usd,
        }
    )

    task = task.transition(TaskStatus.PLANNED)
    approved_policy = validate_plan(
        scenario.donation,
        ledger.organizations,
        recovery.plan,
        autonomous_budget_usd=scenario.autonomous_budget_usd,
        budget_approved=True,
    )
    if not approved_policy.allowed:
        raise RuntimeError(f"approved recovery rejected: {approved_policy.reasons}")
    recovery_commit = ledger.commit_plan(
        recovery.plan,
        autonomous_budget_usd=scenario.autonomous_budget_usd,
        budget_approved=True,
    )
    if not recovery_commit.committed:
        raise RuntimeError(f"recovery commit failed: {recovery_commit.reasons}")
    task = (
        task.transition(TaskStatus.RESERVED)
        .transition(TaskStatus.IN_PROGRESS)
        .transition(TaskStatus.COMPLETED)
    )
    trace.append(
        {
            "event": "recovery_committed",
            "task_version": task.version,
            "state_version": recovery_commit.state_version,
            "quantity": recovery.plan.allocated_quantity,
            "reallocated_quantity": recovery.reallocated_quantity,
            "unresolved_quantity": recovery.unresolved_quantity,
        }
    )

    report = {
        "scenario_id": scenario.scenario_id,
        "seed": scenario.seed,
        "system": "deterministic-recovery-reference",
        "status": task.status,
        "initial": {
            "allocated_quantity": initial_plan.allocated_quantity,
            "allocations": allocation_rows(initial_plan),
        },
        "failure": {
            "organization_id": scenario.failure_event.organization_id,
            "overcommitted_quantity": capacity_result.overcommitted_quantity,
        },
        "decision": {
            "required": True,
            "reason": "budget_approval_required",
            "approved": True,
        },
        "recovery": {
            "allocated_quantity": recovery.plan.allocated_quantity,
            "preserved_quantity": recovery.preserved_quantity,
            "reallocated_quantity": recovery.reallocated_quantity,
            "unresolved_quantity": recovery.unresolved_quantity,
            "changed_organizations": recovery.changed_organizations,
            "allocations": allocation_rows(recovery.plan),
        },
        "policy_violations": 0,
        "trace": trace,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
