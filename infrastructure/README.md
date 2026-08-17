# Infrastructure

Reserved for the minimum viable AWS deployment after the local graph passes the evaluation gates.

Before provisioning:

1. Confirm AWS Builder ID separately from AWS account credentials.
2. Enable MFA and billing alerts.
3. Install AWS CLI v2 and use a non-root development identity.
4. Keep secrets outside source control.
5. Document destroy / teardown commands and expected daily cost.

