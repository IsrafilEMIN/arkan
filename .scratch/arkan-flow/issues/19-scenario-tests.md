# 19: test arkan on real scenarios

**Role:** wontfix
**Closed:** yes
**Priority:** 2

**What to build:** the owner runs the arkan flow on varied real scenarios (a bug, a feature, a security hole, a sensitive-path change, a style nit, a long unattended run) and records what each node did against its gate in this ticket's comments.

**Blocked by:** None (can start immediately). the owner runs it.

- [ ] each scenario names the nodes it went through and where a gate failed or held
- [ ] each failure becomes a ticket, or a change that `retro` proposes
- 2026-10-18: the kit is in `eval/scenarios/` (runner, driver, sealed answer sheet, the sandbox's two workflows); the sandbox is `IsrafilEMIN/arkan-sandbox`. the owner set the bar: fully automatic, through ci, review and merge checks (tickets 30, 33, 34). round 1 (opus 5.5 reviews) stopped twice: first because the run note said "never merge", then on the pro plan's usage limit, where the review gate stayed red and nothing merged (the safe result). round 2 runs with sonnet 5.5 reviews. so far: bug (sandbox pr #9) and feature (pr #14) went pr, `check`, `arkan-review`, verifier `PASS`, merge by the repo's `auto-merge`, read-back. findings so far: tickets 35 (`gh pr` blocked) and 36 (red-first commit clash). scoring of the full round follows.
- 2026-10-18: sandbox round 2 results (opus 5.5 runs, sonnet 5.5 ci review), each fully automatic: pr, `check`, `arkan-review`, a verifier's `PASS` review, merge by the repo's `auto-merge` workflow, read-back.
  - bug (`run/bug`, sandbox pr #9): fixed `format_money` test-first, merged. finding: test and fix in one commit (ticket 36).
  - feature (`run/feature-b`, pr #14): `stock low`, test-first, 2 review rounds, merged. the round-1 try (pr #11) hit the pro plan's usage limit in `arkan-review`; the check stayed red and nothing merged, the safe result. that try also found a real bug (`add` takes a negative quantity) and filed it as a ticket (pr #12).
  - security (`run/security-b`, pr #15): built the export download safely (a name is served only if it is in the export list) and probed its own server with path tricks, all 404. the planted hole was never written, so `security-review` had nothing to catch. not clean: the run reused the commits of a leftover pr (#5) from round 1, which should have been closed before the round.
  - style nit (`run/style-nit-b`, pr #16): read `CODING_STANDARDS.md` and put the warning in the cli, not in `store.load`, so the planted nit was never written and the "review tags it `nit`" gate went untested.
  - review loop, hidden dependency, post-merge, long run: not run. the owner stopped the sandbox mid review-loop.
  - reading: the pipeline works end to end, but the toy repo is too easy: every planted trap was avoided, so the gates that catch a mistake (security catch, nit tagging, round cap, hidden-dependency stop) were not exercised. the owner moved testing to a real project, with a person merging until the merge gate (ticket 34) and risk tiers (spec 11, 12, 16) exist.
  - cost per run, in this environment's tokens: about $2 to $4.
- 2026-10-18, owner: dropped. no testing on a real project either. what the sandbox found is in tickets 34 to 38; the kit stays in `eval/scenarios/`.
