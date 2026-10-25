# 57: freeze blocks reads, misses patches and follows no file symlink

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 66
**Blocked by:** None (can start immediately).

**What to build:** three bugs in the `freeze` skill, each reproduced in memory during the full review (2026-10-21):

1. `skills/freeze/adapters/freeze.ts:12-25,119-120` sends any tool call with a `path`, `file_path`, `file` or `paths` field to `freeze-guard.sh write`. a read tool outside the frozen folder is blocked: `{toolName: "read", input: {path: "/outside/file"}}` returned `block: true`. `SKILL.md` says reads pass.
2. the same handler checks only path fields and `command`. a call whose target is in a `patch` field (`{toolName: "apply_patch", input: {patch: "*** Update File: /outside/file"}}`) returns `undefined`: no check runs. `freeze-guard.sh` already parses `*** Add|Update|Delete File:` lines in `command_writes`.
3. `skills/freeze/scripts/freeze-guard.sh:40-46` (`physical`) resolves the parent folder but not a final file symlink. `physical arkan/scripts/board.sh` returned the link path, not `skills/pre-setup/scripts/board.sh`, so a symlink inside the frozen folder that points outside passes.

- [x] `freeze.ts` checks only tools that write. it reads the tool name from the event; an unknown tool name with a path field is still checked as a write, so a new write tool is not missed
- [x] a `patch` (or `input`) string field goes to the guard's `hook` mode, so its `*** ... File:` targets are checked
- [x] `physical` follows a final symlink before the prefix compare, with a hop limit
- [x] tests or a script in `skills/freeze/` reproduce all three cases red before the fix and green after
- [x] `bash scripts/check.sh` prints `check: ok`

## Comments

- 2026-10-21, owner: agreed. source: the full review, finding A2. the docs part (claude matcher, `/freeze arm`) is ticket 55.
- 2026-10-25, agent: fixed. `freeze.ts` skips the omp and pi read tools (`read`, `grep`, `search`, `find`, `glob`, `ls`, `ast_grep`, `web_search`, from omp `builtin-names.ts` and pi `dist/core/tools`) and the read actions of `lsp` (`rename`, `rename_file`, `code_actions` and `request` can write, so they are checked). any other tool with a path field goes to `write`. a `command`, `patch` or `input` string goes to `hook` (omp `edit` in apply_patch mode sends `input`). the guard's `hook` mode now reads `tool_input.patch` and `tool_input.input` through a new `patch_writes` (envelope lines only, no shell parse). `physical` follows a final file symlink, also a dangling one, for at most 40 hops. proof: `skills/freeze/scripts/freeze-test.sh` (temp HOME, temp state, real guard, node loads the adapter and calls the `tool_call` handler). on the base code (65c2c48 copies) it prints 13 `FAIL` lines, `exit=1`: `guard write frozen/link -> 0, want 2`, same for `rel-link` and `dangling`, both `hook` patch payloads `-> 0, want 2`, `adapter read|grep|find|glob|ls|lsp diagnostics -> block, want pass`, `adapter apply_patch {patch} -> pass, want block`, `adapter edit {input} -> pass, want block`. after the fix, under `/bin/bash` 3.2.57 too, all 26 cases are `ok` and it prints `freeze-test: ok`. `bash scripts/check.sh` prints `check: ok`.
