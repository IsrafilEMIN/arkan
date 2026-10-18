# 34: ship the merge gate a person installs

**Role:** ready-for-agent
**Closed:** no
**Priority:** 7

**What to build:** arkan ships the auto-merge workflow that ticket 33 proved in the sandbox, as `ci/github/arkan-merge.yml` next to `arkan-review.yml`. the person installs it once in a repo; after that the agent never merges: it opens the pr, its verifier posts a verdict, and the repo merges. it merges a pr only when every check on the head commit passed, a review on that same commit begins with `PASS`, the reviewer has write access to the repo, and the head did not change since the verdict. `ci/README.md` says how to install it and which branch rules it needs (a pr required, `check` and `arkan-review` required, no bypass, no status check on branch creation).

**Blocked by:** None (can start immediately). `pre-setup` offering it to a repo is parked spec section 14, which waits on ticket 05.

**Touches:** `ci/`, `README.md`, `skills/arkan-mode/playbooks/shipping.md`.

- [ ] `ci/github/arkan-merge.yml` holds the sandbox's `auto-merge.yml`, with the verdict counted only from a reviewer whose repo permission is write, maintain or admin (`gh api repos/<repo>/collaborators/<login>/permission`), not from author association alone
- [ ] it waits longer than `arkan-review`'s job limit, and refuses when the verdict is for an older head
- [ ] `ci/README.md` lists the install steps and the branch rules; `README.md` points to it
- [ ] the shipping playbook says: where the repo has this gate, post the verdict as a pr review on the head commit and read the pr back; do not call the merge api
- [ ] proof: in `IsrafilEMIN/arkan-sandbox`, a green pr with a `PASS` from a read-only account does not merge, and one from the owner does

## Comments

- 2026-10-18, owner: keep the merge out of the agent's hands. this session's safety check refused any setup where claude merges unreviewed, and a merge gate set up once by the person is the target design anyway. the sandbox copy is at `.github/workflows/auto-merge.yml` on `pre-break` in `IsrafilEMIN/arkan-sandbox`. its `arkan-review` caught two holes before it merged (any `PASS` counted; agent rules skipped as docs) and left one nit: author association `OWNER`/`MEMBER`/`COLLABORATOR` does not prove write access in an org repo.
