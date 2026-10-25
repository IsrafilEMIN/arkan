# 59: arkan-review and arkan-risk run the base branch's workflow

**Role:** ready-for-agent
**Closed:** no
**Priority:** 68
**Blocked by:** None (can start immediately).

**What to build:** a `pull_request` run uses the workflow file from the pr branch. a pr that edits `.github/workflows/arkan-risk.yml` can write its own `<!-- arkan:risk head=<sha> label=auto -->` marker, and a pr that edits `arkan-review.yml` can pass its own check, when the push token may edit workflows (full review, finding A5). `pull_request_target` runs the base branch's copy. that trigger holds secrets and a write token, so no pr file may sit on disk in the job.

- [ ] `arkan-risk` triggers on `pull_request_target` (opened, synchronize, reopened). it already checks out only the base sha with `persist-credentials: false`
- [ ] `arkan-review` triggers on `pull_request_target` in place of `pull_request`. its "Check out the pr head" step (`arkan-review.yml:75-80`) becomes a base-sha checkout, then `git fetch --no-tags origin <head-sha>` (and `refs/pull/<n>/head`, so a fork head resolves). every later step reads git objects only
- [ ] `actions/checkout` in `arkan-review.yml` is pinned to a commit sha, as in `arkan-risk.yml` and `check.yml`
- [ ] the docs-only skip in `arkan-review.yml` and `_changed_files` in `ci/opencode_agent.py` list both sides of a rename (`--no-renames`), so a code file renamed into `docs/` is reviewed
- [ ] `pull_request_review_comment` has no `_target` form and keeps running the pr's copy: `ci/README.md` says so, and that run only applies `arkan:` commands from writers
- [ ] the installed copies in `.github/workflows/` equal the templates in `ci/github/`
- [ ] `ci/README.md` describes the new triggers and why
- [ ] `bash scripts/check.sh` prints `check: ok`; a live pr on arkan shows `arkan-risk` and `arkan-review` running from the base copy

## Comments

- 2026-10-21, owner: agreed, with the correction that `arkan-review` must stop checking out the pr head first.
