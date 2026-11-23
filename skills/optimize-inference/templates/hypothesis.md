# Hypothesis card

Copy this to `hypotheses/<run-name>.md` and fill it in **before** the run (`SKILL.md` rule 11). Do not edit the decision rule after you see numbers. If you must change it, write a new card with a new run name and say why.

```markdown
# <run-name>  (<date, time>)

## Change
- One change: <e.g. split-K 1 → 4 in the decode down-projection GEMV>
- Derived from: <best config or kernel version, e.g. configs/best.json, kernels/gemv/v3>
- Deliberately not changed: <the things a reader might expect you also touched>

## Why
- Gap it targets: <metric, now vs ceiling, from THEORY.md>
- Evidence: <profile line, roofline numbers, or earlier result in PLAN.md>
- Why this change should close part of the gap: <one or two sentences>

## Prediction
- Target metric: <e.g. c1_decode>, expected <+x% or a range>
- Watch for regressions: <other metrics, e.g. prefill_32768, mem_peak_gib, accuracy>
- Lossless? <yes: greedy-equivalence check planned | no: labelled lossy trade, which quality gate>

## Proof it ran
- How we will show the new path ran in serving: <trace, counter, log line>
- Phases and ranks it must cover: <prefill / decode / verify; rank 0 and rank 1>

## Decision rule
- Accept if: <beats both controls on the target metric; nothing worse than 3%; proof present>
- Reject if: <...>
- Repeat if: <win above ~10%, or the controls differ by more than 5%>

## Result (fill in after)
- Runs: <ctl-a, cand, ctl-b, plus repeats>
- `bench.py verdict` output: <ACCEPT / REJECT / REPEAT, with its reasons>
- Proof: <what it showed>
- Decision and reason: <one line, copied to PLAN.md>
```

For kernel versions, use the same card in `kernels/<name>/v<K>/hypothesis.md`. Add the shapes (M, K, N per phase and per card), the roofline numbers and the floor time from `references/kernel-work.md`.
