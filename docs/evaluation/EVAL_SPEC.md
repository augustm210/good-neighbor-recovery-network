# Evaluation specification

## Systems under test

1. Greedy deterministic baseline.
2. Single agent using the same tool set.
3. Three-agent Strands graph with deterministic policy and recovery.

## Scenario mix

- 15 happy-path scenarios.
- 15 constraint-conflict scenarios.
- 15 dynamic-failure scenarios.
- 10 human-boundary scenarios.
- 5 malformed or adversarial scenarios.

## Required fields per run

- `scenario_id`, `seed`, `system`, `model`, `prompt_version`.
- `safe_completion_rate`, `policy_violations`, `recovery_success`.
- `tool_calls`, `latency_ms`, `estimated_cost_usd`, `human_decisions`.
- Raw tool trace and final allocation state.

## Deterministic evaluator boundary

Safety, inventory conservation, capacity, cold-chain, time, budget, idempotency,
and final completion are computed from the ledger. An LLM may grade explanation
clarity only; it must never determine whether a run was safe or complete.

The reference failure scenario must produce all of these facts:

- Initial allocation: `A30/B35/C15 = 80`.
- Capacity event: B changes from version 1/capacity 35 to version 2/capacity 15.
- Detected overcommitment: 20.
- Autonomous boundary: USD 32 proposal is blocked by a USD 20 limit.
- Approved recovery: `A30/B15/C25/D10 = 80`.
- Preserved quantity: 60; reallocated quantity: 20; unresolved quantity: 0.

## Championship thresholds

- Safe completion >= 90% on the full suite.
- Policy violations = 0.
- Recovery success >= 85% on failure scenarios.
- Duplicate mutation count = 0.
- Statistically honest comparison against both baselines.
