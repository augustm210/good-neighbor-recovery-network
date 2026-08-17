from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .models import (
    CapacityChanged,
    Donation,
    FoodLot,
    HandlingRequirement,
    Organization,
)


@dataclass(frozen=True, slots=True)
class DemoScenario:
    scenario_id: str
    seed: int
    donation: Donation
    organizations: tuple[Organization, ...]
    failure_event: CapacityChanged
    autonomous_budget_usd: float
    recovery_route_cost_usd: float


def load_demo_scenario(path: str | Path) -> DemoScenario:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    donation_payload = payload["donation"]
    donation = Donation(
        donation_id=donation_payload["donation_id"],
        lots=tuple(
            FoodLot(
                lot_id=lot["lot_id"],
                donation_id=donation_payload["donation_id"],
                quantity=lot["quantity"],
                available_at=datetime.fromisoformat(lot["available_at"]),
                expires_at=datetime.fromisoformat(lot["expires_at"]),
                handling=HandlingRequirement(lot["handling"]),
            )
            for lot in donation_payload["lots"]
        ),
    )
    organizations = tuple(
        Organization(**organization) for organization in payload["organizations"]
    )
    event_payload = payload["failure_event"]
    event = CapacityChanged(
        event_id=event_payload["event_id"],
        organization_id=event_payload["organization_id"],
        new_capacity=event_payload["new_capacity"],
        new_version=event_payload["new_version"],
        at=datetime.fromisoformat(event_payload["at"]),
        idempotency_key=event_payload["idempotency_key"],
    )
    return DemoScenario(
        scenario_id=payload["scenario_id"],
        seed=payload["seed"],
        donation=donation,
        organizations=organizations,
        failure_event=event,
        autonomous_budget_usd=payload["autonomous_budget_usd"],
        recovery_route_cost_usd=payload["recovery_route_cost_usd"],
    )
