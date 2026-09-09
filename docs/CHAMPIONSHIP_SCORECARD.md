# Championship scorecard

Update this file with links to visible evidence, not confidence statements.

| Dimension | Evidence required | Current evidence | Status |
|---|---|---|---|
| Technical Implementation | Strands Graph, hooks, idempotency, recovery trace, AgentCore deployment | Real Strands 1.52 Graph, narrow tools, atomic/versioned ledger, bounded recovery, separate HITL resume, 30 passing tests, and 5/5 clean end-to-end graph runs; Sydney AgentCore Runtime version 1 is `READY` with MMDSv2; paired HTTP 200 cloud evidence proves [fail-closed human control](../evals/reports/agentcore_cloud_boundary_reference.json) and [approved recovery](../evals/reports/agentcore_cloud_invocation_reference.json), both with zero policy violations | Strong |
| Design | Operations, Activity, Decisions pages; ten-second comprehension test | Three-view judge interface implemented and visually checked at desktop and responsive breakpoints | In progress |
| Potential Impact | 5+ interviews, 2 usability sessions, measured time/waste outcomes | Synthetic planning metric and [AI-simulated red-team](research/AI_SIMULATED_REVIEW_PANEL.md) clearly labeled as non-user evidence; no physical delivery claim | At risk |
| Creativity | Time decay, multi-org allocation, failure-aware patching, baseline lift | 60-case [benchmark](../evals/reports/benchmark_reference.json): +980 safe planned meals versus static greedy; infeasible cases remain safe and explicit | Strong |
| Presentation | Public video no longer than five minutes with working demo and pitch | [Public 4:19 YouTube demo](https://youtu.be/54Mvj1xeBw4) with live interaction, Amazon Polly Generative narration, concise captions, chapter cards, and AgentCore evidence; copyright checks passed | Strong |
| Bonus | Three substantial AWS Builder Center posts | Three distinct publish-ready drafts in [POST_SERIES.md](builder/POST_SERIES.md); publication pending | Ready to publish |

## Stop-ship conditions

- Any executed policy violation.
- Full demo succeeds fewer than five consecutive times.
- Public links require authentication.
- Metrics cannot be reproduced from committed scripts and reports.
- Source license or AI-assistance disclosure is missing.

## Current quantitative evidence

- 60 deterministic cases with committed seeds and raw per-case results.
- Policy-safe rate: 100%; policy violations: 0.
- Full recovery rate on mathematically feasible cases: 100%.
- Duplicate-event replay guard: 100%.
- Overall full recovery: 75%; the remaining 25% are deliberately infeasible constraint-conflict cases and report unresolved work instead of inventing capacity.
- Full automated suite: 30 passing tests.
- End-to-end Strands graph reliability check: 5/5 clean runs, each securing an 80-meal synthetic plan with zero policy violations.
