# 38: ship a ci test job a repo can copy

**Role:** ready-for-agent
**Closed:** no
**Priority:** 7

**What to build:** arkan ships a plain ci workflow, `ci/github/check.yml`, that runs the repo's own check command (its tests, lint and build, the same command the task loop's prove step runs) on each push and each pr, as a job named `check`. the merge gate (ticket 34) and the branch rules require it by that name. the repo's check command is one line at the top of the file, so a repo without `scripts/check.sh` points it at its own command.

**Blocked by:** None (can start immediately). `pre-setup` offering it to a repo is section h of ticket 05's brainstorm, which waits on ticket 05.

**Touches:** `ci/`, `README.md`.

- [ ] `ci/github/check.yml` runs the check command on `push` to the default branch and on `pull_request`, as job `check`
- [ ] the check command is one `env:` line, with `bash scripts/check.sh` as the default
- [ ] `ci/README.md` says how to add it and that `check` and `arkan-review` are the two required checks
- [ ] proof: in `IsrafilEMIN/arkan-sandbox`, a pr that breaks a test gets a red `check`, and its fix turns it green

## Comments

- 2026-10-18, owner: file it on its own, so it is not lost if ticket 05's design changes. the sandbox's copy is `eval/scenarios/sandbox/check.yml`; it has run on every sandbox pr since ticket 33.
