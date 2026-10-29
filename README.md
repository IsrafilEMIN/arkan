# arkan

arkan is one bundle of agent skills for engineering work. a person shapes the work into tasks; `arkan-mode` takes one task and drives it to a checked change.

## install

for omp, run `skills/pre-setup/scripts/setup.sh apply omp` from this checkout, or `/pre-setup`: it links each folder in [`skills/`](skills/) into omp's skills folder. for any other harness, link or copy each `skills/<name>` into the folder that harness reads skills from yourself. then run `/pre-setup` once in each repo where you use arkan: it sets up the issue tracker, the triage labels, the domain docs and the `TODO.md` board.

## the flow in one view

```
idea
 │   shaping: a person starts each step
 ├── grilling ──────────── the idea or its words are fuzzy
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

## sources

[`REFERENCE.md`](REFERENCE.md) lists where each skill comes from and the articles that shaped arkan. [`NOTICE`](NOTICE) keeps the license text of each source.
