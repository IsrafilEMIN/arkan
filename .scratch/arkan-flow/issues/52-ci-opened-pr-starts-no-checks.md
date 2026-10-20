# 52: A pull request opened by ci starts no checks

**Role:** ready-for-human
**Closed:** no
**Priority:** 61

**What to build:** a pull request that ci opens with `github.token` starts no `check`, `arkan-review` or `arkan-risk` run. That covers the post-merge fix pull request (ticket 21) and any future bot pull request. On the gate path the required checks never report; on the broker path the pull request has no risk marker and stays `manual`.

- [ ] a bot pull request starts the same checks as a person's pull request
- [ ] the path does not need a person to close and reopen the pull request
- [ ] proof: a planted bad merge produces a fix pull request whose `check` and `arkan-risk` runs report on that head

**Blocked by:** None for the choice. the build needs a token the repo owner provisions.

## Comments

- 2026-10-19, filed from ticket 21 review rounds 1 and 2. `ci/README.md` documents the limit and offers `POST_MERGE_TOKEN`, but the default stays broken. A fine-grained token works as a secret; a github app installation token expires after an hour and needs minting in a step. The owner decides which path, because the token is a repo setting.
