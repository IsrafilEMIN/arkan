# 58: link-agents.sh --check writes, and setup.sh misses a verify skill

**Role:** ready-for-agent
**Closed:** no
**Priority:** 67
**Blocked by:** None (can start immediately).

**What to build:** two small script bugs from the full review (findings A3 and A6).

1. `skills/symlink-first/scripts/link-agents.sh:82` runs `mkdir -p ~/.claude/skills` in every mode. `--check` must change nothing.
2. `skills/pre-setup/scripts/setup.sh:842` runs `ls -d "$root"/.claude/skills/*verif* "$root"/.agents/skills/*verif*`. when one glob matches nothing, `ls` fails, so a repo with a verify skill in only one of the two folders reads `verify hint "no verify skill"`.

- [ ] `link-agents.sh --check` in a temporary `HOME` with no `~/.claude/skills` leaves the folder absent and reports `MISSING` for each link
- [ ] `setup.sh check` reads `verify ok` when a verify skill is only in `.claude/skills/`, and when it is only in `.agents/skills/`
- [ ] `bash scripts/check.sh` prints `check: ok`

## Comments

- 2026-10-21, owner: agreed.
