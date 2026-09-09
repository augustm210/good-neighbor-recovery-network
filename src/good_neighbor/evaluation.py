from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from .baseline import greedy_allocate
from .policy import validate_plan
from .recovery import recover_after_capacity_change
from .reservation import InMemoryReservationLedger
from .scenario import DemoScenario


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    case_id: str
    seed: int
    category: str
    new_capacity: int
    route_cost_usd: float
    feasible_full_recovery: bool
    duplicate_event_attempt: bool = False


def build_benchmark_cases() -> tuple[BenchmarkCase, ...]:
    cases: list[BenchmarkCase] = []
    seed = 2026082500

    for index in range(15):
        cases.append(
            BenchmarkCase(
                case_id=f"happy-{index + 1:02d}",
                seed=seed + index,
                category="happy_path",
                new_capacity=35,
                route_cost_usd=0.0,
                feasible_full_recovery=True,
            )
        )
    seed += 100
    for index in range(15):
        cases.append(
            BenchmarkCase(
                case_id=f"conflict-{index + 1:02d}",
                seed=seed + index,
                category="constraint_conflict",
                new_capacity=index % 5,
                route_cost_usd=18.0,
                feasible_full_recovery=False,
            )
        )
    seed += 100
    for index in range(15):
        cases.append(
            BenchmarkCase(
                case_id=f"failure-{index + 1:02d}",
                seed=seed + index,
                category="dynamic_failure",
                new_capacity=5 + (index * 7) % 26,
                route_cost_usd=18.0,
                feasible_full_recovery=True,
            )
        )
    seed += 100
    for index in range(10):
        cases.append(
            BenchmarkCase(
                case_id=f"human-{index + 1:02d}",
                seed=seed + index,
                category="human_boundary",
                new_capacity=10 + (index * 5) % 16,
                route_cost_usd=32.0,
                feasible_full_recovery=True,
            )
        )
    seed += 100
    for index in range(5):
        cases.append(
            BenchmarkCase(
                case_id=f"adversarial-{index + 1:02d}",
                seed=seed + index,
                category="adversarial_replay",
                new_capacity=15,
                route_cost_usd=18.0,
                feasible_full_recovery=True,
                duplicate_event_attempt=True,
            )
        )
    return tuple(cases)


def evaluate_case(base: DemoScenario, case: BenchmarkCase) -> dict[str, Any]:
    event = replace(
        base.failure_event,
        event_id=f"event:{case.case_id}",
        new_capacity=case.new_capacity,
        idempotency_key=f"event:{case.case_id}",
    )
    ledger = InMemoryReservationLedger(base.donation, list(base.organizations))
    initial = greedy_allocate(
        base.donation,
        list(base.organizations),
        based_on_state_version=ledger.state_version,
        plan_id=f"initial:{case.case_id}",
    )
    initial_commit = ledger.commit_plan(
        initial,
        autonomous_budget_usd=base.autonomous_budget_usd,
    )
    if not initial_commit.committed:
        raise RuntimeError(f"initial commit failed for {case.case_id}")

    capacity_result = ledger.apply_capacity_change(event)
    if not capacity_result.applied:
        raise RuntimeError(f"capacity event failed for {case.case_id}")
    version_after_event = ledger.state_version
    duplicate_guard_passed: bool | None = None
    if case.duplicate_event_attempt:
        replay = ledger.apply_capacity_change(event)
        duplicate_guard_passed = (
            replay == capacity_result and ledger.state_version == version_after_event
        )

    recovery = recover_after_capacity_change(
        base.donation,
        ledger.organizations,
        initial,
        event,
        based_on_state_version=ledger.state_version,
        incremental_cost_usd=case.route_cost_usd,
    )
    budget_required = case.route_cost_usd > base.autonomous_budget_usd
    decision = validate_plan(
        base.donation,
        ledger.organizations,
        recovery.plan,
        autonomous_budget_usd=base.autonomous_budget_usd,
        budget_approved=budget_required,
    )
    bounded_complete = (
        decision.allowed
        and recovery.unresolved_quantity == 0
        and recovery.plan.allocated_quantity == base.donation.quantity
    )
    baseline_safe_quantity = initial.allocated_quantity - capacity_result.overcommitted_quantity

    return {
        "case_id": case.case_id,
        "seed": case.seed,
        "category": case.category,
        "inputs": {
            "new_capacity": case.new_capacity,
            "route_cost_usd": case.route_cost_usd,
            "feasible_full_recovery": case.feasible_full_recovery,
            "duplicate_event_attempt": case.duplicate_event_attempt,
        },
        "static_greedy": {
            "safe_quantity_after_failure": baseline_safe_quantity,
            "full_recovery": baseline_safe_quantity == base.donation.quantity,
            "unsafe_residual_quantity": capacity_result.overcommitted_quantity,
        },
        "bounded_recovery_contract": {
            "policy_safe": decision.allowed,
            "policy_violations": 0 if decision.allowed else len(decision.reasons),
            "full_recovery": bounded_complete,
            "preserved_quantity": recovery.preserved_quantity,
            "reallocated_quantity": recovery.reallocated_quantity,
            "unresolved_quantity": recovery.unresolved_quantity,
            "human_decision_required": budget_required,
            "duplicate_guard_passed": duplicate_guard_passed,
        },
    }


def run_benchmark(base: DemoScenario) -> dict[str, Any]:
    results = [evaluate_case(base, case) for case in build_benchmark_cases()]
    categories = {
        category: sum(result["category"] == category for result in results)
        for category in (
            "happy_path",
            "constraint_conflict",
            "dynamic_failure",
            "human_boundary",
            "adversarial_replay",
        )
    }
    feasible = [
        result for result in results if result["inputs"]["feasible_full_recovery"]
    ]
    adversarial = [
        result for result in results if result["inputs"]["duplicate_event_attempt"]
    ]

    def rate(numerator: int, denominator: int) -> float:
        return round(numerator / denominator, 4) if denominator else 0.0

    baseline_full = sum(result["static_greedy"]["full_recovery"] for result in results)
    bounded_safe = sum(
        result["bounded_recovery_contract"]["policy_safe"] for result in results
    )
    bounded_full = sum(
        result["bounded_recovery_contract"]["full_recovery"] for result in results
    )
    feasible_full = sum(
        result["bounded_recovery_contract"]["full_recovery"] for result in feasible
    )
    duplicate_passes = sum(
        result["bounded_recovery_contract"]["duplicate_guard_passed"] is True
        for result in adversarial
    )
    human_decisions = sum(
        result["bounded_recovery_contract"]["human_decision_required"]
        for result in results
    )
    baseline_safe_meals = sum(
        result["static_greedy"]["safe_quantity_after_failure"] for result in results
    )
    bounded_safe_meals = sum(
        80 - result["bounded_recovery_contract"]["unresolved_quantity"]
        for result in results
    )

    return {
        "schema_version": "good-neighbor.benchmark.v1",
        "suite": {
            "case_count": len(results),
            "seed_contract": "explicit per-case seeds; deterministic inputs",
            "categories": categories,
        },
        "summary": {
            "static_greedy": {
                "full_recovery_rate": rate(baseline_full, len(results)),
                "safe_meals_total": baseline_safe_meals,
            },
            "bounded_recovery_contract": {
                "policy_safe_rate": rate(bounded_safe, len(results)),
                "policy_violations": sum(
                    result["bounded_recovery_contract"]["policy_violations"]
                    for result in results
                ),
                "overall_full_recovery_rate": rate(bounded_full, len(results)),
                "feasible_full_recovery_rate": rate(feasible_full, len(feasible)),
                "duplicate_guard_rate": rate(duplicate_passes, len(adversarial)),
                "human_decisions": human_decisions,
                "safe_meals_total": bounded_safe_meals,
                "safe_meal_lift": bounded_safe_meals - baseline_safe_meals,
            },
        },
        "limitations": [
            "This suite evaluates the deterministic planning, policy, recovery, and idempotency contract.",
            "The real Strands three-agent topology is validated separately by the committed reference trace and SDK tests.",
            "No stochastic Bedrock model-quality claim is made by this offline benchmark.",
        ],
        "cases": results,
    }
