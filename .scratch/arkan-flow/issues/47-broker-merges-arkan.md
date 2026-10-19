# 47: the broker merges arkan's pull requests

**Role:** ready-for-agent
**Closed:** no
**Priority:** 9

**What to build:** arkan stops merging through its `arkan-merge` workflow; the broker on the owner's mac merges instead, with `--merge --delete-branch`, so merged branches are deleted and stacked pull requests retarget to `main`. the `PASS` rule does not change: the broker's own row-6 check (underground 49) runs before every merge, and `arkan-risk` still writes the label it reads.

**Blocked by:** None for the arkan side. the automatic part needs underground's broker merge loop (its ticket 52); until it ships, the agent runs `agent-merge` after the person's `PASS`.

decisions (owner, 2026-10-19): remove arkan's gate (not a check-only gate: a failed check run stays red on the head and would block the broker's later merge); the agent calls `agent-merge` when its session is still open, and the broker's loop merges the rest every 5 minutes.

- [x] `.github/workflows/arkan-merge.yml` is removed from arkan. `ci/github/arkan-merge.yml` stays as the gate other repos can choose
- [x] `arkan-mode`'s shipping playbook: where a repo has no gate, wait for the person's `PASS`, then `agent-merge <pr> <sha>`; where the broker loop runs, the agent may leave the merge to it
- [x] `AGENTS.md` `### Merging` and `docs/seam.md` row 6 say arkan merges through the broker
- [x] `pre-setup`'s `ci-merge` item asks which path the repo uses (gate or broker) instead of always offering the gate
- [ ] proof: one arkan pull request merges through the broker after the owner's `PASS`, merged by the owner's account, with its branch deleted

## Comments

- 2026-10-19, agent: implemented on `agent/ticket-47-broker-merge`. `pre-setup` records the local choice as `**Merge path:** broker` or `**Merge path:** gate` in the approvals doc. scratch CLI runs covered a missing choice, broker check and apply without writes, a broker/gate conflict, a matching gate, an edited gate, gate installation, and an existing gate without a record. all passed with `/bin/bash`; check calls changed no fixture files.
- 2026-10-19, still open: the paired underground row-6 update needs a writable underground session. worktree creation failed with `git branch: A lock could not be obtained for reference "refs/heads/agent/arkan-47-seam"`. a paired patch passed `git apply --check` against underground's current contract. the final acceptance box stays open until an arkan pull request merges through the broker after the owner's unmarked `PASS`, with the merge account and branch deletion verified. no live merge proof exists yet.
