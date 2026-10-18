# 38: ship a ci test job a repo can copy

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 7

**What to build:** arkan ships a plain ci workflow, `ci/github/check.yml`, that runs the repo's own check command (its tests, lint and build, the same command the task loop's prove step runs) on each push and each pr, as a job named `check`. the merge gate (ticket 34) and the branch rules require it by that name. the repo's check command is one line at the top of the file, so a repo without `scripts/check.sh` points it at its own command.

**Blocked by:** None (can start immediately). `pre-setup` offering it to a repo is section h of ticket 05's brainstorm, which waits on ticket 05.

**Touches:** `ci/`, `README.md`.

- [x] `ci/github/check.yml` runs the check command on `push` to the default branch and on `pull_request`, as job `check`
- [x] the check command is one `env:` line, with `bash scripts/check.sh` as the default
- [x] `ci/README.md` says how to add it and that `check` and `arkan-review` are the two required checks
- [x] proof: in `IsrafilEMIN/arkan-sandbox`, a pr that breaks a test gets a red `check`, and its fix turns it green

## Comments

- 2026-10-18, owner: file it on its own, so it is not lost if ticket 05's design changes. the sandbox's copy is `eval/scenarios/sandbox/check.yml`; it has run on every sandbox pr since ticket 33.
- 2026-10-18, agent: built `ci/github/check.yml`: job `check`, on `push` to `main` and on `pull_request`, one setting (`CHECK_COMMAND: bash scripts/check.sh`), `contents: read`, a 15-minute timeout, `actions/checkout` pinned to `3d3c42e` (v7.0.1, read from the action repo's tags), no language setup and a commented python and node example. `ci/README.md` has a new `## check` section; `README.md` points to it under "review in ci". proof in the sandbox, on base `ci-r38-base` (made from `pre-break`, with this file as its `check.yml` and its `auto-merge.yml` and `arkan-review.yml` removed): pr [#17](https://github.com/IsrafilEMIN/arkan-sandbox/pull/17) broke one test in `tests/test_money.py` and got a red `check` ([check run 117820715327](https://github.com/IsrafilEMIN/arkan-sandbox/actions/runs/39176691256/job/117820715327), failed in the step that runs the check command); the fix turned it green ([check run 117820816415](https://github.com/IsrafilEMIN/arkan-sandbox/actions/runs/39176726403/job/117820816415)). the pr was closed unmerged. the sandbox branches `ci-r38-base` and `ci-r38-proof` are left for the owner to delete.
