# 23: who starts each skill

**Role:** ready-for-agent
**Closed:** no
**Priority:** 7

**What to build:** each skill's frontmatter says who starts it: only the person (`disable-model-invocation: true`, and `agents/openai.yaml` `allow_implicit_invocation: false`), both (default), or only the agent (`user-invocable: false`, which hides it from the `/` menu). rule: a skill that shapes the work, has side effects on the repo or harness, or looks back is the person's; one the person wants on demand and the agent needs mid-task is both; a policy or vocabulary the agent applies is the agent's.

**Blocked by:** None (can start immediately).

| who | skills |
|---|---|
| person only | `grill-with-docs`, `to-spec`, `to-tickets`, `wayfinder`, `product-brief`, `triage`, `pre-setup`, `setup-pre-commit`, `git-guardrails-claude-code`, `freeze`, `wait-what`, `improve-codebase-architecture`, `handoff` |
| both | `arkan-mode`, `code-review`, `diagnosing-bugs`, `prototype`, `grilling`, `assess`, `simplest-path`, `wizard`, `retro` |
| agent only | `tdd`, `test-to-break`, `codebase-design`, `domain-modeling`, `writing-for-agents`, `good-css`, `symlink-first`, `pr` |

harness facts (sources in ticket 17): only claude code can hide a skill from the menu; codex, pi and omp ignore `user-invocable`, so agent-only skills still show there. `triage` stays person only because `#ready-for-agent` is the person's go (ticket 26).

- [ ] every `skills/*/SKILL.md` frontmatter matches the table, and `agents/openai.yaml` matches where it exists
- [ ] proof: in claude code, the agent-only skills are not in the `/` menu and the person-only ones are not in the agent's skill list

## Comments

- 2026-10-18, owner: agreed in session. `retro` as both, `setup-pre-commit` and `handoff` as person only were proposed last and not yet confirmed: confirm before merge.
