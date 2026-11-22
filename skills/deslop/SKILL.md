---
name: deslop
description: "Remove AI-generated code slop from the branch's diff and clean up code style. Use before you commit a change, from opening-a-pr, for /skill:deslop, or \"deslop this\"."
---

# Remove AI code slop

Check the diff against trunk and remove AI-generated slop introduced in the branch. Run it in the branch's worktree:

```bash
trunk=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || { git remote set-head origin -a >/dev/null && git symbolic-ref --short refs/remotes/origin/HEAD; })
git diff "$trunk"...HEAD
git diff HEAD
```

The first diff shows committed work, the second shows uncommitted work. Skip generated files, lockfiles and vendored code.

## Focus Areas

- Extra comments that are unnecessary or inconsistent with local style
- Defensive checks or try/catch blocks that are abnormal for trusted code paths
- Casts to `any` used only to bypass type issues
- Deeply nested code that should be simplified with early returns
- Debug output, dead code, and changes the task did not ask for
- Other patterns inconsistent with the file and surrounding codebase

## Guardrails

- Keep behavior unchanged unless fixing a clear bug.
- Prefer minimal, focused edits over broad rewrites.
- After the edits, run the repo's checks for the touched paths.
- Keep the final summary concise (1-3 sentences), and name each file you changed.
