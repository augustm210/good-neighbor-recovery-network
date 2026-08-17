from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from good_neighbor import (
    InMemoryReservationLedger,
    greedy_allocate,
    load_demo_scenario,
    recover_after_capacity_change,
    validate_plan,
)


def test_capacity_drop_is_recovered_to_a_valid_minimal_change_80_of_80_plan() -> None:
    scenario = load_demo_scenario(ROOT / "evals" / "scenarios" / "demo_scenario.json")
    ledger = InMemoryReservationLedger(scenario.donation, list(scenario.organizations))
    initial = greedy_allocate(
        scenario.donation,
        list(scenario.organizations),
        based_on_state_version=0,
        plan_id="initial",
    )
    assert ledger.commit_plan(
        initial,
        autonomous_budget_usd=scenario.autonomous_budget_usd,
    ).committed
    event_result = ledger.apply_capacity_change(scenario.failure_event)
    assert event_result.overcommitted_quantity == 20

    recovery = recover_after_capacity_change(
        scenario.donation,
        ledger.organizations,
        initial,
        scenario.failure_event,
        based_on_state_version=ledger.state_version,
        incremental_cost_usd=scenario.recovery_route_cost_usd,
    )

    totals = Counter()
    for allocation in recovery.plan.allocations:
        totals[allocation.organization_id] += allocation.quantity
    assert totals == {"org-a": 30, "org-b": 15, "org-c": 25, "org-d": 10}
    assert recovery.plan.allocated_quantity == 80
    assert recovery.preserved_quantity == 60
    assert recovery.reallocated_quantity == 20
    assert recovery.unresolved_quantity == 0
    assert recovery.changed_organizations == ("org-b", "org-c", "org-d")

    pending = validate_plan(
        scenario.donation,
        ledger.organizations,
        recovery.plan,
        autonomous_budget_usd=scenario.autonomous_budget_usd,
    )
    approved = validate_plan(
        scenario.donation,
        ledger.organizations,
        recovery.plan,
        autonomous_budget_usd=scenario.autonomous_budget_usd,
        budget_approved=True,
    )
    assert pending.reasons == ("budget_approval_required",)
    assert approved.allowed
    assert ledger.commit_plan(
        recovery.plan,
        autonomous_budget_usd=scenario.autonomous_budget_usd,
        budget_approved=True,
    ).committed
    assert ledger.state_version == 3


def test_fixture_has_enough_post_failure_capacity_for_claimed_result() -> None:
    scenario = load_demo_scenario(ROOT / "evals" / "scenarios" / "demo_scenario.json")
    post_failure_capacity = sum(
        scenario.failure_event.new_capacity
        if organization.organization_id == scenario.failure_event.organization_id
        else organization.receivable_quantity
        for organization in scenario.organizations
    )

    assert post_failure_capacity == 90
    assert scenario.donation.quantity == 80
