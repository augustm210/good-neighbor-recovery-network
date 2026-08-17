# Good Neighbor Recovery Network

Championship-oriented starter repository for the **Agents for Humans Hackathon**.

The product wedge is narrow by design: coordinate time-sensitive surplus-food recovery across multiple community organizations when capacity, cold-chain, volunteer, route, and budget constraints can change during execution.

## Why an agentic system

- `AllocationAgent` proposes a multi-organization allocation plan.
- `LogisticsAgent` proposes volunteer and route assignments.
- `RecoveryAgent` patches the current plan after a failure event.
- Deterministic policy hooks decide whether a mutation is safe to execute.

The starter included here intentionally implements the deterministic foundation first: domain models, policy checks, a reproducible greedy baseline, scenario fixtures, and tests.

## Quickstart

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\run_baseline.py
.\.venv\Scripts\python.exe scripts\run_demo.py
.\.venv\Scripts\python.exe scripts\run_strands_graph.py
```

Python 3.11+ is sufficient. No cloud credentials are required for the baseline.

## Repository map

- `src/good_neighbor/` — domain models, policy engine, baseline planner.
- `evals/scenarios/` — deterministic evaluation fixtures.
- `docs/evaluation/` — metric and benchmark contract.
- `docs/demo/` — five-minute demo script.
- `infrastructure/` — reserved for minimal AWS deployment.
- `BUILD_LOG.md` — dated evidence of work performed during the contest window.
- `DISCLOSURES.md` — AI-assistance and pre-existing-work disclosure.

## First engineering gate — complete

Do not connect an LLM or deploy to AWS until the deterministic layer passes:

1. Plan-level lot and organization conservation.
2. Lot-specific cold-chain enforcement.
3. Pickup, delivery, expiry, and safety-margin enforcement.
4. Persistent-result idempotency semantics and optimistic state versions.
5. Atomic all-plan commit under competing planners.
6. Bounded minimal-change recovery after a versioned capacity event.
7. Persisted human-decision state when cost exceeds the autonomous boundary.

The reference incident is now mathematically valid: 30 cold-chain and 50 ambient
meals are initially allocated `A30/B35/C15`. After B drops to 15, the recovery
plan preserves 60 meals and moves 20 to produce `A30/B15/C25/D10`. The proposed
USD 32 route cost is blocked by the USD 20 autonomous budget until approval.

## Status

- Devpost registration: complete for account `augustm210`.
- Deterministic policy, transactional reference ledger, recovery, and HITL state: included and tested.
- Reference incident: reproducible 80/80 recovery with zero policy violations.
- Real Strands 1.52 Graph: Allocation -> Logistics -> Recovery, followed by a separate approval-resume invocation.
- Offline SDK evidence uses a clearly labeled frozen tool-calling model; Bedrock inference is not yet claimed.
- AgentCore deployment and cloud trace: next implementation milestone.

See [ARCHITECTURE.md](ARCHITECTURE.md) and [docs/CHAMPIONSHIP_SCORECARD.md](docs/CHAMPIONSHIP_SCORECARD.md).
