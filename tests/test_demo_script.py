from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_demo_script_produces_replayable_success_report() -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_demo.py")],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)

    assert report["status"] == "completed"
    assert report["initial"]["allocated_quantity"] == 80
    assert report["failure"]["overcommitted_quantity"] == 20
    assert report["decision"] == {
        "required": True,
        "reason": "budget_approval_required",
        "approved": True,
    }
    assert report["recovery"]["allocated_quantity"] == 80
    assert report["recovery"]["unresolved_quantity"] == 0
    assert report["policy_violations"] == 0
    assert [event["event"] for event in report["trace"]] == [
        "initial_plan_committed",
        "capacity_changed",
        "decision_required",
        "recovery_committed",
    ]
