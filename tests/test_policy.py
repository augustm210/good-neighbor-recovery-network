from __future__ import annotations

import sys
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from good_neighbor import AllocationPlan, greedy_allocate, load_demo_scenario, validate_plan


def scenario_and_plan():
    scenario = load_demo_scenario(ROOT / "evals" / "scenarios" / "demo_scenario.json")
    plan = greedy_allocate(scenario.donation, list(scenario.organizations))
    return scenario, plan


def test_plan_rejects_cumulative_lot_and_organization_overallocation() -> None:
    scenario, plan = scenario_and_plan()
    source = next(item for item in plan.allocations if item.organization_id == "org-b")
    allocations = (
        replace(
            source,
            allocation_id="over-1",
            quantity=30,
            idempotency_key="reserve:over-1",
        ),
        replace(
            source,
            allocation_id="over-2",
            quantity=30,
            idempotency_key="reserve:over-2",
        ),
    )
    unsafe = AllocationPlan("unsafe", scenario.donation.donation_id, allocations, "commit:unsafe")

    decision = validate_plan(
        scenario.donation,
        scenario.organizations,
        unsafe,
        autonomous_budget_usd=20,
    )

    assert not decision.allowed
    assert "lot_quantity_exceeded" in decision.reasons
    assert "organization_capacity_or_demand_exceeded" in decision.reasons


def test_plan_rejects_early_pickup_and_late_delivery() -> None:
    scenario, plan = scenario_and_plan()
    source = plan.allocations[0]
    lot = scenario.donation.get_lot(source.lot_id)
    unsafe_allocation = replace(
        source,
        pickup_at=lot.available_at - timedelta(minutes=1),
        delivery_at=lot.expires_at,
    )
    unsafe = replace(plan, allocations=(unsafe_allocation,))

    decision = validate_plan(
        scenario.donation,
        scenario.organizations,
        unsafe,
        autonomous_budget_usd=20,
    )

    assert set(decision.reasons) == {
        "pickup_before_available",
        "delivery_after_safety_deadline",
    }


def test_plan_rejects_cold_chain_mismatch() -> None:
    scenario, plan = scenario_and_plan()
    source = next(item for item in plan.allocations if item.lot_id == "lot-cold-30")
    unsafe_allocation = replace(
        source,
        allocation_id="cold-to-ambient",
        organization_id="org-b",
        quantity=10,
        idempotency_key="reserve:cold-to-ambient",
    )
    unsafe = replace(plan, allocations=(unsafe_allocation,))

    decision = validate_plan(
        scenario.donation,
        scenario.organizations,
        unsafe,
        autonomous_budget_usd=20,
    )

    assert decision.reasons == ("cold_chain_required",)


def test_budget_boundary_requires_explicit_approval() -> None:
    scenario, plan = scenario_and_plan()
    costly = replace(plan, estimated_cost_usd=32)

    denied = validate_plan(
        scenario.donation,
        scenario.organizations,
        costly,
        autonomous_budget_usd=20,
    )
    approved = validate_plan(
        scenario.donation,
        scenario.organizations,
        costly,
        autonomous_budget_usd=20,
        budget_approved=True,
    )

    assert denied.reasons == ("budget_approval_required",)
    assert approved.allowed


def test_duplicate_operation_key_is_rejected_within_plan() -> None:
    scenario, plan = scenario_and_plan()
    first, second = plan.allocations[:2]
    duplicate = replace(second, idempotency_key=first.idempotency_key)
    unsafe = replace(plan, allocations=(first, duplicate))

    decision = validate_plan(
        scenario.donation,
        scenario.organizations,
        unsafe,
        autonomous_budget_usd=20,
    )

    assert "duplicate_operation_key" in decision.reasons
