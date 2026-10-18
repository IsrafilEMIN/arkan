# 08: post-merge skill, run by hand

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 9

**What to build:** a `post-merge` skill. when a merged change breaks something, an agent with this skill fixes forward or reverts, asks which node should have caught it, and opens a ticket for the miss so a person can act on it (with `retro` if it needs a look back). in this ticket a person starts the skill; ticket 21 makes it start by itself.

**Blocked by:** 03

what post-merge does (from `docs/core-skills.md` node 9, now removed; see git history):

1. read the signals: ci on main, error logs or alerts the repo has, revert commits, incident issues.
2. tie a failure to the merge that caused it (the first bad commit on main).
3. make main safe: a revert pr, or a fix-forward pr, whichever is safer faster. a revert is always the fallback.
4. ask "which node should have caught this?" (review, prove, tier, ...).
5. open a ticket for the miss on the repo's tracker: the bad diff, the confirmed bug, the fix pr and the answer to step 4. (saving it as a reviewer eval case is parked with review in `.scratch/review-ci/spec.md`.)

what can start it: ticket 21.

pstack parts to draw from (read in pstack's `poteto-mode` on 2026-10-18; the playbooks now live in `skills/arkan-mode/playbooks/`):

- `playbooks/orchestrate.md`: "one retro watcher follows merged PRs for reverts, post-merge CI breaks, and orphaned follow-ups". the closest idea; it lives only inside a long orchestrate run.
- `playbooks/babysit.md` and `scripts/watch-pr/`: a watcher whose output drives each wake-up, under `/loop`, with no sleep loops; and "classify ci before any retrigger" (one retry, then it is real).
- `playbooks/shipping.md` step 4: read the pr back after a merge, because a merge command can report success when the queue only queued it.
- `playbooks/autopilot-full.md` step 6: an hourly `/loop` audit that re-reads its playbook and probes each agent by what it changed, not what it says.

none of these is a full post-merge skill, so arkan writes its own and uses these as parts.

- [x] a post-merge skill exists, with the 5 steps above
- [x] proof: in a throwaway local git repo, a planted bad merge on main, then one run of the skill, gives the first bad commit, a revert or fix commit on a branch, and a ticket for the miss. the person only starts the run.

## Comments

- 2026-10-18, owner: split. this ticket is the skill run by hand; the triggers (ci job, daily job, pre-setup offering them) are ticket 21.
- 2026-10-18, agent: built `skills/post-merge/` (`SKILL.md` and `agents/openai.yaml`). it is person-started (`disable-model-invocation: true`, `allow_implicit_invocation: false`). its steps 2 to 6 are the 5 steps above; step 1 reads the target repo's `docs/agents/issue-tracker.md` and finds the check that shows the break. `playbooks/orchestrate.md` and `playbooks/autopilot-full.md` are not in `skills/arkan-mode/playbooks/` (pstack's orchestrate and autopilot are not part of arkan yet), so the parts used come from `babysit.md` (classify ci: one fresh run, an identical second failure is real) and `shipping.md` step 4 (read the merge back).
- 2026-10-18, agent: proof, in a throwaway local repo under the session scratchpad (`t08/repo`, with a bare `t08/remote.git` as its origin). setup: `calc.sh` with `add`, `test.sh` checking `add 2 3 = 5`, and a local-markdown `docs/agents/issue-tracker.md`. main got four `--no-ff` merges named "pr #1" to "pr #4"; the planted bad one is pr #3 (`tidy add` changes `add` to `$1 + $2 + 1`, plus an unrelated `add div`), and pr #4 lands after it. then one run of the skill, step by step:
  1. tracker: local markdown; check: `./test.sh`.
  2. signals: no revert commits; `./test.sh` fails twice on main's head, so it is real, not flake.
  3. `git bisect start --first-parent main <root>` and `git bisect run ./test.sh` gave `05a7b7c Merge pull request #3 from refactor-add`. the check fails there and passes on its first parent `33fc52d`.
  4. branch `revert-pr-3`: `git revert -m 1 05a7b7c` gave `e6f1311`; `./test.sh` passes; pushed to the bare origin.
  5. node: prove. `test.sh` already covered `add` and fails on `9040b64 tidy add`, but nothing ran it before the merge.
  6. ticket: `.scratch/post-merge/issues/01-pr-3-broke-add.md` (role `needs-triage`) with the bad merge, the failing trace (`add 2 3` gives 6), the revert commit and the step 5 answer, committed on `revert-pr-3` as `7641ea0` and pushed.

  result: met. simulated: the "prs" are local `--no-ff` merges with pr-style messages, there is no forge, so no real pr was opened and `gh pr view` / `gh run list` were not run; there is no ci, so the "ci signal" is the local `./test.sh`; the agent that wrote the skill also ran it. the person's only input was the request to run it. found on the way: in a first try, pr #4 appended to the same file right after pr #3's lines and `git revert -m 1` conflicted. the skill does not say what to do when the revert conflicts; the proof repo was rebuilt with pr #4 in its own file.
