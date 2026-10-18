# 35: pr steps work when `gh pr` is blocked

**Role:** ready-for-agent
**Closed:** no
**Priority:** 8

**What to build:** the pr playbooks (`opening-a-pr`, `babysit`, `shipping`) and `post-merge` name `gh pr create/view/checks/merge`, which use github's graphql api. in a container whose proxy blocks graphql (this cloud environment does), every one of them fails, and a run only gets through because it is told the rest endpoints. each playbook names the rest fallback once, in one place the others point to: create a pr (`POST repos/<o>/<r>/pulls`), read it (`GET .../pulls/<n>`), read checks (`GET .../commits/<sha>/check-runs`), comment (`POST .../issues/<n>/comments`), post a verdict (`POST .../pulls/<n>/reviews`), merge where the agent may (`PUT .../pulls/<n>/merge`).

**Blocked by:** None (can start immediately).

**Touches:** `skills/arkan-mode/playbooks/`, `skills/post-merge/`.

- [ ] one forge note lists the rest fallback for each `gh pr` call the playbooks use, and says to try `gh pr` first
- [ ] `opening-a-pr`, `babysit`, `shipping` and `post-merge` point to it instead of repeating it
- [ ] proof: a scenario run with no environment note about graphql still opens its pr and reads its checks

## Comments

- 2026-10-18: found in ticket 19's sandbox runs. `gh pr create`, `view`, `list`, `checks` and `merge` fail with http 403 through the proxy; `gh api` rest works.
