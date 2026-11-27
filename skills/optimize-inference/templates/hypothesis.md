# Hypothesis card

Copy this to `hypotheses/<run-name>.md` and fill it in **before** the run (`SKILL.md` rule 11). Do not edit the decision rule after you see numbers. If you must change it, write a new card with a new run name and say why.

Stages: probe → opt-in build → A/B → stability gate → other gates. The stability gate (`SKILL.md` rule 6) is required to keep a change: its needles and soak run last in the candidate load, or in one gate-only load after ACCEPT. The other gates are only proposed; the user decides whether they run.

```markdown
# <run-name>  (<date, time from `date`>)

## Change
- One change: <e.g. split-K 1 → 4 in the decode down-projection GEMV>
- Derived from: <best config or kernel version, e.g. configs/best.json, kernels/gemv/v3>
- Deliberately not changed: <the things a reader might expect you also touched>
- Quality class: <same bits | rounding level | discrete decisions | lossy format | spec decoding, sampling | cache, batching, concurrency; see references/quality.md>
- Per-change quality evidence: <from the contract in THEORY.md, e.g. l0 hash on decode and verify rows>

## Why
- Root it targets: <root theory from THEORY.md and the symptoms it explains>
- Gap: <checked root gap, metric and depth bucket, now vs ceiling>
- Probe that checked it: <ablation or upper bound, ms per step, run name>
- Why this change should close part of the gap: <one or two sentences>

## Prediction
- Target metric: <e.g. c1_decode at d50>, expected <+x% or a range>. Pass the point value to `bench.py verdict --predicted PCT`.
- Mechanism metric: <what must move if the theory holds, e.g. step_ms, accept_len, bytes per step>. A win without movement there is REJECT/LOOK.
- Max gain vs bar: <probe upper bound> vs <bar from `bench.py noise`>. Below the bar: bundle, reduce noise, or skip.
- Watch for regressions: <other metrics and depth buckets, mem_peak_gib; reliability: failed requests, looping flag>
- Constraints still met: <context target, memory cap, quality class>. If one is not, the result is CONDITIONAL.

## Load plan
- Loads and ETA: <e.g. ctl + cand, 2 loads × 3 passes, ~25 min>
- Stability gate: needles at <C/2>, <C>; soak N = <N, or n/a>; lossless evidence: <l0 / l1, or n/a>; runs <last in cand load | gate-only load after ACCEPT>

## Proof it ran
- How we will show the new path ran in serving: <trace, counter, log line>
- Phases and ranks it must cover: <prefill / decode / verify; rank 0 and rank 1>

## Decision rule
- Accept if: <`bench.py verdict` ACCEPT on the target metric, mechanism metric moved, quality evidence passes, proof present, stability gate passes>
- Reject if: <...>
- BELOW_BAR: the user decides.

## Observation (optional)
- <anything seen during the run that the card did not predict>

## Result (fill in after)
- Runs: <ctl, cand, plus extra loads>
- `scripts/bench.py verdict` output: <ACCEPT / REJECT / REPEAT / BELOW_BAR, with its reasons>
- Mechanism metric: <moved or not>
- Quality evidence: <pass / fail, numbers>
- Proof: <what it showed>
- What it says about the theory: <confirmed / weakened / refuted; which symptoms stayed>
- Decision and reason: <ACCEPT / REJECT / CONDITIONAL / user decision; one line, copied to PLAN.md>
- Stability gate: <pass / fail: needles C/2, C; soak N or n/a>. A fail rejects with reason "stability gate".
- Other gates proposed: <which, or none>
```

For kernel versions, use the same card in `kernels/<name>/v<K>/hypothesis.md`. Add the shapes (M, K, N per phase and per card), the roofline numbers and the floor time from `references/kernel-work.md`.
