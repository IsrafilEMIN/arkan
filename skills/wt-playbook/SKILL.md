---
name: wt-playbook
description: "Start a change in its own git worktree and branch off current trunk, work there, then hand off to opening-a-pr. Use before the first edit of any change that will ship as a PR, for /skill:wt-playbook, or \"make a worktree\"."
---

# Worktree playbook

One change, one worktree, one branch, one PR. Never edit in the repo's main checkout: other agents share it, and on an underground host a background fetch moves it to origin's default branch at each session start.

## 1. Use the session's worktree when it has one

From the repo, run:

```bash
git rev-parse --path-format=absolute --git-dir --git-common-dir
git symbolic-ref --quiet --short HEAD
git status --short
```

The session is in a linked worktree when the two paths differ. This is the case after the user runs `/wt`. Use that worktree when all of these are true:

- it is on a branch, and the branch is not trunk;
- the branch has no merged or closed PR (`gh pr list --head <branch> --state all`);
- `git status --short` shows no work from another task.

Otherwise make a new one in step 2.

## 2. Make a worktree

```bash
trunk=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || { git remote set-head origin -a >/dev/null && git symbolic-ref --short refs/remotes/origin/HEAD; })
git fetch origin
ts=$(date +%Y%m%d-%H%M%S)
repo=$(basename "$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")")
base=$HOME/.omp/wt
for b in "$(omp config get worktree.base --json 2>/dev/null | jq -r '.value // empty')" "${OMP_WORKTREE_DIR-}"; do
  b=${b/#\~/$HOME}; case $b in /*) base=$b ;; esac
done
wt="$base/wt-$ts-$repo"
omp wt add -b "wt/$ts" "$wt" "$trunk"
```

- **Trunk:** origin's default branch, for example `origin/main`. A repo made with `git init` and `git remote add` has no `origin/HEAD`, so the first line sets it with `git remote set-head origin -a`.
- **Branch name:** `wt/<yyyymmdd-hhmmss>`, the same as omp's `/wt`. Agents cannot run `/wt`, because only the user can run slash commands.
- **Path:** in omp's worktree base, so `omp wt list` shows it. The base is `OMP_WORKTREE_DIR`, else the `worktree.base` setting, else `~/.omp/wt`; like omp, the snippet skips a relative value. The directory name ends with the repo name; `/wt` ends it with a 7-hex hash of the repo path instead. `omp wt list` shows both forms.
- When the `worktree.clone` setting is on, `omp wt add` makes a copy-on-write clone and carries ignored caches such as `node_modules`; it makes a plain checkout when the setting is off or the filesystem cannot clone. A clone does not carry Python virtual environments or CMake build directories; make them again in the worktree.
- Without `omp` on `PATH`, use `git worktree add -b "wt/$ts" "$wt" "$trunk"`.
- The new branch has no upstream. The first push in step 4 sets it, so a plain `git push` can never go to trunk.

Tell the user the worktree path and the branch.

## 3. Work in the worktree

- The bash tool resets its working directory after each turn. Give the worktree path as `cwd` on every bash call, and give absolute worktree paths to `read`, `edit` and `write`. A relative path or a missing `cwd` changes the main checkout.
- Give the worktree path to each subagent in its task.
- Keep unrelated work out. A second change gets its own worktree.
- Commit each finished unit as you go, as a small commit that can land alone. Commit from bash with the worktree as `cwd`, not with the eval commit helper (`commit.draft()`): it works on the session's checkout, not the worktree. Never change git config. If git has no committer identity, give it for that one commit with `git -c user.name=<name> -c user.email=<email> commit`, with the identity the host uses.

## 4. Hand off

When the change is checked, push it with `git push -u origin HEAD`, then follow the `opening-a-pr` skill (`../opening-a-pr/SKILL.md`) to open the PR.

## 5. Cleanup

Do not remove worktrees as part of the change. On an underground host, the session-start sweep removes a worktree and its branch after 3 idle days when origin holds all of its work, and keeps the ones with an open PR.

When the user asks you to remove one, remove it only when `git status --short` in it is empty and its PR merged: `git worktree remove <path>`. For uncommitted or unpushed work, show it and ask first. Never run `omp wt clear --all`, because it removes the worktrees of other sessions too.
