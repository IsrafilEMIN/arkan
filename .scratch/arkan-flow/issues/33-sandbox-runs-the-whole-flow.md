# 33: the sandbox runs the whole flow by itself

**Role:** ready-for-agent
**Closed:** no
**Priority:** 4

**What to build:** `IsrafilEMIN/arkan-sandbox` lets ticket 19's scenario runs go all the way with no person: pr, ci, review, a verifier, merge, and a read-back that the merge landed. it has a `check` ci job that runs `scripts/check.sh`; each run gets its own base branch, so one run's merges never touch another's; `main` and the run base branches require `check` (and `arkan-review` once ticket 30 is in) before a merge; and the runs are told the environment facts they need: merge through the rest api, because the proxy blocks the graphql api behind `gh pr merge`.

**Blocked by:** None (can start immediately). the full run with review needs 30.

**Touches:** the sandbox repo and the run scripts in the session scratchpad; nothing in arkan.

- [ ] a pr in the sandbox runs `check`, and a red `check` blocks its merge
- [ ] each run's pr targets its own base branch, with the same required checks
- [ ] a run merges its own pr through the rest api once the checks pass and the verifier says pass, then reads the pr back as merged
- [ ] proof: one scenario run ends with its pr merged and the read-back recorded

## Comments

- 2026-10-18, owner: the scenario runs must be fully automatic, through ci and the merge checks. the first runs stopped at an open pr because the run note said "never merge"; that note was wrong and is replaced. the sandbox is public, so branch protection works.
