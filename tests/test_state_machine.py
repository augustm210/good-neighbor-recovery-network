from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from good_neighbor import TaskState, TaskStatus


def test_pending_decision_is_persisted_and_resumes_by_versioned_transition() -> None:
    state = TaskState("task-1")
    state = state.transition(TaskStatus.PLANNED)
    state = state.transition(TaskStatus.RESERVED)
    state = state.transition(TaskStatus.IN_PROGRESS)
    state = state.transition(
        TaskStatus.PENDING_DECISION,
        pending_decision_id="decision-1",
    )

    assert state.version == 4
    assert state.pending_decision_id == "decision-1"
    resumed = state.transition(TaskStatus.PLANNED)
    assert resumed.version == 5
    assert resumed.pending_decision_id is None


def test_terminal_state_cannot_be_reopened() -> None:
    state = TaskState("task-1").transition(TaskStatus.FAILED)

    with pytest.raises(ValueError, match="invalid task transition"):
        state.transition(TaskStatus.PLANNED)
