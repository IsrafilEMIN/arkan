# 01: add an enhance skill that audits arkan against its upstream skill sources

**Role:** ready-for-agent
**Closed:** no
**Priority:** 71
**Blocked by:** None (can start immediately).

**What to build:** a manual-only skill, `enhance`, that compares arkan's skill bundle with its two upstream skill sources and reports what to change. A person starts it; no trigger starts it.

The sources:

- [mattpocock/skills](https://github.com/mattpocock/skills) by matt pocock. Its skills live under `skills/engineering/` and `skills/productivity/`.
- [pstack](https://github.com/cursor/plugins/tree/main/pstack) by lauren tan. Its skills live under `pstack/skills/`.

`README.md`, section "where the skills come from", records which arkan skill comes from which source. Read that table as the mapping. A matching folder name alone is not the mapping.

**Report.** Report to the person in the conversation. Write no file in the repo. If the person asks for a file, write it outside the repo. Every run names the arkan commit and the commit each source was read at. Every finding names the upstream path and the arkan path, and cites the line or rule as evidence. The report has these sections. Print each section even when it says `none found`.

- **enhancements**: an upstream skill arkan carries, where upstream has a rule, example, fix or trigger that arkan lacks.
- **additions**: an upstream skill arkan does not carry, or an upstream rule that belongs in a skill arkan already carries.
- **deletions**: an arkan skill whose upstream source was removed or replaced, an arkan skill with no recorded source that no playbook uses, or an arkan skill that another skill now covers.
- **other**: a renamed, moved or removed upstream skill; an adaptation that drifted; a credit or `NOTICE` entry that no longer matches; a name clash; an upstream change that arkan should keep out.

**Divergence.** A difference is not automatically a defect. arkan removed cursor-only parts and changed paths, merge flow and review rules on purpose. Report a deliberate difference as `keep: divergence` with the reason. Do not propose that arkan reverts it.

**Tracking.**

- A row in the table with a commit records the base for the skills it lists. Read that commit as the base and report base..head changes separately from the full comparison.
- The matt pocock row says `main branch` and records no base. Report its head sha and say the base is unknown on the first run. Later runs compare against the sha in the previous report or in the table.
- If one source cannot be read, name the source and the error, and compare the other source. Do not guess.

**Files.**

- `skills/enhance/SKILL.md` with `disable-model-invocation: true`. Its description names both sources and says a person starts it.
- `skills/enhance/agents/openai.yaml` with `allow_implicit_invocation: false` and display name `Enhance`.
- `README.md`: add `enhance` to the skill map and to the `written for arkan` row of the source table.

**Acceptance:**

- [ ] both skill files exist, and `scripts/check.sh` agrees on who starts the skill.
- [ ] the skill names both sources, their paths, and the README table as the mapping.
- [ ] one run prints the arkan commit and both upstream commits, lists every upstream skill with a verdict (`carried`, `not carried` or `renamed`), lists every `skills/*/` folder with a source verdict (`mapped`, `written for arkan` or `not recorded`), and prints the four report sections.
- [ ] every finding cites `upstream path -> arkan path` and a line or rule as evidence.
- [ ] the run reports at least one deliberate difference as `keep: divergence` and does not count it as a deletion.
- [ ] an unreachable source produces a named error and leaves the other source's comparison intact.
- [ ] the run writes nothing: `git status --porcelain` is the same before and after.
- [ ] `README.md` names `enhance`.
- [ ] `PYTHONDONTWRITEBYTECODE=1 bash scripts/check.sh` prints `check: ok`.
- [ ] `scripts/board.sh build` then `scripts/board.sh check` prints `ok`.
- [ ] the run's actual report is in the comments.

**Touches:** `skills/enhance/`, `README.md`, `.scratch/`.
