# 58: link-agents.sh --check writes, and setup.sh misses a verify skill

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 67
**Blocked by:** None (can start immediately).

**What to build:** two small script bugs from the full review (findings A3 and A6).

1. `skills/symlink-first/scripts/link-agents.sh:82` runs `mkdir -p ~/.claude/skills` in every mode. `--check` must change nothing.
2. `skills/pre-setup/scripts/setup.sh:842` runs `ls -d "$root"/.claude/skills/*verif* "$root"/.agents/skills/*verif*`. when one glob matches nothing, `ls` fails, so a repo with a verify skill in only one of the two folders reads `verify hint "no verify skill"`.

- [x] `link-agents.sh --check` in a temporary `HOME` with no `~/.claude/skills` leaves the folder absent and reports `MISSING` for each link
- [x] `setup.sh check` reads `verify ok` when a verify skill is only in `.claude/skills/`, and when it is only in `.agents/skills/`
- [x] `bash scripts/check.sh` prints `check: ok`

## Comments

- 2026-10-21, owner: agreed.
- 2026-10-21, agent: fixed. `link-agents.sh` runs `mkdir -p` only when not `--check`, and skips the dangling-link loop when the mirror folder is absent. `setup.sh` tests each glob match with `[ -e ]`. proof in a temp `HOME` with `.agents/skills/x/SKILL.md` and `agents/openai.yaml`, `HOME=$H bash link-agents.sh --check`: base prints `MISSING .claude/CLAUDE.md`, `MISSING .claude/skills/x`, exit 1, and creates `.claude/skills`; fix prints the same two `MISSING` lines, exit 1, and `.claude/skills` stays absent. link mode still creates the folder and `linked .claude/skills/x`, `ok`. `setup.sh check` on a temp repo with only `.claude/skills/verify-app`, then only `.agents/skills/verify-app`: base reads `verify hint no verify skill` for both; fix reads `verify ok` for both. an empty repo still reads `verify hint`. `bash scripts/check.sh`: `check: ok`.
