# 04: install and update command

**What to build:** one command installs the arkan skills into `~/.agents/skills/`, and the same command updates them. running it twice changes nothing the second time.

**Blocked by:** None (can start immediately).

proposal: a script in the repo root (for example `install.sh`) that keeps one checkout of arkan (a pinned tag or `main`), and links each `skills/<name>` into `~/.agents/skills/<name>` (one canonical copy, per `symlink-first`). update is `git pull` on that checkout, then the same link step. harness-specific links (for example `~/.claude/skills/`) are not its job; `pre-setup` does them (ticket 06).

- [ ] on a clean machine, one command puts every arkan skill in `~/.agents/skills/`
- [ ] a second run prints that nothing changed and changes nothing
- [ ] an update run brings a new or changed skill in, and removes a skill that arkan removed, only if it is arkan's own link
- [ ] a skill folder in `~/.agents/skills/` that arkan did not make is never overwritten; the script reports the clash and stops for that skill
- [ ] the command prints the arkan version (tag or commit) it installed
- [ ] works on linux and macos (bash), with no tool beyond git
- [ ] for claude code, arkan installs as a plugin (a `.claude-plugin/plugin.json` manifest, plus a marketplace entry or `--plugin-dir`), not as plain skills in `~/.claude/skills/`. a plain skill named like a built-in command replaces it (arkan `code-review` would replace `/code-review`); a plugin skill is named `arkan:<skill>`, so both stay
- [ ] proof: in a fresh claude code session, `/code-review` runs the built-in and `/arkan:code-review` runs arkan's

## Comments

- 2026-10-18, owner: do this ticket last, after every other open ticket. ticket 07 waits on it, so 07 comes last too.
- 2026-10-18, owner: claude code gets arkan as a plugin, so no skill is renamed (ticket 17). sources read 2026-10-18: claude code <https://code.claude.com/docs/en/skills>; codex source `codex-rs/skills/src/` in <https://github.com/openai/codex> (its docs page was blocked from the cloud session); pi <https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/skills.md>; omp <https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md>.
