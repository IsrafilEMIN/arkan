# Quality

A speed change is only a win if it keeps the quality the user allowed. This file defines the lossless levels, the
quality contract you write before a round, the metrics, the dump formats and `scripts/quality.py`.

## Levels

### l0, exact

Bit-identical output.

- Evidence: a full-vocab logit fingerprint (one hash per row), switch off vs on, on one binary.
- Cover every path the change touches: decode, batched prefill, verify rows including rejected drafts, appends on a
  cached prefix, each depth bucket, concurrency.
- Free-running answers must also match.
- l0 proves "no change". It does not measure quality.

### l1, rounding level

Not bit-identical, but the difference is the size of rounding noise.

- Per-step FULL-VOCAB KL, and TV when sampling is truncated by top-k or top-p, on control trajectories at the served
  sampling settings, per depth bucket.
- Compare against the floor measured on the rig: control vs a second valid reduction order, with routing replayed.
  The candidate must stay within a margin of the floor that you set before the run.
- Test: paired non-inferiority with a block bootstrap by sequence. Report median, p99 and max (a mean hides tails).
- Optional oracle check: `d_t = KL(fp32||cand)_t - KL(fp32||ctl)_t`; pass when the upper CI < delta. Never use a
  strict "<=": with rounding noise that is a coin flip.
- Direction: paired dNLL of the true next token on held-out REAL text, with a TOST equivalence test and a margin set
  before the run. On the control's own tokens dNLL equals KL and has no direction. "Not significant" never proves
  equivalence.

### l2, lossy

A labelled trade. Report dNLL ± CI, KL quantiles vs the reference, paired evals (matched ids, McNemar), needles and
long sessions.

### Rules for all levels

- Truncated vocabulary (top-64 dumps, "other" bins) UNDERESTIMATES KL (data-processing inequality). It is never l1
  evidence. Use full-vocab logits or in-engine full-vocab KL/TV per row.
- No sequence-level TV or Pinsker certificate as a gate. At served lengths it is vacuous even for pure rounding noise:
  a floor KL of 0.0006/token over 1,000 tokens gives TV <= 0.55.
- Routing and sampling changes also need long real agent sessions with loop flags and paired task results. A change
  that was small per token caused repetition loops in long agent sessions (4.5 vs 5.6 of 10 tasks).
- Task evals catch breakage. They are too weak to prove a small loss absent (61 items is about ±8 points).

## Quality contract

Write it in `THEORY.md` before the first run of a round. Each planned change gets a class, its per-change evidence and
a margin. Per change, collect only the cheap evidence. The stability gate (`SKILL.md` rule 6: needles at C/2 and C, a
soak if sized for N users, the per-change evidence if the change claims l0 or l1) is always required, for every class.
The end-of-round column lists what is proposed on top of it; the user decides.

| change class | example | per-change evidence | end of round, on top of the stability gate (proposed; user decides) |
|---|---|---|---|
| same bits | layout, schedule, fusion | l0 hash on touched paths | none extra |
| rounding level | summation order, chunk size, accumulation dtype | routing REPLAYED; per-step full-vocab KL/TV vs floor per depth bucket; dNLL equivalence | needles at every depth bucket, multi-turn, thinking on/off |
| discrete decisions | router dtype, expert skip, top-k | FREE routing, on-policy at served settings: expert-set agreement + resulting KL/TV and dNLL vs floor | long agent sessions with loop flags, paired tasks |
| lossy format | quant, int8 KV, fp8 prefill | dNLL ± CI, KL quantiles vs reference | full suite, needles at every depth bucket, long sessions |
| spec decoding, sampling | draft length, verify kernel | l0 on verify logits; target distribution unchanged | none extra |
| cache, batching, concurrency | prefix cache, lanes | l0 or l1 on cached appends, together vs alone | multi-turn switching, N streams |

- Margin from the measured floor. Example: the upper CI of the candidate's median per-step KL <= 2 × the floor's;
  a dNLL margin in nats/token.
- Sample size from a pilot of the floor: `n = (z*sigma/(delta/2))^2` sequences (`quality.py size`). Bootstrap by
  sequence.
- Storage: fp16 full logits for a fixed subset of positions. At a 150K vocabulary that is ~0.3 MB per row; 10K rows
  are ~3 GB.

## Answer identity and the determinism check

- Prompt prefixes come from (seed, pass, prompt index), not the clock, so control and candidate see the same prompts
  per pass (`references/logging.md`). On a reused server (`--reuse` or an attached server) they stay identical only
  with a rig `cache_bypass` of `request_field` or `flush_cmd`; otherwise the prompts differ, the verdict is unpaired,
  and `ANSWER_DIFF` is not available.
- `ANSWER_DIFF`: a verdict flag (in `verdicts.jsonl`, not the ledger) when the candidate claims l0 (config
  `"claims": "l0"`), the control is known deterministic (`--determinism`), and a greedy answer differs from the
  control's on the same prompt AND the same compute path (batch size, chunk, cache state cold/warm/bypass). Other
  pairs are logged, not judged.
- Determinism check first (`bench.py run --determinism`): the control must give the same answers twice by the same
  path, with the cache bypassed by whatever the rig supports (`rig.json` `cache_bypass`):
  - `request_field`: a per-request no-cache field, e.g. llama.cpp `"cache_prompt": false`;
  - `flush_cmd`: a flush command between sends;
  - `reload`: a second control load.
- If the answers still differ, `ANSWER_DIFF` turns off for that rig and engine (the ledger records why), bit claims
  move to the teacher-forced logit check of l0/l1, and the report says answer identity was not available.

## Dump formats

Engine hooks write these; `quality.py` reads them.

- Full-logit dump dir: `index.jsonl` rows `{"prompt_id", "pos", "depth", "file", "offset", "vocab", "dtype": "f16|f32"}`
  plus raw little-endian binary files (vocab values at file + offset). Each row declares the full vocabulary size in
  `"full_vocab"`, or you pass `--vocab N`; `dist`, `oracle` and `size` exit 2 without it. Rows match across dirs by
  (prompt_id, pos).
- Fingerprints (l0): `fingerprints.jsonl` rows `{"prompt_id", "pos", "phase", "sha"}`; or `output_sha12` in
  `requests.jsonl`.
- True-token logprobs (dNLL): `{"prompt_id", "pos", "token_id", "logprob"}`, teacher-forced on held-out real text.
- Experts: `{"prompt_id", "pos", "layer", "ids": [...]}`.
- Paired tasks: `{"id", "pass": bool}`.

## scripts/quality.py

numpy is required, except for `l0` and `mcnemar`. The full usage is the module-level `USAGE` string; `-h`/`--help`
prints it and exits 0.

```
python3 scripts/quality.py l0 A_DIR B_DIR                      # fingerprint or output-sha compare, first differing row
python3 scripts/quality.py dist REF_DIR CAND_DIR [--floor FA_DIR FB_DIR] [--margin-ratio 2] [SAMPLING] [--buckets 0,8192,32768]
python3 scripts/quality.py oracle ORACLE_DIR CTL_DIR CAND_DIR --delta D [SAMPLING] [--buckets ...]
python3 scripts/quality.py dnll CTL.jsonl CAND.jsonl --margin NATS
python3 scripts/quality.py experts REF.jsonl CAND.jsonl [--floor FA.jsonl FB.jsonl] [--margin-ratio 2]
python3 scripts/quality.py size FA_DIR FB_DIR --delta D [--z 1.645] [SAMPLING]
python3 scripts/quality.py mcnemar A.jsonl B.jsonl
```

- SAMPLING: `--temperature T` (default 1, > 0), `--top-k K` (0 = off), `--top-p P` (1 = off). The default order is
  temperature, top-k, top-p (vLLM, HF); `--temp-last` applies temperature last (llama.cpp sampler chain).
- Common options: `--boot B` (bootstrap resamples, default 2000), `--seed S` (default 0), `--min-prompts N` (default 5;
  a bucket with fewer prompts is LOW_N and fails), `--vocab N` (the declared full vocabulary size; required by `dist`,
  `oracle` and `size` when the rows carry no `full_vocab`). Rows with a smaller vocab, or with `topk`/`other` fields,
  are refused as truncated.
- Buckets: depth edges, e.g. `0,8192,32768` gives [0,8192) [8192,32768) [32768,inf); without `--buckets` only "all".
- Statistics: block bootstrap by prompt_id (sequence); 90% two-sided for TOST, one-sided 95% for non-inferiority.
- `dist` reports median, p99 and max of per-step KL and TV per depth bucket, the share of infinite KL, the argmax flip
  rate, the near-tie share (top-2 gap below the floor's p99 logit noise) and the flips that are not near ties.
  With `--floor` it gates: the one-sided 95% upper bound of median(cand) − margin_ratio × median(floor) must be <= 0
  in every bucket and in "all".
- With top-k or top-p, KL can be infinite: the gate statistic is TV, and `dist` says KL is undefined there.
- `oracle` gates on the "all" row (95% upper bound of mean d < delta); its buckets are for information only.
- `experts` reports per-layer mean Jaccard and exact-set share. With `--floor` it gates disagreement (1 − Jaccard)
  the same way `dist` does, on the mean.
- `size` prints the raw n and n clamped to at least `--min-prompts`; use the clamped n.
- `mcnemar` FAILs when p < 0.05 and B is worse; otherwise it prints REPORT: no loss detected, which is not
  equivalence (read the CI).
- Exit codes: 0 PASS or REPORT, 1 FAIL, 2 usage or data error. REPORT means numbers only, no gate: `dist` and
  `experts` without `--floor`, `size`, and a non-significant `mcnemar`. Output: a one-line verdict plus a small table.
