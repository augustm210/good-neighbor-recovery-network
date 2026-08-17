from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace

from .models import Allocation, AllocationPlan, CapacityChanged, Donation, Organization


@dataclass(frozen=True, slots=True)
class RecoveryResult:
    plan: AllocationPlan
    preserved_quantity: int
    reallocated_quantity: int
    unresolved_quantity: int
    changed_organizations: tuple[str, ...]


def recover_after_capacity_change(
    donation: Donation,
    organizations: list[Organization] | tuple[Organization, ...],
    current_plan: AllocationPlan,
    event: CapacityChanged,
    *,
    based_on_state_version: int,
    incremental_cost_usd: float,
) -> RecoveryResult:
    """Patch only the capacity-invalid portion of the active plan."""

    lot_by_id = {lot.lot_id: lot for lot in donation.lots}
    organization_by_id = {
        organization.organization_id: organization for organization in organizations
    }
    target = organization_by_id[event.organization_id]
    assigned_to_target = sum(
        allocation.quantity
        for allocation in current_plan.allocations
        if allocation.organization_id == event.organization_id
    )
    excess = max(0, assigned_to_target - target.receivable_quantity)
    original_excess = excess

    kept: list[Allocation] = []
    freed_by_lot: Counter[str] = Counter()
    source_by_lot: dict[str, Allocation] = {}
    target_allocations = sorted(
        (
            allocation
            for allocation in current_plan.allocations
            if allocation.organization_id == event.organization_id
        ),
        key=lambda allocation: (
            lot_by_id[allocation.lot_id].requires_cold_chain,
            allocation.delivery_at,
            allocation.allocation_id,
        ),
    )
    target_ids = {allocation.allocation_id for allocation in target_allocations}
    kept.extend(
        allocation
        for allocation in current_plan.allocations
        if allocation.allocation_id not in target_ids
    )

    for allocation in target_allocations:
        reduction = min(excess, allocation.quantity)
        retained = allocation.quantity - reduction
        if retained:
            if reduction:
                kept.append(
                    replace(
                        allocation,
                        allocation_id=f"patch:{event.event_id}:{allocation.allocation_id}",
                        organization_version=target.version,
                        quantity=retained,
                        idempotency_key=(
                            f"reserve:patch:{event.event_id}:{allocation.allocation_id}"
                        ),
                    )
                )
            else:
                kept.append(replace(allocation, organization_version=target.version))
        if reduction:
            freed_by_lot[allocation.lot_id] += reduction
            source_by_lot[allocation.lot_id] = allocation
            excess -= reduction

    used_by_organization: Counter[str] = Counter()
    for allocation in kept:
        used_by_organization[allocation.organization_id] += allocation.quantity

    new_allocations: list[Allocation] = []
    unresolved = 0
    changed_organizations = {event.organization_id} if original_excess else set()
    for lot_id, freed_quantity in freed_by_lot.items():
        lot = lot_by_id[lot_id]
        remaining = freed_quantity
        candidates = sorted(
            (
                organization
                for organization in organizations
                if organization.can_handle(lot)
            ),
            key=lambda item: (-item.priority, item.distance_km, item.organization_id),
        )
        for organization in candidates:
            available = max(
                0,
                organization.receivable_quantity
                - used_by_organization[organization.organization_id],
            )
            quantity = min(remaining, available)
            if quantity == 0:
                continue
            source = source_by_lot[lot_id]
            allocation_id = (
                f"recovery:{event.event_id}:{lot_id}:{organization.organization_id}"
            )
            new_allocations.append(
                Allocation(
                    allocation_id=allocation_id,
                    donation_id=donation.donation_id,
                    lot_id=lot_id,
                    organization_id=organization.organization_id,
                    organization_version=organization.version,
                    quantity=quantity,
                    pickup_at=source.pickup_at,
                    delivery_at=source.delivery_at,
                    idempotency_key=f"reserve:{allocation_id}",
                )
            )
            used_by_organization[organization.organization_id] += quantity
            changed_organizations.add(organization.organization_id)
            remaining -= quantity
            if remaining == 0:
                break
        unresolved += remaining

    allocations = tuple(
        sorted(
            kept + new_allocations,
            key=lambda item: (item.lot_id, item.organization_id, item.allocation_id),
        )
    )
    plan = AllocationPlan(
        plan_id=f"recovery:{event.event_id}",
        donation_id=donation.donation_id,
        allocations=allocations,
        idempotency_key=f"commit:recovery:{event.event_id}",
        based_on_state_version=based_on_state_version,
        estimated_cost_usd=incremental_cost_usd,
    )
    return RecoveryResult(
        plan=plan,
        preserved_quantity=current_plan.allocated_quantity - original_excess,
        reallocated_quantity=original_excess - unresolved,
        unresolved_quantity=unresolved,
        changed_organizations=tuple(sorted(changed_organizations)),
    )
