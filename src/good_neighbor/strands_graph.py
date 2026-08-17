from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from typing import Any, AsyncGenerator, AsyncIterable

from strands import Agent, tool
from strands.models import Model
from strands.multiagent import GraphBuilder
from strands.types.content import Messages
from strands.types.streaming import StreamEvent
from strands.types.tools import ToolSpec

from .baseline import greedy_allocate
from .models import AllocationPlan, TaskState, TaskStatus
from .policy import validate_plan
from .recovery import RecoveryResult, recover_after_capacity_change
from .reservation import InMemoryReservationLedger
from .scenario import DemoScenario


class FrozenToolModel(Model):
    """Offline model that deterministically invokes one named Strands tool.

    This is an integration fixture, not the production intelligence layer. It
    proves the real Strands agent loop and Graph execute our tool contracts
    without making tests depend on network access or stochastic model output.
    """

    def __init__(self, tool_name: str, tool_input: dict[str, Any]) -> None:
        self._config = {
            "model_id": f"frozen-tool-model:{tool_name}",
            "tool_name": tool_name,
        }
        self._tool_name = tool_name
        self._tool_input = dict(tool_input)

    def get_config(self) -> dict[str, Any]:
        return dict(self._config)

    def update_config(self, **model_config: Any) -> None:
        self._config.update(model_config)

    async def stream(
        self,
        messages: Messages,
        tool_specs: list[ToolSpec] | None = None,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[StreamEvent]:
        del system_prompt, kwargs
        has_tool_result = bool(
            messages
            and any("toolResult" in block for block in messages[-1].get("content", []))
        )
        yield {"messageStart": {"role": "assistant"}}
        if has_tool_result:
            yield {
                "contentBlockDelta": {
                    "delta": {"text": f"{self._tool_name} completed through policy tools."}
                }
            }
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "end_turn"}}
            return

        available_names = {
            spec["name"] for spec in (tool_specs or []) if "name" in spec
        }
        if self._tool_name not in available_names:
            raise RuntimeError(f"required tool is unavailable: {self._tool_name}")
        tool_use_id = f"frozen:{self._tool_name}"
        yield {
            "contentBlockStart": {
                "start": {
                    "toolUse": {
                        "toolUseId": tool_use_id,
                        "name": self._tool_name,
                    }
                }
            }
        }
        yield {
            "contentBlockDelta": {
                "delta": {"toolUse": {"input": json.dumps(self._tool_input)}}
            }
        }
        yield {"contentBlockStop": {}}
        yield {"messageStop": {"stopReason": "tool_use"}}

    async def structured_output(
        self,
        output_model: type[Any],
        prompt: Messages,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[dict[str, Any], None]:
        del output_model, prompt, system_prompt, kwargs
        if False:  # pragma: no cover - keeps this method an async generator
            yield {}
        raise NotImplementedError("FrozenToolModel does not provide structured output")


@dataclass(slots=True)
class ChampionshipRunContext:
    scenario: DemoScenario
    ledger: InMemoryReservationLedger
    task: TaskState
    initial_plan: AllocationPlan | None = None
    recovery: RecoveryResult | None = None
    trace: list[dict[str, Any]] = field(default_factory=list)
    tool_results: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def create(cls, scenario: DemoScenario) -> ChampionshipRunContext:
        return cls(
            scenario=scenario,
            ledger=InMemoryReservationLedger(
                scenario.donation,
                list(scenario.organizations),
            ),
            task=TaskState(task_id=f"task:{scenario.scenario_id}"),
        )

    def replay(self, idempotency_key: str) -> dict[str, Any] | None:
        if not idempotency_key.strip():
            raise ValueError("idempotency_key is required")
        return self.tool_results.get(idempotency_key)

    def record(
        self,
        idempotency_key: str,
        *,
        actor: str,
        tool_name: str,
        before_version: int,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        frozen_result = dict(result)
        self.tool_results[idempotency_key] = frozen_result
        self.trace.append(
            {
                "actor": actor,
                "tool": tool_name,
                "idempotency_key": idempotency_key,
                "before_state_version": before_version,
                "after_state_version": self.ledger.state_version,
                "result": frozen_result,
            }
        )
        return frozen_result


@dataclass(frozen=True, slots=True)
class StrandsIncidentResult:
    context: ChampionshipRunContext
    incident_status: str
    incident_execution_order: tuple[str, ...]
    resume_status: str | None = None
    resume_execution_order: tuple[str, ...] = ()


def _incident_graph(context: ChampionshipRunContext):
    @tool(
        name="propose_and_commit_initial_plan",
        description="Build, policy-check, and atomically commit the frozen initial plan.",
    )
    def propose_and_commit_initial_plan(idempotency_key: str) -> dict[str, Any]:
        """Commit the initial safe plan.

        Args:
            idempotency_key: Unique operation key for this mutation.
        """
        replay = context.replay(idempotency_key)
        if replay is not None:
            return replay
        before = context.ledger.state_version
        plan = greedy_allocate(
            context.scenario.donation,
            list(context.scenario.organizations),
            based_on_state_version=before,
            plan_id="strands-initial",
        )
        plan = replace(plan, idempotency_key=idempotency_key)
        policy = validate_plan(
            context.scenario.donation,
            context.scenario.organizations,
            plan,
            autonomous_budget_usd=context.scenario.autonomous_budget_usd,
        )
        if not policy.allowed:
            raise RuntimeError(f"initial policy rejected: {policy.reasons}")
        context.task = context.task.transition(TaskStatus.PLANNED)
        committed = context.ledger.commit_plan(
            plan,
            autonomous_budget_usd=context.scenario.autonomous_budget_usd,
        )
        if not committed.committed:
            raise RuntimeError(f"initial commit failed: {committed.reasons}")
        context.task = context.task.transition(TaskStatus.RESERVED).transition(
            TaskStatus.IN_PROGRESS
        )
        context.initial_plan = plan
        return context.record(
            idempotency_key,
            actor="allocation_agent",
            tool_name="propose_and_commit_initial_plan",
            before_version=before,
            result={
                "status": "committed",
                "allocated_quantity": plan.allocated_quantity,
                "state_version": committed.state_version,
            },
        )

    @tool(
        name="observe_capacity_change",
        description="Apply the frozen versioned capacity event and report overcommitment.",
    )
    def observe_capacity_change(idempotency_key: str) -> dict[str, Any]:
        """Apply one versioned capacity event.

        Args:
            idempotency_key: Unique operation key for this mutation.
        """
        replay = context.replay(idempotency_key)
        if replay is not None:
            return replay
        before = context.ledger.state_version
        event = replace(context.scenario.failure_event, idempotency_key=idempotency_key)
        result = context.ledger.apply_capacity_change(event)
        if not result.applied:
            raise RuntimeError(f"capacity event failed: {result.reasons}")
        return context.record(
            idempotency_key,
            actor="logistics_agent",
            tool_name="observe_capacity_change",
            before_version=before,
            result={
                "status": "capacity_changed",
                "overcommitted_quantity": result.overcommitted_quantity,
                "state_version": result.state_version,
            },
        )

    @tool(
        name="propose_bounded_recovery",
        description="Patch invalid work and persist a decision when policy blocks execution.",
    )
    def propose_bounded_recovery(idempotency_key: str) -> dict[str, Any]:
        """Create a minimal recovery proposal without bypassing approval.

        Args:
            idempotency_key: Unique operation key for this state transition.
        """
        replay = context.replay(idempotency_key)
        if replay is not None:
            return replay
        if context.initial_plan is None:
            raise RuntimeError("initial plan is unavailable")
        before = context.ledger.state_version
        recovery = recover_after_capacity_change(
            context.scenario.donation,
            context.ledger.organizations,
            context.initial_plan,
            context.scenario.failure_event,
            based_on_state_version=before,
            incremental_cost_usd=context.scenario.recovery_route_cost_usd,
        )
        policy = validate_plan(
            context.scenario.donation,
            context.ledger.organizations,
            recovery.plan,
            autonomous_budget_usd=context.scenario.autonomous_budget_usd,
        )
        if policy.reasons != ("budget_approval_required",):
            raise RuntimeError(f"unexpected recovery policy result: {policy.reasons}")
        context.recovery = recovery
        context.task = context.task.transition(
            TaskStatus.PENDING_DECISION,
            pending_decision_id="decision:recovery-budget",
        )
        return context.record(
            idempotency_key,
            actor="recovery_agent",
            tool_name="propose_bounded_recovery",
            before_version=before,
            result={
                "status": "pending_decision",
                "reason": "budget_approval_required",
                "preserved_quantity": recovery.preserved_quantity,
                "reallocated_quantity": recovery.reallocated_quantity,
                "unresolved_quantity": recovery.unresolved_quantity,
            },
        )

    allocation_agent = Agent(
        agent_id="allocation-agent",
        name="Allocation Agent",
        model=FrozenToolModel(
            "propose_and_commit_initial_plan",
            {"idempotency_key": "tool:strands:initial"},
        ),
        tools=[propose_and_commit_initial_plan],
        system_prompt="Propose allocations only through the deterministic planning tool.",
        callback_handler=None,
    )
    logistics_agent = Agent(
        agent_id="logistics-agent",
        name="Logistics Agent",
        model=FrozenToolModel(
            "observe_capacity_change",
            {"idempotency_key": "tool:strands:capacity-event"},
        ),
        tools=[observe_capacity_change],
        system_prompt="Observe execution state only through versioned tools.",
        callback_handler=None,
    )
    recovery_agent = Agent(
        agent_id="recovery-agent",
        name="Recovery Agent",
        model=FrozenToolModel(
            "propose_bounded_recovery",
            {"idempotency_key": "tool:strands:recovery-proposal"},
        ),
        tools=[propose_bounded_recovery],
        system_prompt="Patch invalid work; never bypass deterministic policy or HITL.",
        callback_handler=None,
    )

    builder = GraphBuilder()
    builder.add_node(allocation_agent, "allocation")
    builder.add_node(logistics_agent, "logistics")
    builder.add_node(recovery_agent, "recovery")
    builder.add_edge("allocation", "logistics")
    builder.add_edge("logistics", "recovery")
    builder.set_entry_point("allocation")
    builder.set_max_node_executions(3)
    builder.set_execution_timeout(30)
    builder.set_node_timeout(10)
    builder.set_graph_id("good-neighbor-incident")
    return builder.build()


def _resume_graph(context: ChampionshipRunContext, decision_id: str):
    @tool(
        name="commit_approved_recovery",
        description="Commit the frozen recovery plan after verifying persisted approval.",
    )
    def commit_approved_recovery(
        idempotency_key: str,
        decision_id: str,
    ) -> dict[str, Any]:
        """Commit a previously blocked recovery.

        Args:
            idempotency_key: Unique operation key for the approved mutation.
            decision_id: Persisted human decision identifier.
        """
        replay = context.replay(idempotency_key)
        if replay is not None:
            return replay
        if context.recovery is None:
            raise RuntimeError("recovery proposal is unavailable")
        if context.task.status is not TaskStatus.PENDING_DECISION:
            raise RuntimeError("task is not waiting for a decision")
        if context.task.pending_decision_id != decision_id:
            raise RuntimeError("decision_id does not match the pending decision")
        before = context.ledger.state_version
        approved_plan = replace(
            context.recovery.plan,
            idempotency_key=idempotency_key,
            based_on_state_version=before,
        )
        policy = validate_plan(
            context.scenario.donation,
            context.ledger.organizations,
            approved_plan,
            autonomous_budget_usd=context.scenario.autonomous_budget_usd,
            budget_approved=True,
        )
        if not policy.allowed:
            raise RuntimeError(f"approved recovery rejected: {policy.reasons}")
        context.task = context.task.transition(TaskStatus.PLANNED)
        committed = context.ledger.commit_plan(
            approved_plan,
            autonomous_budget_usd=context.scenario.autonomous_budget_usd,
            budget_approved=True,
        )
        if not committed.committed:
            raise RuntimeError(f"approved recovery commit failed: {committed.reasons}")
        context.task = (
            context.task.transition(TaskStatus.RESERVED)
            .transition(TaskStatus.IN_PROGRESS)
            .transition(TaskStatus.COMPLETED)
        )
        return context.record(
            idempotency_key,
            actor="recovery_agent",
            tool_name="commit_approved_recovery",
            before_version=before,
            result={
                "status": "completed",
                "allocated_quantity": approved_plan.allocated_quantity,
                "state_version": committed.state_version,
                "decision_id": decision_id,
            },
        )

    resume_agent = Agent(
        agent_id="recovery-resume-agent",
        name="Recovery Resume Agent",
        model=FrozenToolModel(
            "commit_approved_recovery",
            {
                "idempotency_key": "tool:strands:approved-recovery",
                "decision_id": decision_id,
            },
        ),
        tools=[commit_approved_recovery],
        system_prompt="Resume only the persisted, approved recovery plan.",
        callback_handler=None,
    )
    builder = GraphBuilder()
    builder.add_node(resume_agent, "recovery_resume")
    builder.set_entry_point("recovery_resume")
    builder.set_max_node_executions(1)
    builder.set_execution_timeout(15)
    builder.set_node_timeout(10)
    builder.set_graph_id("good-neighbor-resume")
    return builder.build()


def run_strands_incident(
    scenario: DemoScenario,
    *,
    task: str = "Execute the frozen surplus-food capacity-drop scenario.",
    approve: bool = True,
) -> StrandsIncidentResult:
    context = ChampionshipRunContext.create(scenario)
    incident = _incident_graph(context)(task)
    result = StrandsIncidentResult(
        context=context,
        incident_status=incident.status.value,
        incident_execution_order=tuple(
            node.node_id for node in incident.execution_order
        ),
    )
    if not approve:
        return result

    decision_id = context.task.pending_decision_id
    if decision_id is None:
        raise RuntimeError("incident did not persist a decision")
    resume = _resume_graph(context, decision_id)(
        "Resume the frozen recovery after the persisted human approval."
    )
    return replace(
        result,
        resume_status=resume.status.value,
        resume_execution_order=tuple(node.node_id for node in resume.execution_order),
    )
