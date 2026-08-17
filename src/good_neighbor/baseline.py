from __future__ import annotations

from datetime import timedelta

from .models import Allocation, AllocationPlan, Donation, Organization


def greedy_allocate(
    donation: Donation,
    organizations: list[Organization],
    *,
    based_on_state_version: int = 0,
    plan_id: str = "greedy-baseline",
) -> AllocationPlan:
    """Allocate constrained lots first, then priority and distance."""

    remaining_by_organization = {
        organization.organization_id: organization.receivable_quantity
        for organization in organizations
    }
    allocations: list[Allocation] = []
    lots = sorted(
        donation.lots,
        key=lambda lot: (not lot.requires_cold_chain, lot.expires_at, lot.lot_id),
    )

    for lot in lots:
        remaining = lot.quantity
        eligible = [
            organization
            for organization in organizations
            if organization.can_handle(lot)
        ]
        for organization in sorted(
            eligible,
            key=lambda item: (-item.priority, item.distance_km, item.organization_id),
        ):
            if remaining == 0:
                break
            available = remaining_by_organization[organization.organization_id]
            quantity = min(remaining, available)
            if quantity == 0:
                continue
            pickup_at = lot.available_at + timedelta(minutes=10)
            delivery_at = min(
                pickup_at + timedelta(hours=1),
                lot.expires_at - timedelta(minutes=30),
            )
            allocation_id = f"{plan_id}:{lot.lot_id}:{organization.organization_id}"
            allocations.append(
                Allocation(
                    allocation_id=allocation_id,
                    donation_id=donation.donation_id,
                    lot_id=lot.lot_id,
                    organization_id=organization.organization_id,
                    organization_version=organization.version,
                    quantity=quantity,
                    pickup_at=pickup_at,
                    delivery_at=delivery_at,
                    idempotency_key=f"reserve:{allocation_id}",
                )
            )
            remaining_by_organization[organization.organization_id] -= quantity
            remaining -= quantity

    return AllocationPlan(
        plan_id=plan_id,
        donation_id=donation.donation_id,
        allocations=tuple(allocations),
        idempotency_key=f"commit:{plan_id}",
        based_on_state_version=based_on_state_version,
    )
