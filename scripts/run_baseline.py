from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from good_neighbor import greedy_allocate, load_demo_scenario  # noqa: E402


def main() -> None:
    scenario = load_demo_scenario(ROOT / "evals" / "scenarios" / "demo_scenario.json")
    plan = greedy_allocate(scenario.donation, list(scenario.organizations))
    report = {
        "scenario_id": scenario.scenario_id,
        "seed": scenario.seed,
        "system": "greedy-baseline",
        "allocated_quantity": plan.allocated_quantity,
        "unallocated_quantity": scenario.donation.quantity - plan.allocated_quantity,
        "allocations": [
            {
                "lot_id": item.lot_id,
                "organization_id": item.organization_id,
                "organization_version": item.organization_version,
                "quantity": item.quantity,
                "idempotency_key": item.idempotency_key,
            }
            for item in plan.allocations
        ],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
