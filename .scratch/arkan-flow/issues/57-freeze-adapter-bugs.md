# 57: freeze blocks reads, misses patches and follows no file symlink

**Role:** ready-for-agent
**Closed:** no
**Priority:** 66
**Blocked by:** None (can start immediately).

**What to build:** three bugs in the `freeze` skill, each reproduced in memory during the full review (2026-10-21):

1. `skills/freeze/adapters/freeze.ts:12-25,119-120` sends any tool call with a `path`, `file_path`, `file` or `paths` field to `freeze-guard.sh write`. a read tool outside the frozen folder is blocked: `{toolName: "read", input: {path: "/outside/file"}}` returned `block: true`. `SKILL.md` says reads pass.
2. the same handler checks only path fields and `command`. a call whose target is in a `patch` field (`{toolName: "apply_patch", input: {patch: "*** Update File: /outside/file"}}`) returns `undefined`: no check runs. `freeze-guard.sh` already parses `*** Add|Update|Delete File:` lines in `command_writes`.
3. `skills/freeze/scripts/freeze-guard.sh:40-46` (`physical`) resolves the parent folder but not a final file symlink. `physical arkan/scripts/board.sh` returned the link path, not `skills/pre-setup/scripts/board.sh`, so a symlink inside the frozen folder that points outside passes.

- [ ] `freeze.ts` checks only tools that write. it reads the tool name from the event; an unknown tool name with a path field is still checked as a write, so a new write tool is not missed
- [ ] a `patch` (or `input`) string field goes to the guard's `hook` mode, so its `*** ... File:` targets are checked
- [ ] `physical` follows a final symlink before the prefix compare, with a hop limit
- [ ] tests or a script in `skills/freeze/` reproduce all three cases red before the fix and green after
- [ ] `bash scripts/check.sh` prints `check: ok`

## Comments

- 2026-10-21, owner: agreed. source: the full review, finding A2. the docs part (claude matcher, `/freeze arm`) is ticket 55.
