# Repository instructions

## Scope

Build the smallest credible system that demonstrates safe autonomy, failure recovery, measurable impact, and a clear five-minute story.

## Engineering rules

1. Read the relevant files before editing.
2. Keep changes inside the requested subsystem.
3. Every mutation tool must accept an `idempotency_key`.
4. Hard constraints live in deterministic policy code, not only in prompts.
5. Every agent must own distinct state, tools, or responsibility. Delete decorative agents.
6. Add or update tests for every behavior change.
7. Run the smallest relevant test first, then the full suite.
8. Record material milestones and failures in `BUILD_LOG.md`.
9. Never commit credentials, private user data, interview recordings, or generated secrets.
10. Preserve raw evaluation reports and random seeds.

## Definition of done

- Behavior is reproducible from a documented command.
- Tests pass.
- Failure behavior is explicit and bounded.
- Logs explain decisions without exposing secrets.
- The change strengthens a named judging dimension.

