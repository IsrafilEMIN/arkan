# arkan

arkan is one bundle of agent skills for engineering work. a person hands it one task; `arkan-mode` drives that task to a checked change.

## install

arkan is a plugin for omp and claude code. in omp:

```
/marketplace add IsrafilEMIN/arkan
/marketplace install arkan@arkan
/reload-plugins
```

in claude code:

```
/plugin marketplace add IsrafilEMIN/arkan
/plugin install arkan@arkan
```

to update in omp, run `/marketplace update arkan`, then `/marketplace upgrade arkan@arkan`, then `/reload-plugins`.

for any other harness, link or copy each folder in [`skills/`](skills/) into the folder it reads skills from.

## the flow in one view

```
task
 │
 0  arkan-mode ────────── picks a playbook, applies the principles
 1  build ─────────────── the bug-fix playbook when something is broken, `tdd` when a test is cheap
 2  prove ─────────────── tests, build, lint, and the repo's verify skill
 3  pr ────────────────── the opening-a-pr and babysit playbooks
 4  review ────────────── reviewer sessions run `interrogate` on the pr head and record a verdict
 5  merge ─────────────── the shipping playbook, once the broker's merge rule passes
```

a person hands over the task. the agent works alone from there and comes back to the person for approval and for any action that cannot be undone.

## sources

[`NOTICE`](NOTICE) lists the project each copied skill comes from and keeps the license text of each source. [`docs/resources/`](docs/resources/) has one file for each article that shaped arkan.
