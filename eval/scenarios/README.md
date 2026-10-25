# scenario tests

the kit for ticket `arkan-flow` 19: run arkan, unattended, on planted scenarios in a sandbox repo, and score each run against a sheet the run never sees.

## build the sandbox

`eval/scenarios/build.sh build <destination>` writes a fresh sandbox repo from `sandbox/history.bundle` and arkan's committed `skills/` tree at `HEAD`. it refuses a destination that is not empty, a destination inside the arkan checkout, or a dirty `skills/`.

```sh
eval/scenarios/build.sh build /tmp/arkan-sandbox
```

the seed bundle holds two branches: `main` at `294acb1` and `pre-break` at `af4922b`. the build checks both shas, then writes exactly two branches: `main`, and `agent/pre-break` from the seed's `pre-break`. it adds one rebuild commit on each, plants the two sandbox workflows, puts arkan's skills in `.claude/skills/`, replaces the two old board scripts with a `scripts/board.sh` symlink to `../.claude/skills/pre-setup/scripts/board.sh`, regenerates `TODO.md` on both branches, and validates:

- `agent/pre-break` prints `ok` from `scripts/check.sh`;
- `main` fails `test_parses_one_decimal_place_as_tens_of_cents`, the planted post-merge break;
- `.claude/skills/` is byte-identical to arkan's `HEAD:skills` tree;
- neither branch has `ANSWERS.md` or an old board script.

the same inputs give the same branch tips and trees.

`build.sh refresh <checkout> [base]` replaces only `.claude/skills/` on a new `agent/refresh-skills-<arkan-sha>-<base-sha>` branch, pushes it with `agent-gh push`, and opens its pull request with `agent-gh pr-create`. `base` defaults to `agent/pre-break`. it fetches and compares against `origin/<base>`, and refuses a dirty checkout, a dirty `skills/`, or a change outside `.claude/skills/`. if the remote branch already exists at the same commit, it skips the push; at another commit, it refuses to force. a nonzero exit from either broker call ends the refresh with exit 2. after a failed push, no pull request is requested. after a failed `pr-create`, the error names the branch and the head sha the broker verified on the remote, and says the pr state is unknown. either failure removes the temporary worktree, temp root and local branch. a retry at the same arkan and base shas makes the same commit and skips the push. a moved base gives a new branch. the broker must allow the target repository; its base rule accepts `main`, `master`, `agent/*` and `claude/*`.

## the sandbox

the public reference is still [`IsrafilEMIN/arkan-sandbox`](https://github.com/IsrafilEMIN/arkan-sandbox): `stock`, a small stdlib-only python inventory cli with tests, set up the way `pre-setup` would (local-markdown tracker, triage labels, `GLOSSARY.md`, `CODING_STANDARDS.md`, the generated board) and arkan's skills in `.claude/skills/`. its tickets are written like a real user's and never hint at the trap. it was built by hand, before this kit, so it still has `pre-break` and no `agent/pre-break`. the driver and `refresh` need a rebuilt sandbox's `agent/pre-break`.

- **branches.** `agent/pre-break` is the clean start for every scenario but one. `main` holds a planted bad merge for the `post-merge` scenario, so its tests fail on purpose. each run gets its own trunk, `agent/run-<name>`, pushed from its start ref, so one run's merges never touch another's.
- **ci.** [`sandbox/check.yml`](sandbox/check.yml) runs `scripts/check.sh` on each push and pr. arkan's [`ci/github/arkan-review.yml`](../../ci/github/arkan-review.yml) reviews each push; in the sandbox it runs on sonnet 5.5, so the owner's pro plan lasts a whole round.
- **the merge gate.** [`sandbox/auto-merge.yml`](sandbox/auto-merge.yml) merges a pr once every check on its head passed and a review on that same commit, from an author association of `OWNER`, `MEMBER` or `COLLABORATOR`, begins with `PASS`. the fixture checks only that author association, not the reviewer's repo permission, so it does not prove write access. this sandbox uses the gate path, so no agent there calls a merge api; arkan's own repo uses the broker path instead. arkan ships the hardened gate, which also checks for write access, as [`ci/github/arkan-merge.yml`](../../ci/github/arkan-merge.yml).
- **branch rules.** one ruleset on `main`, `agent/pre-break` and `agent/run-*`: a pr is required, `check` must pass (add `arkan-review` too), no deletions, no force pushes, no bypass, and no status check on branch creation (so `run-one.sh` can push a new trunk). the hand-built public sandbox's ruleset still names `pre-break` and `run/**`.

## run it

```sh
RUN_ROUND=r2 eval/scenarios/driver.sh            # every scenario, one at a time
eval/scenarios/run-one.sh bug-r2 agent/pre-break "/arkan-mode do ticket value-report 01"
SANDBOX_REPO=/tmp/arkan-sandbox eval/scenarios/run-one.sh bug-local agent/pre-break "/arkan-mode do ticket value-report 01"
```

- each run is a fresh headless `claude -p` session in a fresh clone, with a narrow tool allowlist and `acceptEdits`, never `bypassPermissions`.
- `SANDBOX_REPO` selects the clone source. it defaults to the public sandbox; point it at a locally built one for a local run. a local sandbox has no GitHub CI or pull requests, so a full scored round uses a GitHub repository.
- `run-one.sh` tells the run only environment facts: its trunk, how to push and open, read and check prs, the ci jobs, how a verdict is posted, and that the owner is away. nothing about the scenario.
- `run-one.sh` chooses the broker route when `AGENT_SANDBOX=1`, or when `agent-gh` resolves and `${AGENT_GH_SOCKET:-$HOME/.agents/sandbox/broker/gh.sock}` is a socket. a guarded run stops if the client or socket is missing. on the broker route, it pushes the trunk with `agent-gh push`, allows `agent-gh` instead of `gh` and `curl`, and tells the run to make every push and pr call through the broker clients. `SANDBOX_REPO` must then be a GitHub repository that the broker allows. only an unguarded run with no offered broker uses `git push` and names the `gh api` rest endpoints, because the cloud proxy blocks the graphql api behind `gh pr ...`. the route is selected once for the tools, push and launch note.
- logs go to `$RUNS_DIR` (default `$TMPDIR/arkan-scenarios/runs`), outside this tree.

## score it

[`ANSWERS.md`](ANSWERS.md) holds, per scenario, the start prompt, the ref, what was planted and the gates that should hold. never copy it into the sandbox. record each run in ticket 19's comments, and turn each failure into a ticket.

## limits

- the public sandbox's `.claude/skills/` is a copy of arkan's skills from when it was built. run `build.sh refresh` to replace it before a round, or run a locally built sandbox.
- a fork pr and the post-merge revert's merge cannot run there: there is no fork, and `main` cannot take the merge workflows while its tests fail.
