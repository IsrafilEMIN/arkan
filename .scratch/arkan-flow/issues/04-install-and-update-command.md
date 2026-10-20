# 04: install and update command

**Role:** ready-for-agent
**Closed:** no
**Priority:** 11

**What to build:** one command installs the arkan skills into `~/.agents/skills/`, and the same command updates them. running it twice changes nothing the second time.

**Blocked by:** None (can start immediately).

proposal (superseded 2026-10-19 by ticket 05: the command is the machine part of `skills/pre-setup/scripts/setup.sh`, not a root `install.sh`): a script in the repo root (for example `install.sh`) that keeps one checkout of arkan (a pinned tag or `main`), and links each `skills/<name>` into `~/.agents/skills/<name>` (one canonical copy, per `symlink-first`). update is `git pull` on that checkout, then the same link step. harness-specific links (for example `~/.claude/skills/`) are not its job; `pre-setup` does them (ticket 06).

- [x] on a clean machine, one command puts every arkan skill in `~/.agents/skills/`
- [x] a second run prints that nothing changed and changes nothing
- [x] an update run brings a new or changed skill in, and removes a skill that arkan removed, only if it is arkan's own link
- [x] a skill folder in `~/.agents/skills/` that arkan did not make is never overwritten; the script reports the clash and stops for that skill
- [x] the command prints the arkan version (tag or commit) it installed
- [x] works on linux and macos (bash), with no tool beyond git
- [x] for claude code, arkan installs as a plugin (a `.claude-plugin/plugin.json` manifest, plus a marketplace entry or `--plugin-dir`), not as plain skills in `~/.claude/skills/`. a plain skill named like a built-in command replaces it (arkan `code-review` would replace `/code-review`); a plugin skill is named `arkan:<skill>`, so both stay
- [ ] proof: in a fresh claude code session, `/code-review` runs the built-in and `/arkan:code-review` runs arkan's

## Comments

- 2026-10-18, owner: do this ticket last, after every other open ticket. ticket 07 waits on it, so 07 comes last too.
- 2026-10-18, owner: claude code gets arkan as a plugin, so no skill is renamed (ticket 17). sources read 2026-10-18: claude code <https://code.claude.com/docs/en/skills>; codex source `codex-rs/skills/src/` in <https://github.com/openai/codex> (its docs page was blocked from the cloud session); pi <https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/skills.md>; omp <https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md>.
- 2026-10-19, ticket 05: no separate `install.sh` and no `arkan-install` skill. the one command is `skills/pre-setup/scripts/setup.sh`, run from a clone of arkan; its machine items install arkan, the claude code plugin, and the links in `~/.agents/skills/`. the criteria above still hold for it.
- 2026-10-19: built in `skills/pre-setup/scripts/setup.sh` and `.claude-plugin/`. boxes 1 to 7 ticked; box 8 stays open because a fresh claude code session is the missing prerequisite, and this environment cannot run `/plugin marketplace add <path>` or `claude --plugin-dir <path>`. proof, in a temp `HOME` and a temp copy of arkan, run from `/tmp`: `apply arkan` linked 84 skills; a second run printed `setup: nothing changed; version v0.0.0-test` and the link list was identical; a new `skills/zz-new` was linked; removing it read `stale: zz-new` and `apply` printed `removed 1`, with a foreign directory untouched; a real `~/.agents/skills/architect` read `clash: architect; left alone`, `apply` linked the other missing skills and exited 1; a link to another arkan checkout stayed in place; `check <repo-root>` from `/tmp` printed both machine lines first and the same repo lines as a run from the repo. box 6 ran under macOS `/bin/bash` 3.2.57, the oldest bash; the script uses bash 3.2 syntax and no tool beyond git and POSIX shell utilities. linux itself was not run here.
