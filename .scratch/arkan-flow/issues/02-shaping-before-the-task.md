# 02: shaping happens before the task

**What to build:** the docs and `arkan-mode` show that grill, to-spec, to-tickets and wayfinder are shaping steps that run before a task exists, and a person starts each one. a task is the smallest piece of work an agent can finish alone, so `arkan-mode` takes a task and closes the loop by itself.

**Blocked by:** None (can start immediately).

- [x] `GLOSSARY.md` defines task, shaping, spec, ticket, task loop, playbook, principle
- [x] `docs/flow.md` "the flow in one view" puts shaping (s1 grill, s2 plan) above a "task" line, and the task loop (nodes 0 to 10) below it
- [x] `arkan-mode` step 0 checks that the work is a task, and names the shaping step to run when it is not
- [x] `docs/core-skills.md` and `docs/sources.md` say grill and plan run before the task, and tickets go to the tracker `pre-setup` set (not `.arkan/plans/`)

## Comments

- resolved 2026-10-18 on branch `claude/gracious-bohr-4fplby`. the task-loop nodes are renumbered: old 3..12 are now 1..10.
