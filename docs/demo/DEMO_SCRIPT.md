# Five-minute demo script

Target duration: 4:40–4:55.

| Time | Beat |
|---|---|
| 0:00–0:25 | 80 meals will expire tonight; coordination is fragmented. |
| 0:25–0:55 | Show the three-agent graph and deterministic safety boundary. |
| 0:55–2:10 | Allocation and logistics run; policy hooks allow safe mutations. |
| 2:10–3:25 | Inject organization capacity drop; Recovery Agent patches the active plan. |
| 3:25–4:05 | Cost exceeds autonomous limit; human sees evidence and approves. |
| 4:05–4:35 | Show benchmark lift versus greedy and single-agent baselines. |
| 4:35–4:55 | Show user evidence, impact metrics, and the final result. |

Every automated claim shown in the video must have a corresponding trace event.

## Frozen truth table

| Moment | Safe allocation | System fact |
|---|---:|---|
| Initial commit | 80/80 | Cold 30 -> A; ambient 35 -> B; ambient 15 -> C. |
| B capacity drops | 60/80 valid, 20 overcommitted | Versioned event changes B from 35 to 15. |
| Recovery proposed | 80/80 feasible | Preserve 60; add 10 to C and 10 to D. |
| Policy boundary | Not executed | USD 32 exceeds the USD 20 autonomous limit. |
| Human approval | 80/80 committed | Final state A30/B15/C25/D10; zero unresolved. |

The presenter must not claim that allocation equals delivery. The final impact
metric counts only verified, on-time, policy-compliant delivery.
