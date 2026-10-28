# arkan

arkan is one bundle of agent skills for engineering work. a person shapes the work into tasks; `arkan-mode` takes one task and drives it to a checked change.

## install

in claude code 2.1.275 or later, install the bundle as a plugin with `/plugin install arkan --marketplace IsrafilEMIN/arkan`; the manifests are in [`.claude-plugin/`](.claude-plugin/). for other harnesses, link or copy each folder in [`skills/`](skills/) into the folder your harness reads skills from. then run `/pre-setup` once in each repo where you use arkan: it sets up the issue tracker, the triage labels, the domain docs and the `TODO.md` board.

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

## where the skills come from

| source | skills in arkan |
|---|---|
| [pstack](https://github.com/cursor/plugins/tree/182f2ce/pstack) by lauren tan, at commit `182f2ce` | `arkan-mode`: its playbooks are pstack's, with the cursor-only parts removed; its `SKILL.md` is a rewrite of `poteto-mode`. the 24 `principle-*` skills are copies of pstack's, adapted; `principle-test-behavior-not-implementation` also carries `arkan-mode`'s failing-shape list |
| [mattpocock/skills](https://github.com/mattpocock/skills) by matt pocock, main branch | `code-review`, `codebase-design`, `diagnosing-bugs`, `domain-modeling`, `grill-with-docs`, `grilling`, `handoff`, `prototype`, `retro`, `setup-pre-commit`, `tdd`, `to-spec`, `to-tickets`, `triage`, `wait-what`, `wayfinder`, `writing-for-agents`, `pre-setup` (from `setup-matt-pocock-skills`), and `arkan-mode`'s spec playbook (from `implement-spec`). some of them are changed. |
| [claude-code-security-review](https://github.com/anthropics/claude-code-security-review/tree/0c6a49f) by anthropic, at commit `0c6a49f` | `security-review`: a copy of `.claude/commands/security-review.md`, with the claude-code-only parts ported |
| [pstack](https://github.com/cursor/plugins/tree/d457567/pstack) by lauren tan, at commit `d457567` | `create-verification` (from `create-verification-skill`) and `maintain-verification` (from `maintain-verification-skill`), ported to arkan's repo-local skill path and sandbox limits; `blast-radius`, `interrogate`, `architect`, `arena`, `swarm`, `figure-it-out`, `benchmark-checklist`, `unslop`, `technical-writing`, `no-comments` (with its comment-sicko agent as a reference prompt), `show-me-your-work`, `how`, `why`, `teach`, `in-your-own-words`, `sharpen`, `recall`, `reflect`, `correct`, `ketchup`, `bro`, `automate-me`, `typescript-best-practices`, `make-bot-ui`, `create-formal-verification`, `maintain-formal-verification`, ported to arkan-mode's principles and playbooks, with transcript paths per harness and the repo's own tracker as an evidence source, with cursor's model config replaced by "different model families where the harness allows" |
| written for arkan | `post-merge`, with parts from pstack's babysit and shipping playbooks |
| not recorded | `assess`, `good-css`, `simplest-path`, `symlink-first`, `test-to-break` |

all three sources use the mit license. [`NOTICE`](NOTICE) keeps their copyright notices and license text.
