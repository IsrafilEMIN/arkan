# arkan

arkan is one bundle of agent skills for engineering work. a person shapes the work into tasks; `arkan-mode` takes one task and drives it to a merged, checked change. the words used here (task, shaping, spec, ticket, task loop, playbook, principle) are defined in [`GLOSSARY.md`](GLOSSARY.md).

## install

there is no install command yet (ticket `arkan-flow` 04). today, link or copy each folder in [`skills/`](skills/) into the folder your harness reads skills from. then run `/pre-setup` once in each repo where you use arkan: it sets up the issue tracker, the triage labels, the domain docs and the `TODO.md` board.

## the flow in one view

```
idea
 │   shaping: a person starts each step
 ├── grill-with-docs ───── the idea or its words are fuzzy
 ├── to-spec, to-tickets ─ the work is more than one task (wayfinder if the goal is unclear)
 │
═══ task ═══════════════ the smallest piece an agent can finish alone
 │   task loop: arkan-mode drives it
 0  arkan-mode ────────── checks it is a task, picks a playbook, applies the principles
 1  build + tdd ───────── diagnosing-bugs when something is broken
 2  prove ─────────────── tests, build, lint, and the repo's verify skill
 3  code-review ───────── in a fresh context, before the pr
 4  pr ────────────────── the opening-a-pr, babysit and shipping playbooks
```

above the task line, a person decides what to build. below it, the agent works alone and comes back to the person for approval and for any action that cannot be undone.

not built yet: review on each pr push in ci, merge approval by risk tier, and watching a change after it merges. they are parked in [`.scratch/review-ci/spec.md`](.scratch/review-ci/spec.md) and ticket `arkan-flow` 08.

## where the skills come from

| source | skills in arkan |
|---|---|
| [pstack](https://github.com/cursor/plugins/tree/182f2ce/pstack) by lauren tan, at commit `182f2ce` | `arkan-mode`: its playbooks are pstack's, with the cursor-only parts removed; its `SKILL.md` and `principles/` are rewrites of `poteto-mode` and the 24 principle skills |
| [mattpocock/skills](https://github.com/mattpocock/skills) by matt pocock, main branch | `code-review`, `codebase-design`, `diagnosing-bugs`, `domain-modeling`, `git-guardrails-claude-code`, `grill-with-docs`, `grilling`, `handoff`, `implement-spec`, `improve-codebase-architecture`, `pr`, `prototype`, `retro`, `setup-pre-commit`, `tdd`, `to-spec`, `to-tickets`, `triage`, `wait-what`, `wayfinder`, `wizard`, `writing-for-agents`, and `pre-setup` (from `setup-matt-pocock-skills`). some of them are changed. |
| [claude-code-security-review](https://github.com/anthropics/claude-code-security-review/tree/0c6a49f) by anthropic, at commit `0c6a49f` | `security-review`: a copy of `.claude/commands/security-review.md`, with the claude-code-only parts ported |
| not recorded | `assess`, `freeze`, `good-css`, `product-brief`, `simplest-path`, `symlink-first`, `test-to-break` |

all three sources use the mit license. [`NOTICE`](NOTICE) keeps their copyright notices and license text. `skills/pr/CREDITS.md` names one more source, for part of the `pr` skill.

## work on arkan itself

tickets live in `.scratch/<feature>/issues/`, and [`TODO.md`](TODO.md) is the board: one card per ticket. the rules are in [`docs/agents/`](docs/agents/).
