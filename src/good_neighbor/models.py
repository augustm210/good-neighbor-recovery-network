from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from math import isfinite


def _require_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


class HandlingRequirement(StrEnum):
    AMBIENT = "ambient"
    COLD_CHAIN = "cold_chain"


@dataclass(frozen=True, slots=True)
class FoodLot:
    lot_id: str
    donation_id: str
    quantity: int
    available_at: datetime
    expires_at: datetime
    handling: HandlingRequirement = HandlingRequirement.AMBIENT

    def __post_init__(self) -> None:
        if not self.lot_id.strip() or not self.donation_id.strip():
            raise ValueError("lot_id and donation_id are required")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        _require_aware(self.available_at, "available_at")
        _require_aware(self.expires_at, "expires_at")
        if self.expires_at <= self.available_at:
            raise ValueError("expires_at must be after available_at")

    @property
    def requires_cold_chain(self) -> bool:
        return self.handling is HandlingRequirement.COLD_CHAIN


@dataclass(frozen=True, slots=True)
class Donation:
    donation_id: str
    lots: tuple[FoodLot, ...]

    def __post_init__(self) -> None:
        if not self.donation_id.strip():
            raise ValueError("donation_id is required")
        object.__setattr__(self, "lots", tuple(self.lots))
        if not self.lots:
            raise ValueError("a donation must contain at least one lot")
        lot_ids = [lot.lot_id for lot in self.lots]
        if len(lot_ids) != len(set(lot_ids)):
            raise ValueError("lot_id values must be unique within a donation")
        if any(lot.donation_id != self.donation_id for lot in self.lots):
            raise ValueError("every lot must belong to the donation")

    @property
    def quantity(self) -> int:
        return sum(lot.quantity for lot in self.lots)

    def get_lot(self, lot_id: str) -> FoodLot:
        for lot in self.lots:
            if lot.lot_id == lot_id:
                return lot
        raise KeyError(lot_id)


@dataclass(frozen=True, slots=True)
class Organization:
    organization_id: str
    capacity: int
    demand: int
    priority: int
    distance_km: float
    cold_chain: bool = False
    version: int = 1

    def __post_init__(self) -> None:
        if not self.organization_id.strip():
            raise ValueError("organization_id is required")
        if self.capacity < 0 or self.demand < 0:
            raise ValueError("capacity and demand cannot be negative")
        if self.priority < 0:
            raise ValueError("priority cannot be negative")
        if not isfinite(self.distance_km) or self.distance_km < 0:
            raise ValueError("distance must be a finite non-negative number")
        if self.version <= 0:
            raise ValueError("version must be positive")

    @property
    def receivable_quantity(self) -> int:
        return min(self.capacity, self.demand)

    def can_handle(self, lot: FoodLot) -> bool:
        return not lot.requires_cold_chain or self.cold_chain


@dataclass(frozen=True, slots=True)
class Allocation:
    allocation_id: str
    donation_id: str
    lot_id: str
    organization_id: str
    organization_version: int
    quantity: int
    pickup_at: datetime
    delivery_at: datetime
    idempotency_key: str

    def __post_init__(self) -> None:
        required = (
            self.allocation_id,
            self.donation_id,
            self.lot_id,
            self.organization_id,
            self.idempotency_key,
        )
        if any(not value.strip() for value in required):
            raise ValueError("allocation identifiers and idempotency_key are required")
        if self.organization_version <= 0:
            raise ValueError("organization_version must be positive")
        if self.quantity <= 0:
            raise ValueError("allocation quantity must be positive")
        _require_aware(self.pickup_at, "pickup_at")
        _require_aware(self.delivery_at, "delivery_at")
        if self.delivery_at < self.pickup_at:
            raise ValueError("delivery_at cannot be before pickup_at")


@dataclass(frozen=True, slots=True)
class AllocationPlan:
    plan_id: str
    donation_id: str
    allocations: tuple[Allocation, ...]
    idempotency_key: str
    based_on_state_version: int = 0
    estimated_cost_usd: float = 0.0

    def __post_init__(self) -> None:
        if not self.plan_id.strip() or not self.donation_id.strip():
            raise ValueError("plan_id and donation_id are required")
        if not self.idempotency_key.strip():
            raise ValueError("plan idempotency_key is required")
        object.__setattr__(self, "allocations", tuple(self.allocations))
        if self.based_on_state_version < 0:
            raise ValueError("based_on_state_version cannot be negative")
        if not isfinite(self.estimated_cost_usd) or self.estimated_cost_usd < 0:
            raise ValueError("estimated_cost_usd must be finite and non-negative")
        allocation_ids = [item.allocation_id for item in self.allocations]
        if len(allocation_ids) != len(set(allocation_ids)):
            raise ValueError("allocation_id values must be unique within a plan")

    @property
    def allocated_quantity(self) -> int:
        return sum(item.quantity for item in self.allocations)


@dataclass(frozen=True, slots=True)
class CapacityChanged:
    event_id: str
    organization_id: str
    new_capacity: int
    new_version: int
    at: datetime
    idempotency_key: str

    def __post_init__(self) -> None:
        if any(
            not value.strip()
            for value in (self.event_id, self.organization_id, self.idempotency_key)
        ):
            raise ValueError("capacity event identifiers are required")
        if self.new_capacity < 0:
            raise ValueError("new_capacity cannot be negative")
        if self.new_version <= 0:
            raise ValueError("new_version must be positive")
        _require_aware(self.at, "at")


class TaskStatus(StrEnum):
    CREATED = "created"
    PLANNED = "planned"
    RESERVED = "reserved"
    IN_PROGRESS = "in_progress"
    PENDING_DECISION = "pending_decision"
    COMPLETED = "completed"
    FAILED = "failed"


_ALLOWED_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.CREATED: frozenset({TaskStatus.PLANNED, TaskStatus.FAILED}),
    TaskStatus.PLANNED: frozenset(
        {TaskStatus.RESERVED, TaskStatus.PENDING_DECISION, TaskStatus.FAILED}
    ),
    TaskStatus.RESERVED: frozenset(
        {TaskStatus.IN_PROGRESS, TaskStatus.PENDING_DECISION, TaskStatus.FAILED}
    ),
    TaskStatus.IN_PROGRESS: frozenset(
        {TaskStatus.PENDING_DECISION, TaskStatus.COMPLETED, TaskStatus.FAILED}
    ),
    TaskStatus.PENDING_DECISION: frozenset(
        {TaskStatus.PLANNED, TaskStatus.FAILED}
    ),
    TaskStatus.COMPLETED: frozenset(),
    TaskStatus.FAILED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class TaskState:
    task_id: str
    status: TaskStatus = TaskStatus.CREATED
    version: int = 0
    pending_decision_id: str | None = None

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("task_id is required")
        if self.version < 0:
            raise ValueError("version cannot be negative")
        if self.status is TaskStatus.PENDING_DECISION and not self.pending_decision_id:
            raise ValueError("pending_decision_id is required for pending decisions")
        if self.status is not TaskStatus.PENDING_DECISION and self.pending_decision_id:
            raise ValueError("pending_decision_id is only valid for pending decisions")

    def transition(
        self,
        status: TaskStatus,
        *,
        pending_decision_id: str | None = None,
    ) -> TaskState:
        if status not in _ALLOWED_TRANSITIONS[self.status]:
            raise ValueError(f"invalid task transition: {self.status} -> {status}")
        return replace(
            self,
            status=status,
            version=self.version + 1,
            pending_decision_id=pending_decision_id,
        )
