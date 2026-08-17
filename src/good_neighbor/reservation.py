from __future__ import annotations

from dataclasses import dataclass, replace
from threading import Lock

from .models import AllocationPlan, CapacityChanged, Donation, Organization
from .policy import validate_plan


@dataclass(frozen=True, slots=True)
class ReservationResult:
    committed: bool
    state_version: int
    reservation_ids: tuple[str, ...]
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CapacityChangeResult:
    applied: bool
    state_version: int
    overcommitted_quantity: int
    reasons: tuple[str, ...] = ()


class InMemoryReservationLedger:
    """Thread-safe reference semantics for a single donation task.

    DynamoDB conditional transactions will implement the same contract in AWS.
    This in-memory ledger exists to make concurrency and idempotency testable now.
    """

    def __init__(self, donation: Donation, organizations: list[Organization]) -> None:
        self._donation = donation
        self._organizations = {
            organization.organization_id: organization for organization in organizations
        }
        if len(self._organizations) != len(organizations):
            raise ValueError("organization_id values must be unique")
        self._state_version = 0
        self._active_plan: AllocationPlan | None = None
        self._mutation_results: dict[str, ReservationResult] = {}
        self._event_results: dict[str, CapacityChangeResult] = {}
        self._lock = Lock()

    @property
    def state_version(self) -> int:
        with self._lock:
            return self._state_version

    @property
    def active_plan(self) -> AllocationPlan | None:
        with self._lock:
            return self._active_plan

    @property
    def organizations(self) -> tuple[Organization, ...]:
        with self._lock:
            return tuple(self._organizations.values())

    @property
    def idempotency_record_count(self) -> int:
        with self._lock:
            return len(self._mutation_results) + len(self._event_results)

    def commit_plan(
        self,
        plan: AllocationPlan,
        *,
        autonomous_budget_usd: float,
        budget_approved: bool = False,
    ) -> ReservationResult:
        with self._lock:
            previous = self._mutation_results.get(plan.idempotency_key)
            if previous is not None:
                return previous

            if plan.based_on_state_version != self._state_version:
                result = ReservationResult(
                    committed=False,
                    state_version=self._state_version,
                    reservation_ids=(),
                    reasons=("state_version_conflict",),
                )
            else:
                decision = validate_plan(
                    self._donation,
                    list(self._organizations.values()),
                    plan,
                    autonomous_budget_usd=autonomous_budget_usd,
                    budget_approved=budget_approved,
                )
                if not decision.allowed:
                    result = ReservationResult(
                        committed=False,
                        state_version=self._state_version,
                        reservation_ids=(),
                        reasons=decision.reasons,
                    )
                else:
                    self._active_plan = plan
                    self._state_version += 1
                    result = ReservationResult(
                        committed=True,
                        state_version=self._state_version,
                        reservation_ids=tuple(
                            allocation.allocation_id for allocation in plan.allocations
                        ),
                    )
            # Only a committed mutation claims the operation key. A policy
            # denial is a read-only result; the same frozen plan must remain
            # executable after a separately persisted human approval.
            if result.committed:
                self._mutation_results[plan.idempotency_key] = result
            return result

    def apply_capacity_change(self, event: CapacityChanged) -> CapacityChangeResult:
        with self._lock:
            previous = self._event_results.get(event.idempotency_key)
            if previous is not None:
                return previous

            organization = self._organizations.get(event.organization_id)
            if organization is None:
                result = CapacityChangeResult(
                    applied=False,
                    state_version=self._state_version,
                    overcommitted_quantity=0,
                    reasons=("unknown_organization",),
                )
            elif event.new_version <= organization.version:
                result = CapacityChangeResult(
                    applied=False,
                    state_version=self._state_version,
                    overcommitted_quantity=0,
                    reasons=("stale_capacity_event",),
                )
            else:
                self._organizations[event.organization_id] = replace(
                    organization,
                    capacity=event.new_capacity,
                    version=event.new_version,
                )
                assigned = 0
                if self._active_plan is not None:
                    assigned = sum(
                        allocation.quantity
                        for allocation in self._active_plan.allocations
                        if allocation.organization_id == event.organization_id
                    )
                overcommitted = max(
                    0,
                    assigned - min(event.new_capacity, organization.demand),
                )
                self._state_version += 1
                result = CapacityChangeResult(
                    applied=True,
                    state_version=self._state_version,
                    overcommitted_quantity=overcommitted,
                )
            self._event_results[event.idempotency_key] = result
            return result
