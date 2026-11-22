---
name: opening-a-pr
description: "Turn the checked work on a worktree branch into small commits, fetch, push it, and open a ready PR with a fixed title and body shape. Use at the end of any change that ships, after wt-playbook, for /skill:opening-a-pr, or \"open a PR\"."
---

# Opening a PR

Use at the end of every change that ships. Start from the worktree and branch that the `wt-playbook` skill made (`../wt-playbook/SKILL.md`). Run every command below with the worktree as `cwd`, and set `trunk=$(git symbolic-ref --short refs/remotes/origin/HEAD)`.

1. **Check the worktree.** Work from a git worktree off trunk, and keep unrelated work out of it. `git status --short` shows only this change's files, and `git log --oneline "$trunk"..HEAD` shows only this change's commits.
2. **Shape the commits.** Rebase into small, landable commits. Then read the full diff (`git diff "$trunk"...HEAD`) and remove debug output, dead code, and changes the task did not ask for.
3. **Fetch before each push.** Run `git fetch origin`. If trunk moved, rebase onto it (`git rebase "$trunk"`) before the first push, and run the repo's checks for the touched paths on the committed head, so CI runs on the base the patch lands on. After the PR is open, rebase again only for a conflict, a CI break that trunk caused, or a trunk change to the same files, because each rebase restarts CI.
4. **Push.** First push: `git push -u origin HEAD`. Later pushes: `git push`. After a rebase, push only your own branch, with `git push --force-with-lease=<branch>:<sha you last pushed>`. If the remote branch has a commit that you did not push, stop and report it. For long work, open the PR after the first checked unit, so CI and review bots run while you work, and push each finished unit before you start the next.
5. **Title:** `type(scope): subject`, naming a real symbol when one carries the change. Type is one of `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`. No period at the end.
6. **Body:** a one-minute briefing under 40 lines with these `##` headings in order, dropping empty ones: `## Why`, `## What changed`, `## Scope`, `## Tradeoffs` (only rejected alternatives a reviewer would otherwise ask about), `## Blast Radius`, `## Verification`. Under Verification, say what you ran and what you did not verify.
7. **Open it ready.** Write the body to a file in `$TMPDIR`, then run `gh pr create --base <trunk branch> --head <branch> --title "<title>" --body-file <file>` without `--draft`.
8. **Stack only when the PR builds on another open PR.** Use `--base <parent branch>`, and rebase onto the parent branch, not trunk. When the parent gets a new head, rebase onto it and push with the lease from step 4. When the parent merges, run `gh pr edit <pr> --base <trunk branch>`, rebase onto trunk, and push with the lease.

Opening a PR does not merge it, and does not give permission to merge it.

**Reply:** the PR as a link, its title, what you verified, and what you did not verify.
