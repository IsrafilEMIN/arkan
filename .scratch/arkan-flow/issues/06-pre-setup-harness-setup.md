# 06: pre-setup sets up each harness the user has

**Role:** ready-for-agent
**Closed:** no
**Priority:** 13

**What to build:** `pre-setup` asks which harnesses the user works in (for example claude code, codex, cursor, pi, omp), and sets each one up the way that harness expects, so a fresh session in each harness lists the arkan skills.

**Blocked by:** 05

- [ ] `skills/pre-setup/harnesses.md` holds one entry per supported harness: where it reads skills (user and project scope), the name of its instruction file (`AGENTS.md`, `CLAUDE.md`, ...), which frontmatter fields it reads, how it marks a skill as manual only (`disable-model-invocation`, `agents/openai.yaml` policy, ...), and whether it follows symlinks
- [ ] each fact in `harnesses.md` names its source (the harness's own docs, with a link and the date read), or is marked `unverified`
- [ ] pre-setup asks which harnesses the user has (multi-select), with the ones it finds on the machine pre-selected
- [ ] for a harness that reads `~/.agents/skills/`, pre-setup changes nothing
- [ ] for a harness that does not (claude code reads `~/.claude/skills/`, as far as we know), pre-setup links each arkan skill there, and links `CLAUDE.md` to `AGENTS.md` in the repo where needed
- [ ] a re-run changes nothing; a removed harness's links are removed only when the user says so
- [ ] proof: in each chosen harness, a fresh session lists the arkan skills
