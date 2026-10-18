# 19: test arkan on real scenarios

**Role:** ready-for-human
**Closed:** no
**Priority:** 2

**What to build:** the owner runs the arkan flow on varied real scenarios (a bug, a feature, a security hole, a sensitive-path change, a style nit, a long unattended run) and records what each node did against its gate in this ticket's comments.

**Blocked by:** None (can start immediately). the owner runs it.

- [ ] each scenario names the nodes it went through and where a gate failed or held
- [ ] each failure becomes a ticket, or a change that `retro` proposes
- 2026-10-18: the kit is in `eval/scenarios/` (runner, driver, sealed answer sheet, the sandbox's two workflows); the sandbox is `IsrafilEMIN/arkan-sandbox`. the owner set the bar: fully automatic, through ci, review and merge checks (tickets 30, 33, 34). round 1 (opus 5.5 reviews) stopped twice: first because the run note said "never merge", then on the pro plan's usage limit, where the review gate stayed red and nothing merged (the safe result). round 2 runs with sonnet 5.5 reviews. so far: bug (sandbox pr #9) and feature (pr #14) went pr, `check`, `arkan-review`, verifier `PASS`, merge by the repo's `auto-merge`, read-back. findings so far: tickets 35 (`gh pr` blocked) and 36 (red-first commit clash). scoring of the full round follows.
