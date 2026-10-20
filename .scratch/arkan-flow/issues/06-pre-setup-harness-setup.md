# 06: pre-setup sets up each harness the user has

**Role:** ready-for-agent
**Closed:** no
**Priority:** 13

**What to build:** `pre-setup` asks which harnesses the user works in (for example claude code, codex, cursor, pi, omp), and sets each one up the way that harness expects, so a fresh session in each harness lists the arkan skills.

**Blocked by:** 05, 41

- [x] `skills/pre-setup/harnesses.md` holds one entry per supported harness: where it reads skills (user and project scope), the name of its instruction file (`AGENTS.md`, `CLAUDE.md`, ...), which frontmatter fields it reads, how it marks a skill as manual only (`disable-model-invocation`, `agents/openai.yaml` policy, ...), and whether it follows symlinks
- [x] each fact in `harnesses.md` names its source (the harness's own docs, with a link and the date read), or is marked `unverified`
- [x] pre-setup asks which harnesses the user has (multi-select), with the ones it finds on the machine pre-selected
- [x] for a harness that reads `~/.agents/skills/`, pre-setup changes nothing
- [x] for claude code, pre-setup installs arkan as a plugin (ticket 04) and makes no links in `~/.claude/skills/`; it links `CLAUDE.md` to `AGENTS.md` in the repo where needed. for another harness that does not read `~/.agents/skills/`, it links each arkan skill where that harness reads skills
- [x] a re-run changes nothing; a removed harness's links are removed only when the user says so
- [ ] proof: in each chosen harness, a fresh session lists the arkan skills

## Comments

- 2026-10-19, ticket 05: this is section 2 of the `pre-setup` script (`setup.sh`), a machine item checked from any repo. claude code gets the plugin, not links. blocked by 41, which builds the script.
- 2026-10-19, agent, built on `agent/ticket-06-harnesses`: `skills/pre-setup/harnesses.md` has one section per harness (claude code, codex, pi, omp, cursor, opencode, hermes). each section covers user and project skill scope, the instruction file, the frontmatter fields, the manual-only mark, and symlinks, with a source per fact or `unverified`. `setup.sh` adds the machine item `harnesses` after `claude-plugin` and the repo item `claude-md` after `agents-block`. `SKILL.md` adds the multi-select ask with the detected harnesses pre-selected, the `claude-md` row, the removal rule (only after a yes), and the `harnesses.md` pointer. proof in a temp `HOME` and a temp repo, bash 3.2.57, with `claude` and `omp` off `PATH`: `~/.claude` and no plugin record read `harnesses missing  claude code needs the plugin; run setup.sh apply claude-plugin`; with a record that names `arkan@arkan` they read `harnesses ok  detected claude code; claude code uses the plugin` and `claude-md missing  CLAUDE.md -> AGENTS.md`; `apply claude-md` printed `claude-md ok  CLAUDE.md` and `readlink CLAUDE.md` read `AGENTS.md`; a second apply printed the same and left the link inode and mtime unchanged; a `HOME` with only `~/.codex` and `~/.pi` read `harnesses ok  detected codex, pi; reads ~/.agents/skills`; an empty `HOME` read `harnesses skip  no harness detected`; a repo without `AGENTS.md` read `claude-md skip  no AGENTS.md`; a real `CLAUDE.md` read `ok`, stayed a regular file, and kept its content; fake `opencode` and `omp` on `PATH` read `harnesses ok  detected codex, opencode, omp; reads ~/.agents/skills`; `~/.config/opencode`, `~/.cursor` and `~/.hermes` read `detected cursor, opencode, hermes`; a file snapshot before and after `check` was identical; the machine lines printed first (`arkan`, `claude-plugin`, `harnesses`), then `git`. box 7 stays open: a fresh session in each chosen harness is the missing prerequisite, and this sandbox has no harness session and cannot start one.
- 2026-10-20, review fixes: `harnesses` reads the install record and the cache only, never `claude`, and detects claude from the command or an installed plugin. hermes without a nested `skills.external_dirs` reads `hint`; the check anchors on a real `external_dirs` entry, so a commented line does not count. dsh is detected, documented with its `DSH_AGENTS_HOME` override, and normalizes a tilde or blank override before it warns. dsh and hermes hints append instead of replacing each other.
