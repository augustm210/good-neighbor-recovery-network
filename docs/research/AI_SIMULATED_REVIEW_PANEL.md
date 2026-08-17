# Synthetic stakeholder red-team

Date: 2026-08-17

> This panel contains five independent AI-simulated expert reviews. It is hypothesis generation and product red-teaming, not real-user research, usability testing, an interview study, or evidence of impact.

## Panel

| Reviewer role | Current-readiness view | Primary concern |
|---|---:|---|
| Food-rescue operations lead | 3.5/10 | The model cannot represent mixed cold-chain lots or real custody and logistics states. |
| Hackathon judge | 12.5/50 | The plan has a 42–46/50 ceiling, but the current repository is still a scaffold rather than a judged product. |
| AWS agent architecture reviewer | 2/10 technical implementation | No real Strands graph, AgentCore deployment, transactional reservation, trace, or resumable HITL exists yet. |
| Nonprofit product/UX lead | 2.6/10 | Operations, Activity, and Decisions are names in a plan, not a tested interface backed by live state. |
| Agent evaluation and safety researcher | 2.5/10 | Safety claims are not yet supported by plan-level invariants, concurrency tests, or replayable evaluation evidence. |

## Unanimous stop-ship findings

1. **The flagship 80/80 recovery is mathematically impossible in the current fixture.** After organization B drops from 35 to 15, total capacity is only `30 + 15 + 25 = 70`. Add an organization with at least 10 units of valid spare capacity, or report an honest 70/80 result and escalate the remaining 10.
2. **The 30/80 cold-chain story cannot be represented.** A donation-level boolean cannot model 30 cold-chain and 50 ambient meals. Introduce `FoodLot` or `DonationLine` and allocate against individual lots.
3. **Single-allocation policy checks do not prove plan safety.** Add `validate_plan`, conservation checks, cumulative organization capacity, valid time windows, load, route, budget, and all-or-nothing reservation semantics.
4. **The current idempotency check is not idempotent execution.** Persist an operation key and result through an atomic claim/mutate/audit workflow; replays must return the first result without another mutation.
5. **Recovery and HITL exist only in prose.** Use a versioned state machine. Preserve completed legal work, patch only invalid unfinished work, persist pending decisions, and resume in a new runtime invocation after approval.
6. **The three-agent AWS architecture is not implemented.** A minimal credible slice is one AgentCore Runtime containing one Strands graph, deterministic local tools/hooks, DynamoDB state and reservations, CloudWatch/AgentCore traces, and frozen S3 evaluation artifacts.
7. **Five AI reviews are not five users.** They may guide failure cases and interface hypotheses, but they cannot be presented as interview, usability, trust, adoption, or impact evidence.

## Frozen hard invariants

- Inventory: `reserved + picked_up + delivered + disposed <= accepted_quantity` for every lot.
- Capacity: active reservations never exceed the current versioned organization capacity.
- Cold chain: every segment and receiver for a cold-chain lot has the required capability.
- Time: `available_at <= pickup <= delivery <= expires_at - safety_margin`.
- Terminal state: every accepted unit ends in exactly one of Delivered, Rejected, or Disposed.
- Budget: cumulative incremental cost above the authorized threshold cannot execute.
- Idempotency: one operation key produces at most one state mutation across retries and crashes.
- Recovery: completed valid actions are never recreated; patches address only unfinished invalid work.
- Concurrency: at most one competing planner commits against a given state version.
- Audit: every state change records run, trace, actor, policy version, and before/after state version.

## Minimum test matrix before UI polish

| Test | Pass condition |
|---|---|
| Two allocations exceed one lot | Entire plan rejected; no partial reservation. |
| 30 cold-chain + 50 ambient | Each lot independently satisfies handling constraints. |
| Early pickup/delivery, expiry, safety margin | Deterministic policy returns the correct result for every boundary. |
| 20 concurrent requests for the last 10 units | Only one valid reservation wins; quantity never becomes negative. |
| Replay the same mutation 100 times | One mutation; identical stored result is returned. |
| Crash at claim, write, and audit boundaries | Restart creates no duplicate or orphan reservation. |
| Capacity drop after partial pickup | Only unfinished work is patched; in-transit work is preserved. |
| Several small costs exceed the total budget | Approval is required before any over-budget mutation. |
| Duplicate, delayed, and out-of-order events | Only a newer state version has an effect. |
| Tampered result with persuasive rationale | Deterministic ledger marks the run as failed. |

## 72-hour championship order

1. **0–12 hours:** repair the demo world, introduce lot-level data, add the fourth organization/spare capacity, freeze three expected ledgers, define the state machine and invariants, and create the first traceable Git commit.
2. **12–30 hours:** implement plan validation, atomic reservation, optimistic versioning, persistent idempotency, cumulative budget checks, and concurrency/boundary tests.
3. **30–48 hours:** implement one real Strands vertical slice, consume the capacity-drop event, produce append-only JSONL trace, and complete bounded minimal-change recovery plus persisted approval/resume.
4. **48–60 hours:** run Greedy, Single-Agent, and Strands Graph against the same scenarios, events, tools, retry limits, and budgets; store paired outputs, seeds, configuration, and confidence intervals.
5. **60–72 hours:** bind the three-page UI to real state and trace, meet WCAG 2.2 AA basics, and run the complete incident scenario successfully five times in a row before visual polish.

## UX contract

- **Operations** answers: what is happening, how many units are safely committed, where risk remains, and whether human action is needed.
- **Activity** is an audit timeline: actor, action, reason, result, and evidence link—not raw logs.
- **Decisions** contains only boundary-crossing approvals, including cost delta, expiry risk, affected lots/routes, alternatives, exact mutations, audit ID, and separate approved-versus-executed states.

## Evidence boundary

This document can be cited as `synthetic stakeholder red-team`. It must never be cited as “five users,” “five interviews,” “user validation,” or “field evidence.” The championship scorecard therefore keeps Potential Impact user evidence at **Not started**.
