from __future__ import annotations

from pathlib import Path

import pytest

from good_neighbor.demo_server import DemoController, WEB_ROOT


def test_demo_controller_stops_for_decision_then_resumes_safely() -> None:
    controller = DemoController()

    pending = controller.apply("start", {"idempotency_key": "demo:start:1"})
    assert pending["stage"] == "awaiting_decision"
    assert pending["report"]["status"] == "pending_decision"
    assert pending["report"]["impact"]["meals_secured_by_plan"] == 0
    assert pending["report"]["recovery_proposal"]["allocated_quantity"] == 80

    completed = controller.apply(
        "approve",
        {
            "idempotency_key": "demo:approve:1",
            "decision_id": pending["report"]["human_decision"]["decision_id"],
        },
    )
    assert completed["stage"] == "completed"
    assert completed["report"]["status"] == "completed"
    assert completed["report"]["impact"]["meals_secured_by_plan"] == 80
    assert completed["report"]["safety_boundary"]["policy_violations"] == 0


def test_demo_controller_replays_each_mutation_idempotently() -> None:
    controller = DemoController()
    first = controller.apply("start", {"idempotency_key": "demo:start:stable"})
    replay = controller.apply("start", {"idempotency_key": "demo:start:stable"})

    assert replay == first
    assert replay["sequence"] == 1


def test_demo_controller_rejects_wrong_decision_and_missing_key() -> None:
    controller = DemoController()
    controller.apply("start", {"idempotency_key": "demo:start:2"})

    with pytest.raises(ValueError, match="decision_id"):
        controller.apply(
            "approve",
            {"idempotency_key": "demo:approve:2", "decision_id": "wrong"},
        )
    with pytest.raises(ValueError, match="idempotency_key"):
        controller.apply("reset", {})


def test_judge_ui_assets_are_packaged_and_expose_three_views() -> None:
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    assert {path.name for path in WEB_ROOT.iterdir()} == {
        "app.css",
        "app.js",
        "evidence.html",
        "index.html",
    }
    assert "Operations" in html
    assert "Activity" in html
    assert "Decisions" in html
    assert "Run capacity-drop incident" in html
    assert "Agent cannot self-approve extra spend" in html
    assert ">Self-approve extra spend<" not in html
    evidence = (WEB_ROOT / "evidence.html").read_text(encoding="utf-8")
    assert "2 × HTTP 200" in evidence
    assert "Zero fictional deliveries" in evidence
