# arkan

arkan is one bundle of agent skills for engineering work. a person hands it one task; `arkan-mode` drives that task to a checked change.

## install

link or copy each folder in [`skills/`](skills/) into the folder your harness reads skills from.

## the flow in one view

```
task
 │
 0  arkan-mode ────────── picks a playbook, applies the principles
 1  build ─────────────── the bug-fix playbook when something is broken, `tdd` when a test is cheap
 2  prove ─────────────── tests, build, lint, and the repo's verify skill
 3  pr ────────────────── the opening-a-pr, babysit and shipping playbooks
 4  review ────────────── reviewer sessions run `interrogate` on the pr head; gh-broker's merge rule gates the merge
```

a person hands over the task. the agent works alone from there and comes back to the person for approval and for any action that cannot be undone.

## sources

[`REFERENCE.md`](REFERENCE.md) lists where each skill comes from and the articles that shaped arkan. [`NOTICE`](NOTICE) keeps the license text of each source.
