# 21: what starts post-merge

**Role:** ready-for-agent
**Closed:** no
**Priority:** 16

**What to build:** `post-merge` (ticket 08) starts by itself, so no person has to start it after a bad merge.

**Blocked by:** 08, 05 (pre-setup decides how it offers the jobs)

what can start it (proposal: a and b together):

- a. **event:** a ci job on main. when main's ci fails, or a revert lands, it starts an agent headless (for example claude code in github actions) with the post-merge skill. fast and cheap: it runs only when something broke.
- b. **schedule:** a daily job for slow signals (error logs, incident issues). on github actions this is a `schedule` trigger; claude code on the web can also run scheduled tasks.
- c. in-session `/loop` only while a person keeps a session open. good for a test, not a base.

pushing ci files and changing repo settings are outward actions: show the exact change and ask first.

- [x] `pre-setup` offers the ci job (a) and the scheduled job (b) per repo
- [ ] proof: a planted bad merge in a test repo gets a revert or fix pr and a ticket for the miss, with no person in the loop

## Comments

- 2026-10-19, agent: built the triggers and the pre-setup offers. `ci/github/arkan-post-merge.yml` runs on a `workflow_run` of `check` on main: a `failure` conclusion, or a head commit that starts `Revert` or contains `This reverts commit`. `ci/github/arkan-post-merge-daily.yml` runs on `schedule` (06:17 utc) and `workflow_dispatch`, and calls no model when the slow-signal step finds nothing. both use `anthropics/claude-code-action` with the `CLAUDE_CODE_OAUTH_TOKEN` secret from `arkan-review`, and read `.claude/skills/post-merge/SKILL.md` (its new `## In ci` section). the model returns structured output and a shell step, not the model, pushes `post-merge/<bad merge short>`, opens the `post-merge:` pull request, and publishes the ticket: an issue for a github tracker, a committed ticket file for a local one, and a ticket-only pull request when a revert already landed. the no-loop rule: a revert whose message contains `post-merge` starts nothing, and every fix or revert commit and pull request title carries `post-merge`, so its own landed pull request cannot start it again; a `failure` conclusion always runs. `setup.sh` has `ci-post-merge` and `ci-post-merge-daily`; `pre-setup` offers them under the `ci-review` secret and skills condition, and still asks before the push. `ci/README.md`, `README.md`, and `skills/post-merge/SKILL.md` are updated.
- 2026-10-19, agent: proof for box 1. in a fresh scratch repo with no `.github/`:
  - `setup.sh check` -> `ci-post-merge missing .github/workflows/arkan-post-merge.yml` and `ci-post-merge-daily missing .github/workflows/arkan-post-merge-daily.yml`.
  - `apply ci-post-merge` -> `ok`; `apply ci-post-merge-daily` -> `ok`; `check` -> both `ok`; `cmp` says both copies are identical to arkan's files.
  - a second apply leaves the files byte-identical (`d1283418016ec75a9528f35d65781e61d6b1b4e3` over both files).
  - after appending one line to the daily copy: `ci-post-merge ok`, `ci-post-merge-daily out-of-date .github/workflows/arkan-post-merge-daily.yml differs from <arkan>/ci/github/arkan-post-merge-daily.yml`.
  - `ruby -ryaml` parses both workflow files, and every embedded `run:` block passes `bash -n`.
  - the event publish step, run with a stub `gh` against a local bare origin, pushed the code branch, opened the pull request, committed and pushed the ticket (`docs: ticket the post-merge miss`), and patched the pull request body where `{{ticket}}` was. a github-tracker case created the issue with `needs-triage` and patched the body too. a revert case with no code pull request opened the ticket-only `post-merge/ticket-<run id>` pull request. two bugs found and fixed this way: the pull request body patch lost its `{{ticket}}` placeholder, and the daily run read failures from every workflow instead of only `check`.
- 2026-10-19, agent: box 2 stays open. a live run needs a model secret in the test repo's ci, and this sandbox cannot add secrets or change repo settings. the local clone of `IsrafilEMIN/srt-flow-throwaway` has one workflow, `.github/workflows/ci.yml` (checkout and `sh check.sh`), with no model step, and its `check.sh` is `exit 0`, so it has no check that can fail. it also has no `docs/agents/issue-tracker.md`. missing to run it: a `CLAUDE_CODE_OAUTH_TOKEN` (or `ANTHROPIC_API_KEY`) actions secret on that repo, arkan's `.claude/skills/` with `post-merge`, the two workflow files on its default branch with `CHECK_COMMAND` pointing at a real check, a tracker doc, then a planted bad merge on the default branch (nothing pushed to its default branch from here). `gh secret list` cannot run here (no gh login), so whether a secret already exists is unread.
