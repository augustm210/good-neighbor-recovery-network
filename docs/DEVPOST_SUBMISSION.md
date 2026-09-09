# Devpost submission copy

Replace every `TODO_PUBLIC_*` placeholder before submitting.

## Project name

Good Neighbor Recovery Network

## Tagline

Safe multi-agent recovery for time-critical surplus food when real-world plans break.

## Track

Good Neighbor Agents

## Links

- Public repository: https://github.com/augustm210/good-neighbor-recovery-network
- Public video (YouTube, 4:19): https://youtu.be/54Mvj1xeBw4
- Optional public live demo: `TODO_PUBLIC_DEMO_URL`
- Builder Center posts: `TODO_PUBLIC_BUILDER_POST_URLS`

## Inspiration

Surplus food recovery is not primarily a matching problem. It is an execution
problem under changing constraints: a recipient loses capacity, a cold-chain
vehicle becomes unavailable, a volunteer route slips, or a recovery plan
crosses an approved budget. A conversational assistant can describe those
problems, but communities need a system that safely changes the plan and leaves
an auditable record of what happened.

Good Neighbor Recovery Network explores a narrow but important question: can a
multi-agent system recover a time-critical food allocation after a real-world
failure without inventing capacity, bypassing policy, or silently spending more
money?

## What it does

The prototype coordinates an 80-meal synthetic surplus-food incident across
four community organizations. Three distinct Strands agents own separate
responsibilities:

- AllocationAgent proposes the initial multi-organization allocation.
- LogisticsAgent records the versioned capacity failure.
- RecoveryAgent preserves valid work and proposes the smallest safe patch.

The initial plan allocates A30/B35/C15. When organization B drops from 35 to 15
meals of capacity, 20 meals become overcommitted. The system preserves 60 valid
meals and proposes A30/B15/C25/D10. Because the simulated route cost is USD 32
and the autonomous limit is USD 20, the agent cannot execute the patch by
itself. It stops at a persisted human decision. Approval resumes through a
separate graph invocation and deterministic policy validation before the plan
is committed.

The judge interface exposes three views—Operations, Activity, and Decisions—so
the outcome, tool trace, state versions, and human boundary can be understood
without reading source code.

## How we built it

The agent graph uses Strands Agents 1.52. Each agent can call only a narrow tool
for its responsibility; agent text cannot mutate operational state directly.
A deterministic policy layer checks inventory conservation, organization
capacity, demand, lot-specific cold-chain requirements, delivery time margins,
state versions, idempotency keys, and the autonomous budget. A compare-and-swap
reference ledger makes commits atomic and preserves prior results for duplicate
operation keys.

The application is deployed to Amazon Bedrock AgentCore Runtime in Sydney as a
Python 3.12 Direct Code package. Runtime version 1 and its DEFAULT endpoint are
READY, MMDSv2 is required, and AWS IAM authorizes invocation. Two real cloud
invocations are preserved in the repository:

1. Without approval, AgentCore returns HTTP 200 but stops at
   `pending_decision`, executes no recovery commit, and reports zero policy
   violations.
2. With approval, AgentCore returns HTTP 200, runs the separate recovery-resume
   graph, commits the 80-meal synthetic plan, and reports zero policy
   violations.

CloudWatch independently records both invocations as successful. The committed
evidence omits account and request identifiers while preserving response
hashes, complete business responses, and tool traces.

## Challenges we ran into

The hardest problem was separating plausible agent output from authorized
action. We solved this by moving hard constraints into deterministic tools and
policy hooks, requiring idempotency keys for every mutation, and ending the run
when human approval is missing.

AWS account initialization also exposed multiple zero-valued AgentCore quotas.
After the agent-count quota became available, the Docker image-size quota was
still zero. Instead of broadening IAM permissions or waiting indefinitely, we
used AgentCore Direct Code deployment. We generated a Linux ARM64-compatible
30.3 MB ZIP from the exact tested container dependencies, uploaded it to a
private Sydney S3 prefix, and granted the Runtime role read-only access to that
single prefix. Once active-session capacity became effective, both cloud
invocations succeeded.

## Accomplishments that we are proud of

- A real, bounded three-agent Strands graph rather than decorative agent roles.
- A fail-closed human budget boundary demonstrated locally and on AgentCore.
- Two HTTP 200 cloud invocations with complete traces and CloudWatch evidence.
- Thirty passing automated tests and five consecutive clean graph runs.
- A 60-case deterministic benchmark with committed seeds and raw per-case
  results: 100% policy-safe outcomes, 100% full recovery on mathematically
  feasible cases, 100% duplicate-event protection, zero policy violations, and
  980 more safely planned meals than the static greedy baseline.
- Honest impact language: 80 meals are secured by a synthetic, policy-valid
  plan; verified physical deliveries remain zero.

## What we learned

Agent safety is most convincing when it is visible as system behavior. The
important moment in this demo is not the successful final allocation; it is the
earlier moment when the agent refuses to execute a feasible plan because it
lacks spending authority. We also learned that recovery quality should be
measured only on feasible cases while infeasible cases must remain safe and
explicit rather than being counted as fictional successes.

## What's next

The next production step is to replace the in-memory reference ledger with
DynamoDB conditional transactions while preserving the same version and
idempotency contract. Real deployments would add authenticated organization
onboarding, verified pickup and delivery events, notification integrations,
route-provider pricing, and measured usability studies with coordinators. None
of those production capabilities or physical outcomes are claimed by this
prototype.

## Built with

- Strands Agents SDK 1.52
- Amazon Bedrock AgentCore Runtime
- AWS IAM
- Amazon S3
- Amazon ECR
- Amazon CloudWatch Logs
- Amazon Polly Generative (`Danielle`, used for the reproducible demo narration)
- Python 3.12
- HTML, CSS, and JavaScript
- pytest

## Testing instructions

1. Clone the public repository on Windows, macOS, or Linux with Python 3.11+.
2. Create a virtual environment and install `.[dev]`.
3. Run `python -m pytest -q`; all 30 tests should pass.
4. Run `python scripts/run_benchmark.py` to reproduce the 60-case report.
5. Run `python -m good_neighbor.demo_server --open`.
6. In Operations, run the capacity-drop incident.
7. Confirm the application stops at the USD 20 human boundary.
8. Inspect Activity and Decisions, then approve the persisted decision.
9. Confirm final allocation A30/B15/C25/D10, 80 planned meals, and zero policy
   violations.
10. Inspect the two committed AgentCore cloud evidence reports for the real
    no-approval and approved invocations.

The public video is a 4:18 H.264/AAC cut of this exact flow, with concise
captions and no private AWS identifiers.

No AWS credentials are required for local judging. The private AgentCore
endpoint is intentionally not exposed as a public unauthenticated service.
