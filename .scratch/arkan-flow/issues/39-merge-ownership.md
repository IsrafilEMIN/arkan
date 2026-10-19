# 39: merge ownership: the repo gate merges; the broker keeps push, pr, verdict, cleanup

**Role:** ready-for-agent
**Closed:** no
**Priority:** 5

**What to build:** write the owner's merge-ownership decision (2026-10-18) into the skills and the ci docs. agent work on this machine runs under srt behind a local broker. the checkpoint, push, pr, review and cleanup rules live in `~/.agents/AGENTS.md`. the split:

- push, pull-request creation, verdict posting and worktree cleanup go through the broker clients only (`agent-gh`, `agent-worktree-remove`); never bare `gh`.
- merging belongs to the repo's own merge gate (`ci/github/arkan-merge.yml` plus required status checks) where it is installed and enforceable.
- fallback only where no gate can bind (for example a private repo on the free plan, where a ruleset returns 403): the broker, `agent-merge <pr> <sha>`.
- no session ever calls `gh pr merge` or any other merge api.

work:

1. `skills/arkan-mode/playbooks/shipping.md`: rewrite steps 4 and 5 to the gate/broker/person rule, and remove `gh pr merge` and `gh pr checks --watch`. step 5's wait uses the broker's `agent-gh pr-checks <repo> <pr>` where the broker exists, else the repo's own tool.
2. grep the repo for other `gh pr merge` or merge-api instructions and align or delete them. `eval/scenarios/**` stays as it is (the fixture).
3. `ci/README.md`: add the plan gate — required status checks need github pro on a private repo, or a public repo; on the free plan the gate cannot bind.
4. record the follow-ups: `arkan-flow` 34 (ship `ci/github/arkan-merge.yml`) and the parked pre-setup host-settings section (`.scratch/review-ci/spec.md` section 14), which owns teaching a repo how to install the gate.

**Blocked by:** None (can start immediately).

**Touches:** `skills/arkan-mode/playbooks/shipping.md`, `skills/arkan-mode/playbooks/opening-a-pr.md`, `ci/README.md`, `.scratch/`.

- [ ] shipping.md steps 4 and 5 state the gate/broker/person rule, and hold no `gh pr merge` and no `gh pr checks --watch`
- [ ] no `gh pr merge` or merge-api instruction left outside `eval/scenarios/**`
- [ ] `ci/README.md` carries the plan note (github pro on a private repo, or a public repo; otherwise the gate cannot bind)
- [ ] `scripts/build-board.sh` writes the board and `scripts/check-board.sh` prints ok
- [ ] the follow-ups (34, spec section 14) are recorded in the comments

## Comments

- 2026-10-18, owner: agent work on this machine runs under srt behind a local broker. the checkpoint, push, pr, review and cleanup rules live in `~/.agents/AGENTS.md`. the split: push, pull-request creation, verdict posting and worktree cleanup go through the broker clients only (`agent-gh`, `agent-worktree-remove`), never bare `gh`; merging belongs to the repo's own merge gate (`ci/github/arkan-merge.yml` plus required status checks) where it is installed and enforceable; fallback only where no gate can bind (for example a private repo on the free plan, where rulesets return 403), the broker, `agent-merge <pr> <sha>`; no session ever calls `gh pr merge` or any other merge api. this ticket writes the split into the skill texts and records the follow-ups.
- 2026-10-18: follow-ups recorded. (1) `arkan-flow` 34 shipped the gate itself: `ci/github/arkan-merge.yml` plus the install steps in `ci/README.md`. (2) teaching a repo how to install the gate is the parked pre-setup host-settings section 14 in `.scratch/review-ci/spec.md`, which waits on ticket 05.
