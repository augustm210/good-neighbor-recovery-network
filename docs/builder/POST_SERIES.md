# AWS Builder Center bonus post series

Publish these as three separate public posts. Each title deliberately contains
“Agents for Humans”. Each post links to the public evidence repository.

---

## Post 1 — Agents for Humans: Why Our Food-Recovery Agents Cannot Approve Their Own Spending

An agent that can propose a useful plan is not automatically authorized to
execute it. That distinction became the core design rule of Good Neighbor
Recovery Network, our Agents for Humans Hackathon project.

The scenario is intentionally small and inspectable. Eighty surplus meals must
be allocated before they expire. AllocationAgent proposes A30/B35/C15.
LogisticsAgent then observes that organization B has lost 20 meals of capacity.
RecoveryAgent can preserve 60 valid meals and move the remaining 20, producing
A30/B15/C25/D10.

The recovery is feasible, but its simulated route cost is USD 32 while the
autonomous budget is USD 20. RecoveryAgent therefore cannot commit the plan.
It calls a narrow deterministic tool that checks inventory, capacity,
cold-chain, time, state-version, idempotency, and budget rules. The tool returns
a persisted decision ID and the graph ends in `pending_decision`.

This is stronger than telling a model “do not overspend” in a prompt. The agent
has no direct state-write capability, and the only commit tool requires a valid
human decision. An adversarial prompt cannot bypass that API contract.

We demonstrated the boundary twice: in the local three-view judge interface and
through a real Amazon Bedrock AgentCore Runtime invocation. Without approval,
AgentCore returned HTTP 200 but performed no recovery commit, reported zero
secured meals, and produced zero policy violations. With approval, a separate
Recovery Resume graph revalidated the decision and committed the 80-meal
synthetic plan.

The lesson is simple: useful autonomy needs visible authority boundaries.
Refusal is not a failed demo here; it is the most important successful behavior
in the system.

Repository: https://github.com/augustm210/good-neighbor-recovery-network

---

## Post 2 — Agents for Humans: Deploying a Strands Graph to AgentCore When Account Quotas Start at Zero

Our local Strands graph was working, but deploying it to Amazon Bedrock
AgentCore exposed a practical cloud-engineering challenge: several account
quotas initially had an applied value of zero.

The first blocker was Total Agents per Account. Once that became available, our
79.6 MB single-manifest Linux ARM64 container reached the next blocker: the
account's Docker image-size quota was still zero even though the documented
default was much larger.

Rather than add broad permissions or wait on another path, we used AgentCore
Direct Code deployment. We generated the ZIP from inside the exact tested ARM64
container, which preserved AgentCore 1.21.0, Strands Agents 1.52.0, our source,
the scenario, and compatible native wheels. The compressed package was only
30.3 MB.

We uploaded the content-addressed package to a private S3 bucket in Sydney. The
Runtime execution role received read-only access to one project prefix, plus
the CloudWatch permissions needed for Runtime logs. No long-lived AWS access
key was created; development used temporary `aws login` credentials. Runtime
version 1 reached READY with Python 3.12, HTTP protocol, public networking,
AWS-IAM authorization, and MMDSv2 required.

When active-session capacity later became effective, we ran two real calls
through the DEFAULT endpoint. Both returned HTTP 200, and CloudWatch recorded
successful completion. We preserved public-safe reports with response hashes
and complete tool traces while removing account, session, and request
identifiers.

The broader lesson is to treat deployment evidence as a chain: artifact hash,
least-privilege identity, Runtime status, endpoint status, invocation response,
and independent logs. A console screenshot alone is not enough.

Repository: https://github.com/augustm210/good-neighbor-recovery-network

---

## Post 3 — Agents for Humans: Evaluating Safe Recovery Without Inventing Success

Agent demos often show one happy path. We wanted evidence that Good Neighbor
Recovery Network remains safe when the world changes or when recovery is
mathematically impossible.

We built a deterministic 60-case benchmark with committed seeds and raw
per-case results:

- 15 happy paths
- 15 infeasible constraint conflicts
- 15 dynamic failures
- 10 human-approval boundaries
- 5 duplicate-event attacks

We compare a static greedy plan with the bounded recovery contract used by the
Strands agents. The benchmark separates two metrics that are easy to conflate:
safety and full recovery.

The bounded system achieved a 100% policy-safe rate, zero policy violations,
100% full recovery on mathematically feasible cases, and 100% duplicate-event
protection. Overall full recovery was 75%, because one quarter of the benchmark
is deliberately infeasible. Those cases report unresolved work instead of
inventing capacity. Across all cases, the bounded contract produced 980 more
safely planned meals than the static greedy baseline.

We also keep the impact claim narrow. “80 meals secured” means secured by a
synthetic, policy-valid plan. The prototype reports zero verified physical
deliveries and does not claim real beneficiaries. This distinction matters:
evaluation should make a system more credible, not inflate its story.

The same safety claims now have three layers of evidence: automated tests,
frozen benchmark reports, and paired real AgentCore invocations showing both
the no-approval boundary and the approved recovery path.

Repository: https://github.com/augustm210/good-neighbor-recovery-network
