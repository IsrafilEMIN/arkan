# 54: opening-a-pr owns the pr body; remove the `pr` skill

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 63
**Blocked by:** None (can start immediately).

**What to build:** two files tell an agent how to write a pr body, and they disagree. `skills/arkan-mode/playbooks/opening-a-pr.md` asks for `## Why`, `## What changed`, `## Scope`, `## Tradeoffs`, `## Blast Radius` and `## Verification`. `skills/pr/SKILL.md` asks for `## Summary`, `## Evidence` and `## Merge Danger`. `skills/arkan-mode/SKILL.md:57` tells the agent to use both. keep the opening-a-pr playbook as the one pr body format and delete the `pr` skill.

- [x] `skills/pr/` is gone: `SKILL.md`, `CREDITS.md` and `agents/openai.yaml`
- [x] the opening-a-pr `## Blast Radius` line asks how to undo the change: the revert command, a flag to turn off, or "one-way door: no clean revert". this keeps what ticket 43 added to the `pr` skill
- [x] every reference to the `pr` skill names the opening-a-pr playbook instead: `skills/arkan-mode/SKILL.md:57`, `skills/post-merge/SKILL.md:21`, `skills/benchmark-checklist/SKILL.md:34`, `skills/technical-writing/SKILL.md:93`, `README.md:54`, `README.md:60` and `NOTICE:9`
- [x] in a temporary `HOME`, `setup.sh apply arkan` removes the installed `pr` link after the skill is gone, and a second run prints `nothing changed`
- [x] `bash scripts/check.sh` prints `check: ok`

## Comments

- 2026-10-21, owner: decision. when the two formats conflict, opening-a-pr wins and the `pr` skill goes. source: the full review of both repos, finding A4 (two pr body templates).
- 2026-10-21, agent: the `pr` skill also carries a menu of visuals (pseudocode, call trees, mermaid, diffs) copied from dex horthy's `show-me` skill, credited in `skills/pr/CREDITS.md`. the menu goes with the skill. opening-a-pr already allows screenshots and videos after the sections. the closed tickets 05, 23 and 43 name the `pr` skill; they are history and stay as they are.
- 2026-10-21, agent: `git rm -r skills/pr` removes `SKILL.md`, `CREDITS.md` and `agents/openai.yaml`. the opening-a-pr `## Blast Radius` bullet now asks how to undo the change (the revert command, the flag to turn off, or "one-way door: no clean revert" and what someone must undo by hand), and keeps the `pr` skill's note that a change that is cheap to undo is lower risk. `arkan-mode`, `post-merge`, `benchmark-checklist` (its number goes in `## Verification`) and `technical-writing` name the opening-a-pr playbook; `README.md` drops `pr` from the matt pocock list and the CREDITS sentence; `NOTICE` drops the CREDITS sentence and keeps every license text. `git grep` outside `.scratch/` finds no other reference to the `pr` skill.
- 2026-10-21, agent: proof. `git archive agent/tickets-54-55` into a temp dir, then in a fresh temp `HOME`: `setup.sh apply arkan` from that copy linked 84 skills, with `~/.agents/skills/pr -> <base copy>/skills/pr`. `setup.sh apply arkan` from this branch printed `83 skill(s)`, `removed 1 (pr)`, `marker updated`, and the `pr` link is gone. a second run printed `setup: nothing changed`. `bash scripts/check.sh` printed `check: ok`. closed.
