---
name: freeze
description: Freeze writes to one directory so every edit stays inside it, with a pre-tool-use guard that blocks writes outside the frozen directory. Use when the user says freeze <dir>, wants to lock edits to a directory, or asks to stop writes outside a path.
disable-model-invocation: true
hooks:
  PreToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: command
          command: "\"$HOME/.agents/skills/freeze/scripts/freeze-guard.sh\" hook"
---

# Freeze

Freeze writes to one directory. The guard script allows edits under the frozen directory. It blocks writes outside it. The guard runs as a claude code pre-tool-use hook.

## Procedure

1. Arm the freeze on the target directory.

```bash
"$HOME/.agents/skills/freeze/scripts/freeze-guard.sh" arm $ARGUMENTS
```

`$ARGUMENTS` is the directory from the user request. If it is empty, ask for the directory.

2. Edit only files under the frozen directory. The guard blocks any other target.

3. Check the state at any time.

```bash
"$HOME/.agents/skills/freeze/scripts/freeze-guard.sh" status
```

4. Lift the freeze when the work is done.

```bash
"$HOME/.agents/skills/freeze/scripts/freeze-guard.sh" disarm
```

The freeze is per project. The state key is the resolved project directory (`/` becomes `%`). The state file holds one absolute directory path.

## Setup

Claude code only. Other harnesses are not supported.

1. Install the skill so the guard sits at `$HOME/.agents/skills/freeze/scripts/freeze-guard.sh`, and install `jq`.
2. The frontmatter `hooks` block in this file registers the guard when you type `/freeze <dir>`. The skill then runs the arm command.
3. To keep the guard on in every session, copy the same block into the `hooks` key of `~/.claude/settings.json`. Add `Bash` to the matcher (`"Write|Edit|Bash"`) to turn on the shell write check.

The hook stays inert until a state file exists.

## Limits

- The guard checks the file tools of the harness only. Read tools pass untouched.
- Bash writes are a best-effort text check, and only when `Bash` is in the matcher. The guard reads `>`, `>>`, `2>`, `&>`, `tee`, and `sed -i` targets. A quoted path with a space, a variable, or a command substitution can hide a target.
- A subprocess write is invisible. A program that opens a file itself never reaches the guard.
- Path checks handle `..` and symlinks. The guard resolves the deepest existing ancestor of each target, then re-appends the rest. A textual compare alone cannot do this.
- This is a seatbelt, not a sandbox. It stops a mistaken edit. It does not stop a determined process.
