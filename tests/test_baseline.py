from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from good_neighbor import greedy_allocate, load_demo_scenario, validate_plan


def test_greedy_allocates_mixed_lots_without_cross_lot_capacity_leak() -> None:
    scenario = load_demo_scenario(ROOT / "evals" / "scenarios" / "demo_scenario.json")
    plan = greedy_allocate(scenario.donation, list(scenario.organizations))

    assert plan.allocated_quantity == 80
    assert Counter(
        (allocation.lot_id, allocation.organization_id, allocation.quantity)
        for allocation in plan.allocations
    ) == Counter(
        {
            ("lot-cold-30", "org-a", 30): 1,
            ("lot-ambient-50", "org-b", 35): 1,
            ("lot-ambient-50", "org-c", 15): 1,
        }
    )
    assert validate_plan(
        scenario.donation,
        scenario.organizations,
        plan,
        autonomous_budget_usd=scenario.autonomous_budget_usd,
    ).allowed


def test_cold_chain_lot_never_reaches_ambient_only_organization() -> None:
    scenario = load_demo_scenario(ROOT / "evals" / "scenarios" / "demo_scenario.json")
    plan = greedy_allocate(scenario.donation, list(scenario.organizations))

    cold_allocations = [
        allocation
        for allocation in plan.allocations
        if allocation.lot_id == "lot-cold-30"
    ]
    assert {allocation.organization_id for allocation in cold_allocations} == {"org-a"}
