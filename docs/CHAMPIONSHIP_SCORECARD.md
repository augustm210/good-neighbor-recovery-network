# Championship scorecard

Update this file with links to visible evidence, not confidence statements.

| Dimension | Evidence required | Current evidence | Status |
|---|---|---|---|
| Technical Implementation | Strands Graph, hooks, idempotency, recovery trace, AgentCore deployment | Real Strands 1.52 Graph, narrow tools, atomic/versioned ledger, bounded recovery, separate HITL resume, [reference trace](../evals/reports/strands_capacity_drop_reference.json), 18 tests; cloud deployment pending | In progress |
| Design | Operations, Activity, Decisions pages; ten-second comprehension test | Demo contract only | Not started |
| Potential Impact | 5+ interviews, 2 usability sessions, measured time/waste outcomes | Impact metric contract plus [AI-simulated red-team](research/AI_SIMULATED_REVIEW_PANEL.md) (not user evidence) | Not started |
| Creativity | Time decay, multi-org allocation, failure-aware patching, baseline lift | Executable minimal-change recovery reference; baseline lift still pending | In progress |
| Presentation | Public 4:40–4:55 video with working demo and pitch | Timed script | In progress |
| Bonus | Three substantial AWS Builder Center posts | Editorial plan | Not started |

## Stop-ship conditions

- Any executed policy violation.
- Full demo succeeds fewer than five consecutive times.
- Public links require authentication.
- Metrics cannot be reproduced from committed scripts and reports.
- Source license or AI-assistance disclosure is missing.
