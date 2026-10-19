# 50: make the 24 principles skills, pstack-shaped

**Role:** ready-for-agent
**Closed:** no
**Priority:** 34
**Blocked by:** None — starts after ticket 49 merges, because both edit `skills/arkan-mode/SKILL.md`.

**What to build:** move the 24 principles from prose in `skills/arkan-mode/principles/` into leaf skills, the way pstack ships them. The owner approved this shape on 2026-10-19.

- add `skills/principle-<title>/` for all 24 principles. start from the pstack copies installed in `~/.agents/skills/principle-*`, drop cursor-only references, and point paths at arkan-mode. each folder gets `agents/openai.yaml` with `allow_implicit_invocation: false`, matching `disable-model-invocation: true` in the front matter.
- `principle-test-behavior-not-implementation` already exists from ticket 49 and keeps its arkan additions.
- delete `skills/arkan-mode/principles/` after folding any arkan-only rule into the matching leaf.
- rewrite the principles section of `arkan-mode/SKILL.md`: one line says each entry names the `principle-<title>` skill and its leaf is read in full; the 24 entries keep their "when it applies" lines, grouped as now.
- rewrite the 58 citations of `principles/` in skills, README and docs to name the skill, not the file. cite by skill name so a later move costs less.
- update `README.md`'s source table: the 24 are pstack copies, adapted.
- after the merge, the owner relinks `~/.agents/skills/principle-*` to the arkan copies.

**Touches:** `skills/principle-*/`, `skills/arkan-mode/SKILL.md`, `skills/arkan-mode/principles/` (delete), every skill that cites `principles/`, `README.md`.

- [ ] 24 leaf skills exist, each with front matter, `agents/openai.yaml`, and no cursor-only reference.
- [ ] `skills/arkan-mode/principles/` is deleted; no file cites it.
- [ ] `bash scripts/check.sh` prints `check: ok`.
- [ ] the board is rebuilt and checked.

## Comments

- 2026-10-19, owner: approved the recovery proposal in session. the installed pstack copies are the base; arkan's prose files are checked for extra rules before deletion.
