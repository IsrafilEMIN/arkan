---
name: arena
description: "Run N candidates at the same task in parallel, pick a base, and graft the strongest parts of the others into it. Use for /arena, 'arena this', 'throw it in the arena', or when one attempt at a non-trivial artifact would lock in the wrong shape."
---

# Arena

Open a todo list with one entry per phase (frame, fan out, cross-judge, pick, graft, verify) before launching anything.

`architect` uses arena for design sketches; `blast-radius` uses it for a wide change. Use it on its own for any artifact where one attempt would lock in the wrong shape.

## Phase A: frame

Every candidate gets the same prompt, so the prompt is the contract.

1. State the artifact each candidate produces.
2. Write the rubric: 3 to 6 concrete, gradeable criteria for success on this task. It is your tool in phase D; candidates only see the task.
3. **Pick the runners.** Two is the default. Where the harness lets you pick a model per subagent, put the runners on different model families: different models make different mistakes, and that is the point. Where it does not, run each candidate on the current model in its own fresh context, and say so in the synthesis note. If the harness refuses a model, use the closest one it accepts and say so. Add runners when the arena covers several design directions; use the same model several times when the work is generation-bound rather than judgment-bound.
4. Give each candidate its own output place: a git worktree where possible, else `.scratch/arena-<slug>/candidate-<n>/`, per **separate before you serialize shared state** (`principle-separate-before-serializing-shared-state`).

## Phase B: fan out

Spawn all N subagents at once, in the background where the harness allows. Each gets the task, the path to the shared grounding, its own output path, and an instruction to produce the artifact and a short rationale naming the alternatives it considered and rejected.

If a candidate produces nothing, go on with N-1 and note the dropout.

## Phase C: cross-judge

After every candidate has finished, spawn one read-only judge subagent, on a different model family from yours where the harness allows. It sees the rubric and the candidates by path label, scores each criterion, and recommends a base with its reasons. It runs while you read in phase D. Never spawn it while candidates are still writing.

## Phase D: pick a base

Read every candidate end to end before picking. Score each against the rubric criterion by criterion, not on overall feel, and compare with the judge. Agreement on the base confirms the pick. Disagreement means one of you is biased or the rubric was ambiguous: read both rationales before deciding.

Pick the base a future maintainer can extend most easily without breaking its invariants. When two feel tied, prefer the cleaner boundary or the smaller api, per the **laziness protocol** (`principle-laziness-protocol`).

## Phase E: graft

Walk each losing candidate once more for what is worth porting into the base, usually one or two things per candidate, not most of it. Fold each graft in by hand, per **redesign from first principles** (`principle-redesign-from-first-principles`), so the result keeps one mental model. Don't paste mechanically.

If the candidates converge on one shape, that is strong agreement: note it and ship the shared shape, no graft needed. If they diverge wildly, phase A was under-specified: reframe and re-run instead of averaging.

## Phase F: verify

Verify the synthesized artifact like any other output, per **prove it works** (`principle-prove-it-works`). If verification finds a problem the arena missed, either phase A was wrong (reframe and re-run) or a candidate caught it and you missed the graft (go back to phase E). Don't paper over it.

## Outputs

One synthesized artifact, with a short synthesis note beside it: the base and why, the judge's verdict, each graft and its source candidate, what was rejected and why, any convergence or dropouts, which models ran (or "same model, fresh contexts"), and the verification result. Delete the candidate worktrees or `.scratch/arena-*` folders once the note is written.
