# 45: incidents become review evals

**Role:** ready-for-agent
**Closed:** no
**Priority:** 30

**What to build:** every merged change that broke main becomes a test case for the ci reviewer, so a change to the reviewer (its prompt, tools or model) is kept only if it still catches the old misses. from the claude code team's review post: "any incidents are now an eval"; this was parked in `.scratch/review-ci/spec.md` and noted in ticket 08.

**Blocked by:** None (can start immediately). it has no reviewer to score until `arkan-review` runs in a repo (ticket 42's runner decision).

- [ ] `post-merge` (ticket 08) saves each confirmed miss as one eval case: the bad diff, the bug, where it lived, and the fix pr
- [ ] the cases live in one folder per repo, in a format a script and an agent can both read
- [ ] a script runs the reviewer against every case and prints, per case, caught or missed
- [ ] a change to `arkan-review` or the `code-review` / `security-review` skills is kept only when it misses no case it caught before
- [ ] proof: one planted past bug is saved as a case, the script reports it caught, and a weakened reviewer prompt reports it missed

## Comments

- 2026-10-19, owner: capture this so it is actually built, not left parked.
