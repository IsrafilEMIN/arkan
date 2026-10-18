# 01: arkan-mode replaces poteto-mode

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 23

**What to build:** `arkan-mode` is the only engineering mode. it carries pstack's playbooks in its own folder, ported for every harness, and `poteto-mode` is removed from the bundle. an agent that starts a task in any harness gets playbook steps it can follow with that harness's own tools.

**Blocked by:** None (can start immediately).

done already (2026-10-18, this branch): `skills/arkan-mode/SKILL.md` is rewritten on the shape of `poteto-mode` (task check, playbook match, principles, triggers, autonomy, subagents, reply, comments), and `skills/arkan-mode/playbooks` is a link to `../poteto-mode/playbooks` so every named playbook opens.

- [x] `skills/arkan-mode/playbooks/` is a real folder with the 12 playbooks `arkan-mode` names (investigation, bug fix, feature, refactoring, prototype, authoring a skill, autonomous run, pause safely, session pickup, opening a pr, babysit, shipping); the link is gone
- [x] no cursor-only part is left: `grep -rEin 'subagent_type|run_in_background|cursor|grok|origin pr|control-ui|control-cli|deslop|poteto-agent' skills/arkan-mode` prints no line, or each line left is reported in the comments with why
- [x] each step that named a skill that is not installed (`swarm`, `arena`, `interrogate`, `show-me-your-work`, `ketchup`, `architect`, ...) names an installed skill, a planned arkan skill, or plain steps
- [x] pstack's scripts (`watch-pr`, `orch`, `check-plan`, `bootstrap`, `worktree-audit.sh`) and `references/bugbot-triage.md` are each ported, kept, or dropped, with a note per item in the comments
- [x] `arkan-mode/principles/` covers all 24 principles (one entry each); then the 24 `skills/principle-*` folders are removed, or kept by an owner decision recorded here
- [x] `skills/poteto-mode/` is removed; `grep -rn poteto-mode skills docs` only finds history notes
- [x] the mit notice for pstack text is kept (see `NOTICE`)
- [x] each change in behavior from pstack is reported in the comments for owner confirmation before it lands

## Comments

- supersedes `completion-loop` ticket 01 ("port poteto-mode to all agents"): the port now goes into `arkan-mode`, not into `poteto-mode`.
- 2026-10-18, done on branch `claude/fervent-turing-qu5b6e`:
  - `skills/arkan-mode/playbooks/` holds the 12 playbooks as real files; the link is gone. the first commit copies them unchanged, so the port shows as its own diff.
  - the ticket's grep prints no line in `skills/arkan-mode`.
  - skills that are not installed now point at what arkan has: `how` and `why` → read the code and its git history; `architect` → sketch types and signatures with empty bodies; `arena` → sketch two or three shapes (exhaust the design space); `interrogate` → `code-review` in a fresh context; `show-me-your-work` → the decision trail in `SKILL.md`; `figure-it-out` → shaping (step 0); `create-skill` → `writing-for-agents`; `deslop`, `no-comments`, `technical-writing`, `unslop` → the reply and comment rules in `SKILL.md`; the control skills → the repo's verify skill or the harness's own tools; cursor's `/loop` → the harness's loop or wake-up tool; principle skills → `principles/<group>.md`.
  - pstack's scripts are dropped: `watch-pr` (babysit and shipping now use `gh pr view` and `gh pr checks --watch`, or the harness's pr events), `orch`, `check-plan`, `bootstrap` and `worktree-audit.sh` (no arkan playbook used them). `references/bugbot-triage.md` is dropped; babysit points at "review bots and security bots" in `SKILL.md`. git history keeps all of them.
  - `principles/` already had all 24 principles; the 24 `skills/principle-*` folders and `skills/poteto-mode/` are removed (owner decision, 2026-10-18).
  - `NOTICE` keeps the pstack license and now names `skills/arkan-mode/`.
  - changes in behavior from pstack, for the owner to confirm: no Origin forge, only `gh` or the run's github tools; no `arena` bakeoff before a feature; no multi-model `interrogate` for a contested design (it is named in the pr instead); the autopilot exemptions in opening a pr and babysit are gone; babysit's frozen queued-stack list and bugbot pass count from `watch-pr` are gone; a shipping verifier is any agent that did not write the code, not a cursor cloud agent.
