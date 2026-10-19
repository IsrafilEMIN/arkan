---
name: swarm
description: "Fan out N parallel workers, drain them, and return one report. Use for /swarm, 'swarm this', or parallel coverage, races, gauntlets and exploration."
---

# Swarm

Where `arena` makes N versions of one artifact and merges them, swarm splits work across N workers (or races them) and returns one report. `maintain-verification`'s source wave is a swarm.

## Start

Open a todo list with one entry per phase before launching anything: 1 frame, 2 fan out, 3 aggregate, 4 report.

## Phase A: frame

1. State the done predicate, and the artifact or report the swarm returns.
2. Choose the shape: split the work into slices, race N workers on the same brief, or mix both. For a race or a mix, declare `first pass`, `rank all` or `best-of` before spawning.
3. Pick the worker model. A fast model suits most slices. For a model race, name each arm's model up front. Where the harness does not let you pick models, every worker runs on the current model; say so in the report.
4. Give each worker its own writable output when it writes (its own worktree or `.scratch/swarm-<slug>/worker-<n>/`). When workers verify or measure commits, each brief names the exact shas. A measurement brief also names the method (sample count, what one sample is, order), and the worker records both in its result; for performance numbers, use `benchmark-checklist`.

## Phase B: fan out

Spawn all N workers at once, in the background where the harness allows. Use workers that run where the work is: in the cloud when the harness offers it and the work needs nothing from the person's machine, on the machine (under its sandbox) when it does.

Every brief stands alone: the goal, the scope, the exact slice or race arm, how to verify, and what to report. Reports use `PASS`, `ISSUES` or `BLOCKED`, with evidence. A worker that can prove a defect reports `ISSUES` and lists every issue it can prove, not only the first.

Workers never push, open pull requests or merge: they report. The coordinator alone acts on the results, through the repo's normal flow.

If a worker drops out, go on with N-1 and note it.

## Phase C: aggregate

Read the final results. Drop a result that does not record the shas and the method its brief names, and respawn that worker once; after a second miss, record a gap. A gap never counts as a pass. For coverage, every required slice needs a result. For a race, apply the rule declared up front. Do not paste raw worker output.

## Phase D: report

Return one report in the chat: a table (slice or arm, result, evidence), one line per issue, gaps and dropouts, and the race rule when one was used. Turn each proven issue that is not this task's work into a ticket on the repo's tracker.
