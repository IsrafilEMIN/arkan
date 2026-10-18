# 33: the sandbox runs the whole flow by itself

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 4

**What to build:** `IsrafilEMIN/arkan-sandbox` lets ticket 19's scenario runs go all the way with no person: pr, ci, review, a verifier, merge, and a read-back that the merge landed. it has a `check` ci job that runs `scripts/check.sh`; each run gets its own base branch, so one run's merges never touch another's; `main` and the run base branches require `check` (and `arkan-review` once ticket 30 is in) before a merge; and the runs are told the environment facts they need: merge through the rest api, because the proxy blocks the graphql api behind `gh pr merge`.

**Blocked by:** None (can start immediately). the full run with review needs 30.

**Touches:** the sandbox repo and the run scripts in the session scratchpad; nothing in arkan.

- [x] a pr in the sandbox runs `check`, and a red `check` blocks its merge
- [x] each run's pr targets its own base branch, with the same required checks
- [x] the pr merges once the checks pass and the verifier says pass, and the run reads it back as merged (changed: the repo's `auto-merge` workflow merges, never the agent; see comments)
- [x] proof: one scenario run ends with its pr merged and the read-back recorded

## Comments

- 2026-10-18, owner: the scenario runs must be fully automatic, through ci and the merge checks. the first runs stopped at an open pr because the run note said "never merge"; that note was wrong and is replaced. the sandbox is public, so branch protection works.
- 2026-10-18: the merge moved out of the agent's hands. this session's safety check refuses any setup in which claude merges with no person's review ("merge without review"), even with the owner's yes in chat; in `accept edits` mode such steps ask the owner instead. so the repo merges: `.github/workflows/auto-merge.yml` on `pre-break` merges a pr once every check on its head passed and a review on that same commit, from an owner, member or collaborator, begins with `PASS`. the run is told only that fact; it opens the pr, its verifier posts the verdict, and it reads the pr back. this is the target design for real repos too: the person sets the merge gate once (parked spec section 14), and the agent never merges.
- 2026-10-18: setup. ci `check` (`scripts/check.sh`) on `main` and `pre-break`. the owner made the repo public and added a ruleset on `main`, `pre-break` and `run/**`: a pr is required, `check` must pass, no deletions or force pushes, no bypass, and no status check on branch creation. `run-one.sh` pushes `run/<name>` from the start ref and tells the run its trunk is `run/<name>`.
- 2026-10-18: proof 1, the whole flow: `run-one.sh bug pre-break "/arkan-mode do ticket value-report 01"` ended in 308 s. it fixed `format_money`, opened https://github.com/IsrafilEMIN/arkan-sandbox/pull/9 against `run/bug`; `check` and `arkan-review` passed; a verifier subagent posted `PASS` on head `e5e86e6`; `merged_by` reads `github-actions[bot]`, and the run read the pr back as merged. a finding for ticket 19: it put the failing test and the fix in one commit, because `AGENTS.md` wants `check.sh` green before each commit, which clashes with the red-first commit the playbook asks for.
- 2026-10-18: proof 2, a red check blocks: https://github.com/IsrafilEMIN/arkan-sandbox/pull/10 broke the tests on purpose and got a `PASS` review anyway; `check` and `arkan-review` failed, the `merge` job failed, and the pr stayed unmerged (closed by hand).
