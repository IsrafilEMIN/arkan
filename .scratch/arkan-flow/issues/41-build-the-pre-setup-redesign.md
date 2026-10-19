# 41: build the pre-setup redesign

**Role:** ready-for-agent
**Closed:** no
**Priority:** 10

**What to build:** `skills/pre-setup/` as ticket 05's `## Answer` lays it out: a routing `SKILL.md`, `scripts/setup.sh` with `check` and `apply <item>`, and the seeds moved to `references/`. the repo sections (4 to 14) come first; the machine sections (1 to 3) belong to tickets 04, 06 and 17 and plug into the same script.

**Blocked by:** None (can start immediately).

- [ ] `setup.sh check` prints one line per item, `ok`, `missing` or `out of date`, and changes nothing
- [ ] `setup.sh apply <item>` installs an item that has no choice; a second run changes nothing
- [ ] the skill skips each `ok` item, asks only where 05's table says it asks, and asks before any change on the host
- [ ] the seed `references/issue-tracker-local.md` says to edit the ticket and run the skill's `board.sh`, not to edit the board by hand
- [ ] the domain-docs section writes `GLOSSARY.md merge=union` to `.gitattributes`
- [ ] `docs/agents/sensitive-paths.md` and `docs/agents/approvals.md` are written, each with a one-line entry in the `AGENTS.md` block
- [ ] a re-run in a set-up repo changes nothing; a ci workflow file older than arkan's copy is offered as an update, with its diff
- [ ] after the repo sections, the skill shows the diff and commits only after a yes
- [ ] proof: run in a fresh scratch repo, then again; the second run reports every item `ok` and leaves `git status` clean

## Comments
