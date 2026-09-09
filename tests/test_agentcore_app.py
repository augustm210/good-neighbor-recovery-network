from __future__ import annotations

import pytest

from good_neighbor.agentcore_app import run_incident_payload


def test_agentcore_payload_returns_completed_bounded_recovery_contract() -> None:
    report = run_incident_payload({"action": "run_incident", "approve": True})

    assert report["schema_version"] == "good-neighbor.agentcore.v1"
    assert report["status"] == "completed"
    assert report["incident_graph"]["execution_order"] == [
        "allocation",
        "logistics",
        "recovery",
    ]
    assert report["resume_graph"]["execution_order"] == ["recovery_resume"]
    assert report["active_plan"]["allocated_quantity"] == 80
    assert report["active_plan"]["allocations"] == [
        {"organization_id": "org-a", "quantity": 30},
        {"organization_id": "org-b", "quantity": 15},
        {"organization_id": "org-c", "quantity": 25},
        {"organization_id": "org-d", "quantity": 10},
    ]
    assert report["human_decision"]["approved"] is True
    assert report["human_decision"]["decision_id"] == "decision:recovery-budget"
    assert report["safety_boundary"]["policy_violations"] == 0
    assert report["impact"]["meals_secured_by_plan"] == 80
    assert report["impact"]["verified_deliveries"] == 0


def test_agentcore_payload_stops_before_unapproved_recovery_commit() -> None:
    report = run_incident_payload({"action": "run_incident", "approve": False})

    assert report["status"] == "pending_decision"
    assert report["resume_graph"]["status"] is None
    assert report["active_plan"]["plan_id"] == "strands-initial"
    assert report["recovery_proposal"]["allocated_quantity"] == 80
    assert report["human_decision"]["approved"] is False
    assert report["human_decision"]["decision_id"] == "decision:recovery-budget"
    assert report["impact"]["meals_secured_by_plan"] == 0
    assert all(
        entry["tool"] != "commit_approved_recovery"
        for entry in report["tool_trace"]
    )


@pytest.mark.parametrize(
    "payload",
    [
        {"action": "delete_everything"},
        {"approve": "yes"},
        {"task": ""},
    ],
)
def test_agentcore_payload_rejects_invalid_contract(payload: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        run_incident_payload(payload)
