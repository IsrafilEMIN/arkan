### Shipping

**You own what lands. Run the change the way a user would, merge only through the broker's merge rule, then confirm the cleanup.** Every PR targets trunk (no stacks, see **Size** in `playbooks/opening-a-pr.md`), so each PR lands on its own, lowest first.

1. **Run the user path on the head before it lands.** One verifier per PR, a subagent or a separate session that did not write the code, runs the change the way a user would, with the repo's verify skill or the harness's own browser, terminal, or API tools. It compares parent against head and returns `PASS`, `PASS+NOTES`, or `FAIL`, with the head sha it ran, the run path and the outcome. The broker does not check this step, so it binds you: on `FAIL`, do not merge; fix it on a new head, which needs fresh reviewer verdicts. A verdict whose sha is not the current head does not describe the PR: run it again.
2. **Check the merge rule.** Read `broker pr-status <owner/repo> <n>` and walk every line of **the merge rule** in `references/broker.md` against it. A head with a missing verdict waits on its reviewer session. A hold goes to the person, per step 9 of `playbooks/babysit.md`.
3. **Merge.** Run `broker merge <owner/repo> <n>`. If the broker refuses, stop and report its exact reason. Then read the PR back with `gh-broker pr-status` until it reads merged with trunk as its base, because a queued merge is not a landed one.
4. **Confirm the cleanup.** Read the merge's output: `removed worktree` and `deleted local branch` mean the local cleanup is done. A `kept` line or an error means it is not: report the path and the reason. Check the remote branch with `git ls-remote --heads origin <branch>`, and report it as left over when it still prints a sha, because the broker cannot delete it.
5. **Leave the PRs alone while they land.** Change no branch while a merge is pending, because a merge lands whatever its branch holds at that moment. If a merge stalls, find out why before you change anything.
6. **Move to the next PR.** The next lowest PR starts again at step 1 on its own head.

**Reply:** each PR with its link, head sha, user-path verdict and who produced it, the reviewer verdicts, what landed, the cleanup lines, any remote branch left over, and any hold with its reason.
