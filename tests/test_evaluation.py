from __future__ import annotations

from pathlib import Path

from good_neighbor.evaluation import build_benchmark_cases, run_benchmark
from good_neighbor.scenario import load_demo_scenario


ROOT = Path(__file__).resolve().parents[1]


def test_benchmark_case_mix_and_seeds_are_frozen() -> None:
    cases = build_benchmark_cases()

    assert len(cases) == 60
    assert len({case.case_id for case in cases}) == 60
    assert len({case.seed for case in cases}) == 60
    assert {category: sum(case.category == category for case in cases) for category in {
        "happy_path",
        "constraint_conflict",
        "dynamic_failure",
        "human_boundary",
        "adversarial_replay",
    }} == {
        "happy_path": 15,
        "constraint_conflict": 15,
        "dynamic_failure": 15,
        "human_boundary": 10,
        "adversarial_replay": 5,
    }


def test_benchmark_proves_safe_recovery_and_idempotency_without_overclaiming() -> None:
    scenario = load_demo_scenario(ROOT / "evals" / "scenarios" / "demo_scenario.json")
    report = run_benchmark(scenario)
    bounded = report["summary"]["bounded_recovery_contract"]

    assert bounded["policy_safe_rate"] == 1.0
    assert bounded["policy_violations"] == 0
    assert bounded["feasible_full_recovery_rate"] == 1.0
    assert bounded["duplicate_guard_rate"] == 1.0
    assert bounded["human_decisions"] == 10
    assert bounded["safe_meal_lift"] > 0
    assert report["limitations"]


def test_infeasible_cases_remain_safe_and_report_unresolved_work() -> None:
    scenario = load_demo_scenario(ROOT / "evals" / "scenarios" / "demo_scenario.json")
    report = run_benchmark(scenario)
    conflicts = [case for case in report["cases"] if case["category"] == "constraint_conflict"]

    assert all(case["bounded_recovery_contract"]["policy_safe"] for case in conflicts)
    assert all(case["bounded_recovery_contract"]["full_recovery"] is False for case in conflicts)
    assert all(case["bounded_recovery_contract"]["unresolved_quantity"] > 0 for case in conflicts)
