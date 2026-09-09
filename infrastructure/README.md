# Infrastructure

Reserved for the minimum viable AWS deployment after the local graph passes the evaluation gates.

Before provisioning:

1. Confirm AWS Builder ID separately from AWS account credentials.
2. Enable MFA and billing alerts.
3. Install AWS CLI v2 and use a non-root development identity.
4. Keep secrets outside source control.
5. Document destroy / teardown commands and expected daily cost.

## Local prerequisites

- AWS CLI v2: installed and version-verified.
- Node.js 24 LTS: installed for the AgentCore CLI/CDK toolchain.
- AgentCore CLI 0.27.0: installed and version-verified.
- AWS CDK 2.1136.0: installed and version-verified.
- Strands Agents 1.52: installed in the repository `.venv`.
- AWS Builder Center: browser login verified separately from AWS account credentials.

Cloud provisioning remains intentionally blocked until `aws sts
get-caller-identity` succeeds for a non-root development identity and the target
region/model access are recorded. Browser Builder ID login alone is not AWS API
authorization.

Current read-only probe: `aws sts get-caller-identity` returns `NoCredentials`.
Do not solve this with long-lived access keys or by deploying as root. Use an
approved non-root console/IAM Identity Center identity with temporary
credentials and record the target account and region before bootstrap.

The reviewed hackathon identity and permission plan is documented in
[`iam/README.md`](iam/README.md). The checked-in JSON contains no account ID or
credentials and can be audited before it is created in IAM.
