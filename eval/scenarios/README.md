# scenario tests

the kit for ticket `arkan-flow` 19: run arkan, unattended, on planted scenarios in a sandbox repo, and score each run against a sheet the run never sees.

## the sandbox

[`IsrafilEMIN/arkan-sandbox`](https://github.com/IsrafilEMIN/arkan-sandbox), public: `stock`, a small stdlib-only python inventory cli with tests, set up the way `pre-setup` would (local-markdown tracker, triage labels, `GLOSSARY.md`, `CODING_STANDARDS.md`, the generated board) and arkan's skills in `.claude/skills/`. its tickets are written like a real user's and never hint at the trap.

- **branches.** `pre-break` is the clean start for every scenario but one. `main` holds a planted bad merge for the `post-merge` scenario, so its tests fail on purpose. each run gets its own trunk, `run/<name>`, pushed from its start ref, so one run's merges never touch another's.
- **ci.** [`sandbox/check.yml`](sandbox/check.yml) runs `scripts/check.sh` on each push and pr. arkan's [`ci/github/arkan-review.yml`](../../ci/github/arkan-review.yml) reviews each push; in the sandbox it runs on sonnet 5.5, so the owner's pro plan lasts a whole round.
- **the merge gate.** [`sandbox/auto-merge.yml`](sandbox/auto-merge.yml) merges a pr once every check on its head passed and a review on that same commit, from someone with write access, begins with `PASS`. this sandbox uses the gate path, so no agent there calls a merge api; arkan's own repo uses the broker path instead. arkan ships the hardened gate as [`ci/github/arkan-merge.yml`](../../ci/github/arkan-merge.yml).
- **branch rules.** one ruleset on `main`, `pre-break` and `run/**`: a pr is required, `check` must pass (add `arkan-review` too), no deletions, no force pushes, no bypass, and no status check on branch creation (so `run-one.sh` can push a new trunk).

## run it

```sh
RUN_ROUND=r2 eval/scenarios/driver.sh            # every scenario, one at a time
eval/scenarios/run-one.sh bug-r2 pre-break "/arkan-mode do ticket value-report 01"
```

- each run is a fresh headless `claude -p` session in a fresh clone, with a narrow tool allowlist and `acceptEdits`, never `bypassPermissions`.
- `run-one.sh` tells the run only environment facts: its trunk, the rest endpoints for prs (the cloud proxy blocks the graphql api behind `gh pr ...`), the ci jobs, how a verdict is posted, and that the owner is away. nothing about the scenario.
- logs go to `$RUNS_DIR` (default `$TMPDIR/arkan-scenarios/runs`), outside this tree.

## score it

[`ANSWERS.md`](ANSWERS.md) holds, per scenario, the start prompt, the ref, what was planted and the gates that should hold. never copy it into the sandbox. record each run in ticket 19's comments, and turn each failure into a ticket.

## limits

- the sandbox was built by hand in one session; rebuilding it from this folder is not scripted yet.
- the sandbox's `.claude/skills/` is a copy of arkan's skills from when it was built. refresh it before a round, or results test old skills.
- a fork pr and the post-merge revert's merge cannot run there: there is no fork, and `main` cannot take the merge workflows while its tests fail.
