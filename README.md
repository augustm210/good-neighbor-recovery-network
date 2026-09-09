# Good Neighbor Recovery Network

Championship-oriented working prototype for the **Agents for Humans Hackathon**.

The product wedge is narrow by design: coordinate time-sensitive surplus-food recovery across multiple community organizations when capacity, cold-chain, volunteer, route, and budget constraints can change during execution.

## Why an agentic system

- `AllocationAgent` proposes a multi-organization allocation plan.
- `LogisticsAgent` proposes volunteer and route assignments.
- `RecoveryAgent` patches the current plan after a failure event.
- Deterministic policy hooks decide whether a mutation is safe to execute.

The prototype implements the deterministic foundation first, then exposes it
through a real Strands Graph, an AgentCore-compatible HTTP boundary, and a
judge-facing operations interface.

## Quickstart

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\run_baseline.py
.\.venv\Scripts\python.exe scripts\run_demo.py
.\.venv\Scripts\python.exe scripts\run_strands_graph.py
.\.venv\Scripts\python.exe scripts\run_benchmark.py
.\.venv\Scripts\python.exe -m good_neighbor.demo_server --open
```

Python 3.11+ is sufficient. No cloud credentials are required for the baseline.

## Repository map

- `src/good_neighbor/` — domain models, policy engine, Strands Graph, AgentCore adapter, and demo server.
- `evals/scenarios/` — deterministic evaluation fixtures.
- `evals/reports/` — committed machine-readable reference traces and benchmark evidence.
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
- Judge demo: Operations, Activity, and Decisions views backed by idempotent local HTTP actions.
- Evaluation: 60 frozen-seed cases; 100% policy-safe outcomes, zero policy violations, and 100% full recovery on mathematically feasible cases.
- AgentCore: a Python 3.12 Direct Code Runtime is `READY` in Sydney with MMDSv2 required. A real `DEFAULT` endpoint invocation returned HTTP 200, completed the incident and approval-resume graphs, secured an 80-meal synthetic plan, and reported zero policy violations; the [sanitized cloud evidence](evals/reports/agentcore_cloud_invocation_reference.json) includes the complete tool trace and CloudWatch completion record.

## Evidence, not promises

- [Real AgentCore human-boundary invocation](evals/reports/agentcore_cloud_boundary_reference.json) — HTTP 200, stops at `pending_decision` without approval, CloudWatch-confirmed success.
- [Real AgentCore approved invocation](evals/reports/agentcore_cloud_invocation_reference.json) — HTTP 200, complete graph and resume trace, CloudWatch-confirmed success.

- [60-case benchmark report](evals/reports/benchmark_reference.json)
- [Canonical Strands tool trace](evals/reports/strands_capacity_drop_reference.json)
- [Architecture and safety boundary](ARCHITECTURE.md)
- [Five-minute judge demo](docs/demo/DEMO_SCRIPT.md)
- [Public 4:19 demo video](https://youtu.be/54Mvj1xeBw4) — working product, human boundary, evaluation, and real AgentCore evidence.
- [Reproducible video segments](docs/demo/video_segments.json) — generates a 4:18 working-demo cut with short captions and chapter cards.
- [AI and pre-existing-work disclosure](DISCLOSURES.md)

“80 meals” is a synthetic planning scenario. The prototype measures meals
secured by a policy-valid plan; it does not claim that physical deliveries took
place or that real people were served.

See [ARCHITECTURE.md](ARCHITECTURE.md) and [docs/CHAMPIONSHIP_SCORECARD.md](docs/CHAMPIONSHIP_SCORECARD.md).

## Reproduce the demo video

On Windows with FFmpeg, AWS CLI, and a temporary authenticated project profile:

```powershell
.\scripts\render_demo_video.ps1
```

The renderer uses Amazon Polly Generative voice `Danielle` in Sydney for the
English narration, records the live judge interface in Edge, burns concise
captions, and writes `build/video/good-neighbor-demo.mp4`. Use `-ReuseAudio`
when changing visuals or caption styling without synthesizing the narration
again.
