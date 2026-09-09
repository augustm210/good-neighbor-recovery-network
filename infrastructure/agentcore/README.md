# AgentCore Runtime

This is the minimum cloud slice for the contest incident. It deploys the real
Strands graph behind an AWS-IAM-authorized AgentCore HTTP runtime. The current
runtime deliberately uses the frozen tool-calling model so the cloud trace is
reproducible; it does not claim Bedrock model inference.

## Local account target

`agentcore/aws-targets.json` is intentionally ignored because it contains the
AWS account ID. Copy `agentcore/aws-targets.example.json`, replace the account
placeholder locally, and keep the target region as `ap-southeast-2`.

## Verify and deploy

```powershell
aws sts get-caller-identity --profile agents-for-humans-dev
agentcore validate
agentcore deploy --target default --yes --verbose
agentcore status --target default
agentcore invoke --target default '{"action":"run_incident","approve":true}'
```

If the account has not been CDK-bootstrapped, the same container can be built
by the Sydney-scoped CodeBuild project using `buildspec.yml` and then registered
through `bedrock-agentcore-control create-agent-runtime`. This avoids granting
the development user broad CloudFormation bootstrap permissions. The exact
resource inventory and teardown commands must be recorded in `BUILD_LOG.md`.

The initial direct ECR path used for reproducible container evidence is:

```powershell
$image = "ACCOUNT_ID.dkr.ecr.ap-southeast-2.amazonaws.com/bedrock-agentcore-good-neighbor:IMAGE_TAG"
aws bedrock-agentcore-control create-agent-runtime `
  --agent-runtime-name good_neighbor_runtime `
  --agent-runtime-artifact "{\"containerConfiguration\":{\"containerUri\":\"$image\"}}" `
  --role-arn arn:aws:iam::ACCOUNT_ID:role/AmazonBedrockAgentCoreGoodNeighborRuntimeRole `
  --network-configuration '{"networkMode":"PUBLIC"}' `
  --protocol-configuration '{"serverProtocol":"HTTP"}' `
  --lifecycle-configuration '{"idleRuntimeSessionTimeout":300,"maxLifetime":900}' `
  --client-token UUID

# Required for runtimes created after the June 2026 MMDSv2 enforcement.
aws bedrock-agentcore-control update-agent-runtime `
  --agent-runtime-id RUNTIME_ID `
  --metadata-configuration '{"requireMMDSV2":true}'
```

After the agent-count quota was granted, the account still reported a Docker
image-size quota of 0 MB. The deployed Runtime therefore uses the official
Direct Code path: a 30.3 MB Linux ARM64-compatible ZIP in a private Sydney S3
bucket, Python 3.12, `main.py`, HTTP protocol, and the same least-privilege
execution role. Runtime version 1 is `READY` with MMDSv2 required.

`Active Session Workloads per Account` later became effective at 2,500. A real
invocation through the `DEFAULT` endpoint returned HTTP 200 and completed both
the incident graph and separate approval-resume graph with zero policy
violations. The sanitized response, CloudWatch completion evidence, and full
tool trace are preserved in
`evals/reports/agentcore_cloud_invocation_reference.json`.

The accepted request contract is:

```json
{
  "action": "run_incident",
  "approve": true,
  "task": "Optional bounded task text"
}
```

The response exposes the incident and approval-resume execution orders, final
allocation, deterministic safety claims, impact count, and complete tool trace.

## Teardown gate

Before the first deployment, record the exact generated stack names with
`agentcore status --target default`. Use the CLI removal command against only
this project and target after the demo; never delete shared account resources.
