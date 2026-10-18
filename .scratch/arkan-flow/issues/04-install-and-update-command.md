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

## Comments

- 2026-10-18, owner: do this ticket last, after every other open ticket. ticket 07 waits on it, so 07 comes last too.
