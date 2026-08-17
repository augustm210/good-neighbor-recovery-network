from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import timedelta

from .models import Allocation, AllocationPlan, Donation, Organization


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    reasons: tuple[str, ...]


def validate_plan(
    donation: Donation,
    organizations: list[Organization] | tuple[Organization, ...],
    plan: AllocationPlan,
    *,
    autonomous_budget_usd: float,
    budget_approved: bool = False,
    safety_margin: timedelta = timedelta(minutes=30),
) -> PolicyDecision:
    """Validate the complete proposed state transition, never just one row."""

    reasons: list[str] = []

    def reject(reason: str) -> None:
        if reason not in reasons:
            reasons.append(reason)

    if safety_margin < timedelta(0):
        raise ValueError("safety_margin cannot be negative")
    if autonomous_budget_usd < 0:
        raise ValueError("autonomous_budget_usd cannot be negative")
    if plan.donation_id != donation.donation_id:
        reject("donation_mismatch")
    if not plan.allocations:
        reject("empty_plan")

    lot_by_id = {lot.lot_id: lot for lot in donation.lots}
    organization_by_id = {
        organization.organization_id: organization for organization in organizations
    }
    if len(organization_by_id) != len(organizations):
        raise ValueError("organization_id values must be unique")

    lot_totals: Counter[str] = Counter()
    organization_totals: Counter[str] = Counter()
    operation_keys: list[str] = []

    for allocation in plan.allocations:
        operation_keys.append(allocation.idempotency_key)
        if allocation.donation_id != donation.donation_id:
            reject("donation_mismatch")

        lot = lot_by_id.get(allocation.lot_id)
        if lot is None:
            reject("unknown_lot")
        else:
            lot_totals[lot.lot_id] += allocation.quantity
            if allocation.pickup_at < lot.available_at:
                reject("pickup_before_available")
            if allocation.delivery_at > lot.expires_at - safety_margin:
                reject("delivery_after_safety_deadline")

        organization = organization_by_id.get(allocation.organization_id)
        if organization is None:
            reject("unknown_organization")
        else:
            organization_totals[organization.organization_id] += allocation.quantity
            if allocation.organization_version != organization.version:
                reject("organization_version_mismatch")
            if lot is not None and not organization.can_handle(lot):
                reject("cold_chain_required")

    if len(operation_keys) != len(set(operation_keys)):
        reject("duplicate_operation_key")

    for lot_id, quantity in lot_totals.items():
        if quantity > lot_by_id[lot_id].quantity:
            reject("lot_quantity_exceeded")

    for organization_id, quantity in organization_totals.items():
        if quantity > organization_by_id[organization_id].receivable_quantity:
            reject("organization_capacity_or_demand_exceeded")

    if plan.allocated_quantity > donation.quantity:
        reject("donation_quantity_exceeded")
    if plan.estimated_cost_usd > autonomous_budget_usd and not budget_approved:
        reject("budget_approval_required")

    return PolicyDecision(allowed=not reasons, reasons=tuple(reasons))


def validate_allocation(
    donation: Donation,
    organization: Organization,
    allocation: Allocation,
    *,
    autonomous_budget_usd: float = 0.0,
    safety_margin: timedelta = timedelta(minutes=30),
    seen_idempotency_keys: set[str] | None = None,
) -> PolicyDecision:
    """Compatibility helper for a one-row proposal; execution uses validate_plan."""

    plan = AllocationPlan(
        plan_id=f"single:{allocation.allocation_id}",
        donation_id=donation.donation_id,
        allocations=(allocation,),
        idempotency_key=f"single:{allocation.idempotency_key}",
    )
    decision = validate_plan(
        donation,
        [organization],
        plan,
        autonomous_budget_usd=autonomous_budget_usd,
        safety_margin=safety_margin,
    )
    if seen_idempotency_keys and allocation.idempotency_key in seen_idempotency_keys:
        return PolicyDecision(
            allowed=False,
            reasons=decision.reasons + ("duplicate_mutation",),
        )
    return decision
