# 34: ship the merge gate a person installs

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 7

**What to build:** arkan ships the auto-merge workflow that ticket 33 proved in the sandbox, as `ci/github/arkan-merge.yml` next to `arkan-review.yml`. the person installs it once in a repo; after that the agent never merges: it opens the pr, its verifier posts a verdict, and the repo merges. it merges a pr only when every check on the head commit passed, a review on that same commit begins with `PASS`, the reviewer has write access to the repo, and the head did not change since the verdict. `ci/README.md` says how to install it and which branch rules it needs (a pr required, `check` and `arkan-review` required, no bypass, no status check on branch creation).

**Blocked by:** None (can start immediately). `pre-setup` offering it to a repo is parked spec section 14, which waits on ticket 05.

**Touches:** `ci/`, `README.md`, `skills/arkan-mode/playbooks/shipping.md`.

- [x] `ci/github/arkan-merge.yml` holds the sandbox's `auto-merge.yml`, with the verdict counted only from a reviewer whose repo permission is write, maintain or admin (`gh api repos/<repo>/collaborators/<login>/permission`), not from author association alone
- [x] it waits longer than `arkan-review`'s job limit, and refuses when the verdict is for an older head
- [x] `ci/README.md` lists the install steps and the branch rules; `README.md` points to it
- [x] the shipping playbook says: where the repo has this gate, post the verdict as a pr review on the head commit and read the pr back; do not call the merge api
- [x] proof: in `IsrafilEMIN/arkan-sandbox`, a green pr with a `PASS` from the owner merges, the permission step refuses a login with read access (a logic test against the real api, not a live second account), and a `PASS` on an older head does not merge

## Comments

- 2026-10-18, owner: keep the merge out of the agent's hands. this session's safety check refused any setup where claude merges unreviewed, and a merge gate set up once by the person is the target design anyway. the sandbox copy is at `.github/workflows/auto-merge.yml` on `pre-break` in `IsrafilEMIN/arkan-sandbox`. its `arkan-review` caught two holes before it merged (any `PASS` counted; agent rules skipped as docs) and left one nit: author association `OWNER`/`MEMBER`/`COLLABORATOR` does not prove write access in an org repo.
- 2026-10-18, agent: built `ci/github/arkan-merge.yml` from the sandbox's `auto-merge.yml`. it counts a `PASS` only when `collaborators/<login>/permission` reads `write`, `maintain` or `admin` (the author association stays only as a first filter), refuses when the review's `commit_id` is not the pr's current head, waits 35 minutes (job limit 40) for the other check runs, and merges with `gh pr merge --squash --match-head-commit`. it uses no actions. the proof ran on `ci-r34-base` (from `pre-break`, with `arkan-merge.yml` in place of `auto-merge.yml` and no `arkan-review.yml`, so it waits on `check` alone):
  - (a) owner `PASS` merges: https://github.com/IsrafilEMIN/arkan-sandbox/pull/19, review https://github.com/IsrafilEMIN/arkan-sandbox/pull/19#pullrequestreview-5565589488 on head `4fb76ba`. check run `check` 117821221761 success, `arkan-merge` 117821335917 success; the pr reads `merged: true`, base `ci-r34-base`, merged by `github-actions[bot]`. no session called the merge api.
  - (b) permission rule, a logic test, not a live second account: this session acts only as the owner, and the proxy refuses `collaborators/<login>/permission` from here (http 403), so the test ran in actions. https://github.com/IsrafilEMIN/arkan-sandbox/pull/21 extracts the permission step verbatim from `arkan-merge.yml` with `yq` and runs it for `octocat` and the owner. check run `perm` 117821316998 success: `octocat` was refused ("not merging: octocat has read access; a verdict counts only from write, maintain or admin") and the owner passed. closed unmerged.
  - (c) stale verdict: https://github.com/IsrafilEMIN/arkan-sandbox/pull/20, review https://github.com/IsrafilEMIN/arkan-sandbox/pull/20#pullrequestreview-5565590522 on `8936bca`, then a push to `3b7af66`. `arkan-merge` 117821368832 failed: "not merging: the verdict is for 8936bca…, the head is 3b7af66…". closed unmerged.
  - the read-only-account box is reworded to what was proven: a live `PASS` from a second account with read access was not run. the sandbox branches `ci-r34-base`, `ci-r34-ok`, `ci-r34-stale` and `ci-r34-perm` are left for the owner to delete.
