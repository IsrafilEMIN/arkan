# 25: a claim that agents can check

**What to build:** a claim works as a lock: before any work, the agent pushes a branch with a fixed name per ticket, `claim/<feature>-<NN>`. git rejects the push if that branch exists, so two agents never start the same ticket. the claim branch points at the work branch (the harness may pick the work branch's name). the merge deletes the claim branch, the work branch and the worktree.

**Blocked by:** None (can start immediately).

- [ ] the `## Board` section of `docs/agents/issue-tracker.md` and `arkan-mode` step 0 say how to claim, check and release
- [ ] proof: two agents that try to claim one ticket at once: one push wins, the other stops and picks another ticket
