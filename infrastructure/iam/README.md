# AWS development identity

Use a dedicated human development identity for the hackathon. Do not deploy as
the root user and do not create a long-lived access key.

## Identity

- IAM user: `agents-for-humans-dev`
- Console access: enabled, with password reset required on first sign-in
- MFA: required before cloud deployment
- Region: `ap-southeast-2` (Sydney)
- Local profile: `agents-for-humans-dev`
- Tags: `Project=agents-for-humans`, `Purpose=HackathonDevelopment`

## Attached policies

1. AWS managed `SignInLocalDevelopmentAccess` for temporary `aws login`
   credentials.
2. AWS managed `BedrockAgentCoreFullAccess` for AgentCore development.
3. Customer managed `AgentsForHumansAgentCoreCliDev`, created from
   `agentcore-cli-development-policy.json`, for the AgentCore CLI build and
   deployment resources.

The customer policy is based on the AWS AgentCore CLI development policy. It
narrows regional resources to Sydney, keeps the AWS-required
`bedrock-agentcore-*` naming boundaries, and explicitly denies unused user-ID
delegation APIs. The AWS managed AgentCore policy is intentionally broad and is
acceptable only for this isolated development account during the hackathon.

## Verification gate

Run these commands after the user completes the first console sign-in, changes
the temporary password, and enables MFA:

```powershell
aws login --profile agents-for-humans-dev
aws sts get-caller-identity --profile agents-for-humans-dev
aws configure set region ap-southeast-2 --profile agents-for-humans-dev
```

Do not continue if the caller ARN is `root`. Do not print or commit account IDs,
cached login tokens, passwords, or other credentials.

## Teardown

After the hackathon, remove the user policy attachments, delete the customer
managed policy, delete the IAM user, and remove the local login session with:

```powershell
aws logout --profile agents-for-humans-dev
```

Cloud resources receive a separate inventory and destroy command before the
first deployment.
