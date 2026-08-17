# Build log

## 2026-08-17

- Registered Devpost account `augustm210` for Agents for Humans Hackathon.
- Narrowed the product from a general community coordinator to a perishability-aware surplus-food recovery network.
- Created a new local contest repository during the official build window.
- Added deterministic domain models, policy checks, a greedy baseline, a synthetic scenario, and unit tests.
- Verified local Python 3.12.3 and Git 2.48.1; Node/npm and AWS CLI were not available on PATH.
- Completed five independent AI-simulated expert reviews and preserved their consensus as a synthetic stakeholder red-team; explicitly did not count this as real-user evidence.
- Installed the current-user AWS CLI v2 package after verifying its AWS digital signature; verified `aws-cli/2.36.24` from the installed executable.
- Verified through visible browser UI that GitHub and AWS Builder Center are signed in; no credentials or browser storage were inspected.
- Replaced the donation-level cold-chain boolean with two independently constrained food lots: 30 cold-chain and 50 ambient meals.
- Added organization D and proved the post-failure world has 90 units of capacity, making the claimed 80/80 recovery feasible.
- Added complete-plan policy validation for lot and organization conservation, cold chain, time safety margins, state versions, duplicate operation keys, and budget approval.
- Added a thread-safe reference ledger with compare-and-swap state versions, stored idempotency results, and versioned capacity events.
- Added bounded recovery that preserves 60 valid meals, reallocates the 20 invalidated meals, and produces A30/B15/C25/D10.
- Added a persisted task state machine for approval/resume and a machine-readable end-to-end demo report.
- Expanded the suite from 4 tests to 16, including concurrent planners, idempotent replay, approval resume, plan-level over-allocation, recovery, and script-level replay.
- Added the real Strands Agents 1.52 SDK in an isolated repository virtual environment.
- Implemented a bounded three-node Strands Graph (Allocation -> Logistics -> Recovery) whose agents can mutate state only through narrow deterministic tools.
- Implemented approval as a separate Strands resume invocation keyed to the persisted decision rather than a suspended runtime session.
- Added an adversarial prompt test proving that model text cannot bypass the budget boundary or self-approve.
- Preserved a canonical machine-readable Strands tool trace and expanded the suite to 18 passing tests.
- Installed Node.js 24.19.0 LTS for the official AgentCore CLI/CDK prerequisite.
- Installed and version-verified AgentCore CLI 0.27.0 and AWS CDK 2.1136.0.
- Recorded the first AgentCore install failure: the new Node path was not visible to the current process, so the package postinstall could not find `node`; retrying with an explicit process PATH succeeded.
- Confirmed with a read-only probe that AWS CLI has no configured profile, region, or credentials; cloud deployment remains blocked on a non-root AWS API identity, not Builder ID login.

## Next milestone

Implement one Strands vertical slice on the now-frozen deterministic contract:

`Donation -> AllocationAgent -> policy check -> reserve capacity -> audit event`
