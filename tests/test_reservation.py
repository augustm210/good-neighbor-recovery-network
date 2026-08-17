from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from good_neighbor import InMemoryReservationLedger, greedy_allocate, load_demo_scenario


def make_ledger_and_plan():
    scenario = load_demo_scenario(ROOT / "evals" / "scenarios" / "demo_scenario.json")
    ledger = InMemoryReservationLedger(scenario.donation, list(scenario.organizations))
    plan = greedy_allocate(
        scenario.donation,
        list(scenario.organizations),
        based_on_state_version=0,
    )
    return scenario, ledger, plan


def test_replay_returns_stored_result_without_second_mutation() -> None:
    scenario, ledger, plan = make_ledger_and_plan()

    first = ledger.commit_plan(plan, autonomous_budget_usd=scenario.autonomous_budget_usd)
    replay = ledger.commit_plan(plan, autonomous_budget_usd=scenario.autonomous_budget_usd)

    assert first == replay
    assert first.committed
    assert ledger.state_version == 1
    assert ledger.idempotency_record_count == 1


def test_competing_planners_cannot_both_commit_same_state_version() -> None:
    scenario, ledger, plan = make_ledger_and_plan()
    plans = (
        replace(plan, plan_id="planner-a", idempotency_key="commit:planner-a"),
        replace(plan, plan_id="planner-b", idempotency_key="commit:planner-b"),
    )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(
            executor.map(
                lambda candidate: ledger.commit_plan(
                    candidate,
                    autonomous_budget_usd=scenario.autonomous_budget_usd,
                ),
                plans,
            )
        )

    assert sum(result.committed for result in results) == 1
    assert sum(result.reasons == ("state_version_conflict",) for result in results) == 1
    assert ledger.state_version == 1


def test_capacity_event_is_idempotent_and_detects_overcommitment() -> None:
    scenario, ledger, plan = make_ledger_and_plan()
    assert ledger.commit_plan(
        plan,
        autonomous_budget_usd=scenario.autonomous_budget_usd,
    ).committed

    first = ledger.apply_capacity_change(scenario.failure_event)
    replay = ledger.apply_capacity_change(scenario.failure_event)

    assert first == replay
    assert first.applied
    assert first.overcommitted_quantity == 20
    assert ledger.state_version == 2
    assert ledger.idempotency_record_count == 2


def test_budget_denial_does_not_consume_mutation_key_before_approval() -> None:
    scenario, ledger, plan = make_ledger_and_plan()
    costly = replace(plan, estimated_cost_usd=32)

    denied = ledger.commit_plan(
        costly,
        autonomous_budget_usd=scenario.autonomous_budget_usd,
    )
    approved = ledger.commit_plan(
        costly,
        autonomous_budget_usd=scenario.autonomous_budget_usd,
        budget_approved=True,
    )

    assert denied.reasons == ("budget_approval_required",)
    assert not denied.committed
    assert approved.committed
    assert ledger.state_version == 1
    assert ledger.idempotency_record_count == 1
