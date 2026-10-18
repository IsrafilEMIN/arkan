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

 a spec with tickets: arkan-mode's spec playbook runs one task loop per
 #ready-for-agent ticket, in parallel, then one review and one pr
```

above the task line, a person decides what to build. below it, the agent works alone and comes back to the person for approval and for any action that cannot be undone.

after a merge breaks main, a person starts `post-merge`: it finds the first bad merge, reverts or fixes forward on a branch, and opens a ticket for the miss.

not built yet: merge approval by risk tier, and starting `post-merge` by itself when main breaks. they are parked in [`.scratch/review-ci/spec.md`](.scratch/review-ci/spec.md) and ticket `arkan-flow` 21.

## review in ci

[`ci/github/arkan-review.yml`](ci/github/arkan-review.yml) runs `code-review` and `security-review` on each push to an open pr, keeps the findings and the round count in one comment on the pr (a later push gets only its new commits reviewed, and round 4 asks for a rethink), and sets an `arkan-review` check that fails while an `important` or security finding is open. to add it to a repo:

1. put arkan's skills in the repo's `.claude/skills/` on the default branch.
2. add the repo secret `CLAUDE_CODE_OAUTH_TOKEN` (from `claude setup-token`), or `ANTHROPIC_API_KEY`.
3. copy the file to `.github/workflows/arkan-review.yml`, and make `arkan-review` a required check.

it skips docs-only prs and prs from forks, and says so on the pr. the details are in [`ci/README.md`](ci/README.md).

## where the skills come from

| source | skills in arkan |
|---|---|
| [pstack](https://github.com/cursor/plugins/tree/182f2ce/pstack) by lauren tan, at commit `182f2ce` | `arkan-mode`: its playbooks are pstack's, with the cursor-only parts removed; its `SKILL.md` and `principles/` are rewrites of `poteto-mode` and the 24 principle skills |
| [mattpocock/skills](https://github.com/mattpocock/skills) by matt pocock, main branch | `code-review`, `codebase-design`, `diagnosing-bugs`, `domain-modeling`, `git-guardrails-claude-code`, `grill-with-docs`, `grilling`, `handoff`, `improve-codebase-architecture`, `pr`, `prototype`, `retro`, `setup-pre-commit`, `tdd`, `to-spec`, `to-tickets`, `triage`, `wait-what`, `wayfinder`, `wizard`, `writing-for-agents`, `pre-setup` (from `setup-matt-pocock-skills`), and `arkan-mode`'s spec playbook (from `implement-spec`). some of them are changed. |
| [claude-code-security-review](https://github.com/anthropics/claude-code-security-review/tree/0c6a49f) by anthropic, at commit `0c6a49f` | `security-review`: a copy of `.claude/commands/security-review.md`, with the claude-code-only parts ported |
| written for arkan | `post-merge`, with parts from pstack's babysit and shipping playbooks |
| not recorded | `assess`, `freeze`, `good-css`, `product-brief`, `simplest-path`, `symlink-first`, `test-to-break` |

all three sources use the mit license. [`NOTICE`](NOTICE) keeps their copyright notices and license text. `skills/pr/CREDITS.md` names one more source, for part of the `pr` skill.

## work on arkan itself

tickets live in `.scratch/<feature>/issues/`, and [`TODO.md`](TODO.md) is the board: one card per ticket. the rules are in [`docs/agents/`](docs/agents/). [`eval/scenarios/`](eval/scenarios/) runs arkan unattended on planted scenarios in a sandbox repo and scores each run.
