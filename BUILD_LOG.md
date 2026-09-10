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
- Verified through visible console UI that the AWS Management Console session is authenticated; no account settings were changed during the check.
- Confirmed from current AWS documentation that AgentCore Runtime is supported in `ap-southeast-2` (Sydney).
- Added an auditable, credential-free IAM plan for a dedicated `agents-for-humans-dev` identity using temporary `aws login` credentials, Sydney-scoped AgentCore CLI build resources, and an explicit deny for unused user-ID delegation APIs.
- Created the dedicated `agents-for-humans-dev` IAM user with console access, mandatory first-login password reset, `SignInLocalDevelopmentAccess`, and `BedrockAgentCoreFullAccess`; no access key was created and the one-time password was left for the user to retrieve directly.
- Enabled MFA on the AWS root user, then limited further root use to the one-time IAM bootstrap work.
- Created the customer-managed `AgentsForHumansAgentCoreCliDev` policy from the checked-in JSON and attached it directly to `agents-for-humans-dev`; the user now has four direct policies including `IAMUserChangePassword`, and still requires first-login password reset plus user MFA before deployment.
- Verified the IAM user now has one assigned virtual MFA device (`agents-dev-authenticator-phone`); access keys remain at zero.
- Completed AWS CLI temporary browser login for `agents-for-humans-dev` without creating long-lived access keys; STS returned the expected IAM-user ARN.
- Configured the CLI profile region as `ap-southeast-2` and verified the read-only AgentCore control-plane call `list-agent-runtimes`, which currently returns no runtimes.

## Next milestone

Implement one Strands vertical slice on the now-frozen deterministic contract:

`Donation -> AllocationAgent -> policy check -> reserve capacity -> audit event`

## 2026-08-18 AgentCore vertical slice

- Added the serializable AgentCore HTTP adapter (`good_neighbor.agentcore.v1`) with explicit payload validation, approval/resume status, deterministic safety claims, impact counts, and the complete tool trace.
- Added five adapter contract tests; the full local suite now passes with 23 tests.
- Added the ARM64 container definition, generated `.dockerignore`, AgentCore project manifest, IAM runtime trust/execution policies, and a CDK synthesis project for auditability.
- `agentcore validate --json` passed. CDK TypeScript build and `cdk synth` passed.
- The CDK deployment path is intentionally not used: the account is not CDK-bootstrapped and the development identity was denied `cloudformation:DescribeStacks`; no broad CloudFormation/bootstrap permissions were added.
- Created the Sydney ECR repository `bedrock-agentcore-good-neighbor` with scan-on-push and AES256 encryption.
- Built and pushed a single-manifest `linux/arm64` image from AWS Public ECR base `python:3.12-slim`; the final image tag is `20260818-3` and the ECR digest begins `sha256:c1dd2e55`.
- Verified the same application through a local container: `/ping` returned `Healthy`; `/invocations` returned `completed`, 80 recovered meals, and zero policy violations. ARM64 QEMU did not return a local HTTP response, so this was not treated as cloud evidence.
- Direct `create-agent-runtime` was attempted with a fixed client token and the least-privilege execution role. AWS returned `ServiceQuotaExceededException: maxAgents limit exceeded`; `list-agent-runtimes` remains empty. This is an account/region quota blocker, not an application or IAM-role failure.
- S3 regional connectivity from the workstation timed out during the CodeZip fallback test; the ECR path remains healthy. No S3 bucket was assumed to exist.

## 2026-08-25 Judge experience and evaluation

- Restored temporary AWS CLI login for the dedicated IAM user; no long-lived access key was created.
- Verified through Service Quotas API that `Total Agents per Account` is currently 0 in both Virginia and Sydney and is region-specific.
- Verified two open requests: Virginia requests 1,000 and Sydney requests 1,200. Sydney remains the deployment target; no duplicate quota request was submitted.
- Added an English judge-facing web interface with Operations, Activity, and Decisions views. The demo stops at the USD 20 autonomy boundary, requires the persisted decision ID, and resumes to a policy-valid 80-meal plan.
- Added idempotent start, approve, and reset HTTP actions; wrong decision IDs and missing operation keys fail closed.
- Completed desktop visual QA of the local interface and HTTP smoke-tested ready -> awaiting decision -> completed with zero policy violations.
- Added a deterministic 60-case benchmark with explicit seeds and raw per-case results: 15 happy, 15 infeasible conflicts, 15 dynamic failures, 10 human boundaries, and 5 duplicate-event attacks.
- Benchmark result: static greedy full recovery 25%; bounded contract overall full recovery 75%; policy-safe 100%; feasible full recovery 100%; duplicate guard 100%; zero policy violations; +980 safe planned meals.
- Tightened the output contract to distinguish meals secured by a synthetic plan from verified physical deliveries; the prototype claims zero verified deliveries.
- Expanded the full automated suite to 30 passing tests, including judge API state transitions, fail-closed approval handling, packaged UI assets, benchmark reproducibility, and duplicate-event replay.
- Completed five consecutive end-to-end runs through the real Strands graph. All five completed in the expected Allocation -> Logistics -> Recovery order, secured an 80-meal synthetic plan, and reported zero policy violations.
- Pinned the container runtime to `bedrock-agentcore==1.21.0` and `strands-agents==1.52.0` so the contest image cannot silently drift to untested core SDK versions.
- Built and pushed the updated single-manifest `linux/arm64` contest image to the existing Sydney ECR repository as `20260825-1`; ECR reports Docker schema 2, 79,598,104 bytes, and digest prefix `sha256:090d2a79`.

## 2026-08-30 AgentCore cloud deployment

- Confirmed through Service Quotas API that Sydney `Total Agents per Account` is now 1,000 and that no Runtime existed before this deployment attempt.
- Replayed the container creation request and reached the next account initialization limit: the applied Docker image-size quota is 0 MB even though the AWS default is 2,048 MB and the verified image is only 79.6 MB.
- Used the official Direct Code alternative instead of waiting: generated a 30,324,048-byte ZIP from the exact tested ARM64 image, preserving the AgentCore 1.21.0 and Strands 1.52.0 dependencies, entrypoint, scenario, and native ARM64 wheels.
- Worked around a workstation route failure to the ordinary Sydney S3 endpoint by using the reachable Sydney dual-stack endpoint; created a private deterministic deployment bucket and uploaded the content-addressed ZIP.
- Extended the Runtime role with read-only access to the single deployment bucket and project prefix; no broad S3 permission was granted to the Runtime.
- Created `good_neighbor_runtime` through Direct Code with Python 3.12, HTTP protocol, public networking, five-minute idle timeout, fifteen-minute maximum lifetime, and a persisted idempotency token.
- Verified Runtime version 1 reached `READY` and reports `requireMMDSV2: true`.
- The first real cloud invocation reached the data plane but returned `maxVms limit exceeded`. `Active Session Workloads per Account` is 0, its AWS default is 2,500, and a Sydney quota request for 2,500 is now pending.

## 2026-09-09 First successful AgentCore invocation

- Reauthenticated the dedicated IAM user through temporary `aws login`; no long-lived access key was created.
- Audited the complete Sydney AgentCore quota surface and confirmed the applied `Active Session Workloads per Account` value is now 2,500. The Runtime, `DEFAULT` endpoint, Direct Code package limits, session-creation rate, and data-plane rate are sufficient for the contest path.
- Invoked the real Sydney `good_neighbor_runtime` version 1 through its AWS-IAM-authorized `DEFAULT` endpoint with a unique runtime session ID.
- AgentCore returned HTTP 200 and `application/json`. The incident graph ran Allocation -> Logistics -> Recovery, and the separate approval graph ran Recovery Resume.
- The cloud result preserved 60 valid meals, safely reallocated 20, completed an 80-meal synthetic plan, reported zero unresolved meals and zero policy violations, and continued to claim zero verified physical deliveries.
- CloudWatch recorded `Invocation completed successfully` with a measured Runtime execution time of 0.018 seconds.
- Preserved the complete public-safe response, tool trace, request, response hash, and sanitized cloud metadata in `evals/reports/agentcore_cloud_invocation_reference.json`; account, resource suffix, request ID, and session ID are omitted from committed evidence.
- Ran a second real AgentCore invocation without human approval. It returned HTTP 200 but correctly stopped at `pending_decision`, did not execute the recovery commit, claimed zero secured meals, and reported zero policy violations.
- CloudWatch independently recorded the human-boundary invocation as successful in 0.014 seconds. The sanitized response and three-tool trace are preserved in `evals/reports/agentcore_cloud_boundary_reference.json`.
- Reworded the judge UI boundary from the ambiguous negative-mark label `Self-approve extra spend` to the positive safety claim `Agent cannot self-approve extra spend`, based on observed user confusion; added an asset regression assertion.

## 2026-09-09 reproducible judge video

- Added a nine-segment, 4:18 demo narrative that opens with the problem and audience, demonstrates the real incident and human boundary, and closes on frozen-seed and AgentCore evidence.
- Synthesized the final English narration with Amazon Polly's Generative `Danielle` voice in Sydney instead of the local system voice; source text and segment timing remain reproducible.
- Added a Playwright/Edge recorder with chapter cards and an animated focus pointer for each real interaction, plus FFmpeg assembly with concise burned-in captions.
- Rendered `build/video/good-neighbor-demo.mp4` as H.264/AAC, 1440x900, 25 fps, 258.016 seconds, 12,330,814 bytes; SHA-256 is `39002d02b80e9bfa2722c5092c4832b468f2a4607d0affc99512f69bf2e9ce24`.
- Extracted and visually inspected representative frames covering the opening, incident, human-decision boundary, recovery, cloud evidence, and closing. The video contains no account IDs, runtime suffixes, session IDs, or physical-delivery claims.
- Uploaded the QA-checked cut to YouTube, supplied the complete English project description, marked it not made for children, passed YouTube's copyright check, and published it publicly at `https://youtu.be/54Mvj1xeBw4`.
- Created the public contest repository at `https://github.com/augustm210/good-neighbor-recovery-network` with a concise AgentCore/Strands project description and no server-generated starter files, preserving the local commit history for the initial push.

## 2026-09-10 Devpost submission draft

- Completed YouTube phone verification, uploaded the custom 1280x720 project thumbnail, and verified YouTube Studio reported all changes saved.
- Created the Devpost project `Good Neighbor Recovery Network` and saved its project name and elevator pitch.
- Added a truthful English project story, public GitHub repository, public 4:19 YouTube demo, Strands built-with entry, and reproducible testing instructions.
- Generated and visually QA-checked a 1500x1000 (3:2) architecture diagram covering the bounded agent graph, deterministic policy, human spending gate, AgentCore deployment, and evidence metrics; uploaded it to the Devpost draft.
- Selected the Good Neighbor Agents track and saved the required private submission fields. Devpost now reports `4/5 steps done` on the finalization page.
- Intentionally left the terms checkbox unchecked and did not click `Submit project`; the project remains a draft pending final visual and bonus-content review.
