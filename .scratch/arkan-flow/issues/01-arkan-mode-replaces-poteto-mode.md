# 01: arkan-mode replaces poteto-mode

**What to build:** `arkan-mode` is the only engineering mode. it carries pstack's playbooks in its own folder, ported for every harness, and `poteto-mode` is removed from the bundle. an agent that starts a task in any harness gets playbook steps it can follow with that harness's own tools.

**Blocked by:** None (can start immediately).

done already (2026-10-18, this branch): `skills/arkan-mode/SKILL.md` is rewritten on the shape of `poteto-mode` (task check, playbook match, principles, triggers, autonomy, subagents, reply, comments), and `skills/arkan-mode/playbooks` is a link to `../poteto-mode/playbooks` so every named playbook opens.

- [ ] `skills/arkan-mode/playbooks/` is a real folder with the 12 playbooks `arkan-mode` names (investigation, bug fix, feature, refactoring, prototype, authoring a skill, autonomous run, pause safely, session pickup, opening a pr, babysit, shipping); the link is gone
- [ ] no cursor-only part is left: `grep -rEin 'subagent_type|run_in_background|cursor|grok|origin pr|control-ui|control-cli|deslop|poteto-agent' skills/arkan-mode` prints no line, or each line left is reported in the comments with why
- [ ] each step that named a skill that is not installed (`swarm`, `arena`, `interrogate`, `show-me-your-work`, `ketchup`, `architect`, ...) names an installed skill, a planned arkan skill, or plain steps
- [ ] pstack's scripts (`watch-pr`, `orch`, `check-plan`, `bootstrap`, `worktree-audit.sh`) and `references/bugbot-triage.md` are each ported, kept, or dropped, with a note per item in the comments
- [ ] `arkan-mode/principles/` covers all 24 principles (one entry each); then the 24 `skills/principle-*` folders are removed, or kept by an owner decision recorded here
- [ ] `skills/poteto-mode/` is removed; `grep -rn poteto-mode skills docs` only finds history notes
- [ ] the mit notice for pstack text is kept (see `docs/sources.md`)
- [ ] each change in behavior from pstack is reported in the comments for owner confirmation before it lands

## Comments

- supersedes `completion-loop` ticket 01 ("port poteto-mode to all agents"): the port now goes into `arkan-mode`, not into `poteto-mode`.
