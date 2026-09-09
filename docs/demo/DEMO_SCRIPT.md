# Five-minute demo script

Target duration: 4:40–4:55.

| Time | Beat |
|---|---|
| 0:00–0:25 | State the synthetic scenario: 80 meals expire tonight; coordination is fragmented. |
| 0:25–0:55 | Show the three-agent orbit and deterministic “what agents cannot do” boundary. |
| 0:55–1:35 | In Operations, click **Run capacity-drop incident**. Show the safe patch stopping at a decision. |
| 1:35–2:15 | Open Activity. Point to narrow tools, actor ownership, state versions, and verified results. |
| 2:15–3:20 | Open Decisions. Explain USD 32 versus the USD 20 autonomous limit; approve the persisted decision. |
| 3:20–3:55 | Return to Operations: A30/B15/C25/D10, 60 preserved, 20 moved, zero policy violations. |
| 3:55–4:30 | Show the 60-case report: 100% policy-safe, 100% feasible recovery, +980 safe planned meals. |
| 4:30–4:55 | Close with who it is for, why fragmented coordination matters, and the honest production boundary. |

Every automated claim shown in the video must have a corresponding trace event.

## Frozen truth table

| Moment | Safe allocation | System fact |
|---|---:|---|
| Initial commit | 80/80 | Cold 30 -> A; ambient 35 -> B; ambient 15 -> C. |
| B capacity drops | 60/80 valid, 20 overcommitted | Versioned event changes B from 35 to 15. |
| Recovery proposed | 80/80 feasible | Preserve 60; add 10 to C and 10 to D. |
| Policy boundary | Not executed | USD 32 exceeds the USD 20 autonomous limit. |
| Human approval | 80/80 committed | Final state A30/B15/C25/D10; zero unresolved. |

The presenter must not claim that allocation equals delivery. “80 secured”
means secured by a synthetic, policy-valid recovery plan; verified physical
deliveries remain zero in the prototype.
