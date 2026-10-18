# 35: pr steps work when `gh pr` is blocked

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 8

**What to build:** the pr playbooks (`opening-a-pr`, `babysit`, `shipping`) and `post-merge` name `gh pr create/view/checks/merge`, which use github's graphql api. in a container whose proxy blocks graphql (this cloud environment does), every one of them fails, and a run only gets through because it is told the rest endpoints. each playbook names the rest fallback once, in one place the others point to: create a pr (`POST repos/<o>/<r>/pulls`), read it (`GET .../pulls/<n>`), read checks (`GET .../commits/<sha>/check-runs`), comment (`POST .../issues/<n>/comments`), post a verdict (`POST .../pulls/<n>/reviews`), merge where the agent may (`PUT .../pulls/<n>/merge`).

**Blocked by:** None (can start immediately).

**Touches:** `skills/arkan-mode/playbooks/`, `skills/post-merge/`.

- [x] one forge note lists the rest fallback for each `gh pr` call the playbooks use, and says to try `gh pr` first
- [x] `opening-a-pr`, `babysit`, `shipping` and `post-merge` point to it instead of repeating it
- [x] proof: `gh pr view` fails here with the graphql block, and each read-only rest call in the note returns the fields the note names on a closed sandbox pr

## Comments

- 2026-10-18: found in ticket 19's sandbox runs. `gh pr create`, `view`, `list`, `checks` and `merge` fail with http 403 through the proxy; `gh api` rest works.
- 2026-10-18: changed the proof box. it asked for a scenario run, and the owner dropped scenario testing (ticket 19, wontfix), so the proof is read-only calls against closed prs in `IsrafilEMIN/arkan-sandbox`. nothing was created, commented, reviewed, edited or merged there.
- 2026-10-18: done. the note is **Forge without GraphQL** in `skills/arkan-mode/playbooks/opening-a-pr.md`, after **Forge**. `babysit.md` step 1 and `shipping.md` step 1 add "and its **Forge without GraphQL** calls when `gh pr` is blocked" to their forge pointer; `post-merge` step 3 points to its view call. the playbooks decide the same things; only the calls change. proof, with gh 2.89.0:
  - `gh pr view 9 --repo IsrafilEMIN/arkan-sandbox` and `gh pr checks 9`: exit 1, `HTTP 403: GitHub GraphQL is not available from Claude Code sessions; use the REST API (gh api repos/{owner}/{repo}/...).` the message also names proxy routes for review threads, auto-merge and draft/ready (`.../pulls/{n}/ccr/...`).
  - view, `GET .../pulls/9`: `state` closed, `merged` true, `merged_at` 2026-10-18T21:09:11Z, `mergeable` null, `mergeable_state` unknown, `base.ref` run/bug, `head.sha` e5e86e6e. pr 14: the same shape, base run/feature-b.
  - checks, `GET .../commits/<head>/check-runs`: `total_count` 3, `merge`, `arkan-review`, `check`, each completed with success (prs 9 and 14).
  - status, `GET .../commits/<head>/status`: `state` pending with `total_count` 0. the repo uses check runs only, so an empty status reads pending; the note says so.
  - reviews, `GET .../pulls/9/reviews`: two `COMMENTED` reviews (github-actions[bot], IsrafilEMIN), each with `commit_id` the head sha. pr 14: the same.
  - watch: `gh run list --commit <head>` lists the runs over rest; `gh run watch 39174189745 --exit-status` exits 0 on a finished run.
  - not proved here, because they write: create, comment, review, edit base and merge. their endpoints and fields are github's documented rest ones.
