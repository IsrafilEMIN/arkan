# 47: the broker merges arkan's pull requests

**Role:** ready-for-agent
**Closed:** no
**Priority:** 9

**What to build:** arkan stops merging through its `arkan-merge` workflow; the broker on the owner's mac merges instead, with `--merge --delete-branch`, so merged branches are deleted and stacked pull requests retarget to `main`. the `PASS` rule does not change: the broker's own row-6 check (underground 49) runs before every merge, and `arkan-risk` still writes the label it reads.

**Blocked by:** None for the arkan side. the automatic part needs underground's broker merge loop (its ticket 52); until it ships, the agent runs `agent-merge` after the person's `PASS`.

decisions (owner, 2026-10-19): remove arkan's gate (not a check-only gate: a failed check run stays red on the head and would block the broker's later merge); the agent calls `agent-merge` when its session is still open, and the broker's loop merges the rest every 5 minutes.

- [ ] `.github/workflows/arkan-merge.yml` is removed from arkan. `ci/github/arkan-merge.yml` stays as the gate other repos can choose
- [ ] `arkan-mode`'s shipping playbook: where a repo has no gate, wait for the person's `PASS`, then `agent-merge <pr> <sha>`; where the broker loop runs, the agent may leave the merge to it
- [ ] `AGENTS.md` `### Merging` and `docs/seam.md` row 6 say arkan merges through the broker
- [ ] `pre-setup`'s `ci-merge` item asks which path the repo uses (gate or broker) instead of always offering the gate
- [ ] proof: one arkan pull request merges through the broker after the owner's `PASS`, merged by the owner's account, with its branch deleted

## Comments
