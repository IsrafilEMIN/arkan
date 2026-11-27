# Measurement methodology

Most "wins" and "regressions" in inference tuning are measurement errors. In every case below, a check like this changed a conclusion.

## Counting

- **Count tokens with the tokenizer or the server's usage stats, not streamed chunks.** With speculative decoding, engines emit several tokens per SSE chunk; counting chunks under-reported MTP decode. Use `stream_options: {include_usage: true}` or `continuous_usage_stats`, or re-tokenize the output.
- **Size prompts with the real tokenizer.** Tokens per word differ by model and text: ratios of 1.08 and 3.5 were seen, and "random word" documents at ~3.5 tokens per word turned nominal "32K/128K" cells into 58K/232K. `bench.py` calibrates tokens per word once per run from the server's `prompt_tokens`, then scales documents to it.
- **Build prompts before the clock starts.** `bench.py` seeds each prompt prefix from (seed, pass, prompt id): `[run-seed S pass P prompt ID]`. Control and candidate get the same prompts in the same pass; passes inside one load get different prefixes, so the prefix cache cannot hit. A warm-cache test repeats a prompt on purpose, as its own test.
- **Reused servers keep prompts paired only with a cache bypass.** With `--reuse` or an attached server, the prefixes stay identical between ctl and cand only when `rig.json` `cache_bypass` is `request_field` or `flush_cmd`, applied to every timed request (`path.cache = "bypass"`). Without one, the pass numbers continue from `.bench-server.json` so no prompt repeats on the same server; `verdict` is then unpaired (per-pass samples) and `ANSWER_DIFF` is not available.
- **Decode tok/s:** completion tokens after the first token ÷ time since the first token.
- **Prefill tok/s:** prompt tokens ÷ TTFT on a cold prompt. Report cold and warm (cache-hit) separately; never publish a cache-hit prefill as prefill. Check `cached_tokens` in `requests.jsonl`.
- **Concurrent throughput (cN):** total completion tokens across N streams ÷ wall time from first start to last finish. Per-stream sums overstate it when streams don't overlap. Verify the server actually ran N at once (`max_running`, state slots).

## Noise

Sources of run-to-run noise:

- thermals and clocks;
- power source (a laptop on battery or a balanced profile ran 8–10% slower). `rig.json` `checks.on_ac` blocks runs on battery by default and flags `ON_BATTERY` (`rig.md`);
- background CPU load (a laptop RTX 4080 went 107 → 75 tok/s under light CPU load);
- allocator state, JIT and graph capture, which differ per load;
- prompt content, because acceptance depends on text type. Use the fixed, seeded prompt panel; random prompts moved acceptance from 2.4 to 3.7 and made c1 comparisons pure noise.

### Calibrate the noise

- **Calibrate at the start** and after a driver, power-cap or engine-build change: run the control as several loads, each with several passes.
- **Keep updating from every control-config run in the ledger.** `python3 scripts/bench.py noise` prints the pooled SDs per config hash and metric over the last `rig.json` `noise.window` rows (default 20):
  - `sd_within`: pooled SD between passes of one load (df = sum of passes − 1 over loads);
  - `sd_load`: SD of the load means between loads.
- **Pool the SD; never use max − min.** The range grows with the number of runs, so it widens the bar every time you add a control.
- **Calibrated** means the control's config hash has at least `noise.min_loads` ok loads (default 3) and within-load df of at least `noise.min_df` (default 4).

### The verdict statistics

The gain `g` (%, positive = better) is paired: per prompt, the ratio candidate ÷ control in the same pass, as a geometric mean over prompts, plus total tokens ÷ total time. Never use the median of a mixed panel: short and long prompts, or code and prose, have different speeds. Metrics without per-prompt data, and unpaired prompts, use per-pass samples.

```
L_ctl, L_cand = number of control and candidate loads
t        = t(0.975, df = control loads in the noise window − 1) / 1.96   # 3 loads: ×2.19, 6: ×1.31, >30: ×1
bar      = max(k × t × sd_load × sqrt(1/L_ctl + 1/L_cand), floor_pct)        # k = noise.k, default 2.5
se_total = sqrt(se_prompt² + sd_load² × (1/L_ctl + 1/L_cand))               # se_prompt = bootstrap SD over prompts
lower    = g − 1.96 × t × se_total                                         # CI = g ± 1.96 × t × se_total
drift    = newest control load vs the mean of the other control loads in the window;
           REPEAT if |x − mean| > max(k × sd_load × sqrt(1 + 1/(L − 1)), floor_pct)
trend    = first vs last pass of a load in the window;
           REPEAT if above max(k × sqrt(2) × sd_within, floor_pct)
```

- **More passes cannot push the bar below the between-load term.** The bar and `se_total` shrink with the number of loads, not passes. Plan loads, not only passes. With only a few control loads, `sd_load` itself is uncertain, so the Student-t factor `t` widens the bar and the CI until more control loads build up in the ledger.
- **The window** is the selected candidate loads plus the control loads from the last control load before the first selected candidate load onward. Drift, trend and `HOST_BUSY` look only there; older flagged loads are ignored.
- **Surprise:** give the card's prediction with `--predicted PCT`. `verdict` asks for a REPEAT when `g > --surprise-ratio` (default 2) × PCT and the candidate has fewer than 2 loads. Without `--predicted`, the fallback is a REPEAT when `g > 10%` and the candidate has only 1 load.
- **Uncalibrated:** bar 3%, drift and trend 5%, `se_total = se_prompt` (the CI is prompt-only); the verdict is marked "uncalibrated". An uncalibrated pair verdict is never ACCEPT or BELOW_BAR: it asks for more control loads, or use the triple mode.
- **Watch-only verdict flags:** `NOISY` (per-pass SD above the bar) and `LOW_N` (ledger flag: fewer than `noise.min_samples` c1 samples or fewer than `noise.min_tokens` tokens per sample; defaults 6 and 64). They never decide.
- **`HOST_BUSY`** is a ledger flag (CPU or disk above the idle baseline in the timed window). It makes a verdict REPEAT only when it is on a run in the window.
- **Comparing engines:** same card, same day, back to back, same statistic. Accept "B is faster" only if the lower CI bound of the paired gain is above 0.
- Discard cold first runs and the first boot after a JIT cache miss (36 vs 90 tok/s on one vLLM boot).
- Microbenchmarks need interleaved min-of-N timing; clock ramp-up made one kernel look 2.5× slower than it was.

## Loads

A load is the costly, noisy step: weight load, JIT and graph capture, allocator state. Count loads, not tests.

- **List every test for the experiment before the first run** and put them in the config's `tests` list, so they run in the same load:
  - built-in timing;
  - the depth buckets the card predicts a gain in (next section);
  - the quality evidence for the change's class (`quality.md`);
  - proof (`"proof"`).
  A failed test flags `TEST_FAIL`. Keep the same order in every load: position in the load changes thermals and cache state.
- **The stability gate (`SKILL.md` rule 6): its needles and soak run last, in the candidate load only.** The control is the current best and already passed them; they are pass/fail, not a paired comparison. The gate's lossless part is the quality evidence above, which runs in both loads. The needles and soak are run flags, not config keys, so `best-config.json` never carries them into the next control:
  - needles at C/2 and C: `--long` with numbers, e.g. `--long 65536,131072` for C = 131072. They run after all passes and tests; a miss flags `NEEDLE_MISS`;
  - if the config sizes the KV pool or max running requests for N users at full context: `--soak N`. It runs `workloads.py soak --n N --context <largest --long>` as the test "soak" after all passes; a missed code or failed request flags `TEST_FAIL`.
  `BENCH_FLAGS` goes to every config of one `queue.sh` call, so queue the candidate on its own: `bash scripts/queue.sh ctl && BENCH_FLAGS="--long 65536,131072 --soak 4" bash scripts/queue.sh cand`. The flags run after everything compared, so timing stays paired. If the candidate load would get too long (e.g. a long N-user soak), run them in one gate-only load after ACCEPT instead. Write `best-config.json` only after ACCEPT and a gate pass; a gate failure rejects with reason "stability gate".
- **How `verdict` sees a gate failure:** a hard flag (`NEEDLE_MISS`, `TEST_FAIL`) on the latest candidate load makes it REJECT; in triple mode any flagged compared run rejects. Older flagged candidate loads are only skipped.
  - Gate in the candidate load: `verdict` rejects on its own. Write "stability gate" and the flag in `PLAN.md`.
  - Gate-only load after ACCEPT: run it under the candidate's config name, then rerun `verdict`; a flagged gate load makes it REJECT. Never take an ACCEPT from before the gate load as final.
- **Smoke-start the candidate once before queueing:** launch it, send one short request, read the answer and the proof line, stop it. A candidate that fails to load or falls back should not cost a queue slot.
- **Default: two loads.** One control load with every test, then one candidate load with every test, each with several passes. Run them with `bash scripts/queue.sh ctl cand` and decide with `python3 scripts/bench.py verdict --ctl ctl --cand cand --predicted PCT`. `verdict` reads every ok load of both configs (`--since ISO` to limit them). If the bar is above the effect you predict, add loads of both configs (Noise, above); extra passes only shrink `se_prompt` and the trend check.
- **The noise split picks the mode:**

  | `sd_load` vs `sd_within` ÷ sqrt(passes) | Mode |
  |---|---|
  | small | one load per config (default) |
  | large (allocator, JIT, thermals) | alternating loads (ABAB), or the triple control → candidate → control |

  The triple mode stays: `bench.py verdict CTL_A CAND CTL_B`. Several candidates can share controls: control, A, control, B, control.
- **Request-field options need no reload:** `extra_body`, per-request sampling or draft settings. Use two configs with the same `launch` and run with `BENCH_FLAGS="--reuse"`; ctl and cand then alternate inside one load. Their prompts stay paired only with a `cache_bypass` (Counting, above). The harness reuses the server only if `.bench-server.json` records the same `launch` and `base_url`. A launch flag or env var needs a reload. Reused runs have no `startup_s`, and their memory peak covers only that run; measure startup and peak memory on fresh loads.
- **Drift checks** (`verdict` runs the first two in the window):
  - drift of the newest control load against the others;
  - the first-vs-last pass trend inside each load;
  - the logged clocks and temperatures (`state_start`, `state_end`, sampler phases) and the same-day control history.
  On REPEAT (conditions in Decide before you measure): run one more load pair in reverse order (candidate, then control).
- **Reuse the last control load** only if it is from the same day, the control config is unchanged and its drift check passes.
- **Profile in its own load,** after the A/B. nsys and ncu wrap the server launch and slow it, so a profiled load never gives timing and never joins a comparison.
- Never split one config's tests across loads to save time. Never compare a test from one load with the same test from a load on another day.
- The hypothesis card lists the load count and an ETA (`bash scripts/queue.sh status` gives ETAs from past durations).

## Context depth

- **Buckets come from the section-0 context target:** short, ~25%, 50% and 100% of it. They are per rig and model, not fixed token counts.
- **Per bucket, measure:**
  - decode as ms per step, over enough tokens to clear `LOW_N`;
  - prefill tok/s;
  - the ceiling for that depth (`ceilings.md`) and the percentage reached.
  The largest gap at any depth feeds the zoom-out (`diagnosis.md`).
- **Use real text** (`--text FILE`). Routing and sparse attention depend on content; filler text skews both.
- **Cheap long decode:** prefill one long document once, then take several decode samples on the cached prefix, each with a different short question. One long prefill then gives many decode samples at that depth.
- `python3 scripts/workloads.py sweep --context N --text FILE` runs the sweep as a config test or standalone.
- **Per-change A/B:** only the buckets the card predicts a gain in, plus one short guard bucket.
- **Full sweep:** at the round baseline, at round end, and when a large gain lands (default ~20%) or an attention, KV or cache change is accepted. The full sweep is proposed; the user decides. The threshold is configurable.
- A fixed decode window can end inside a long prefill. Keep long-context requests in their own test: a cold request, then a warm same-document request.
- Retrieval needles (3 random codes at different depths, answered exactly) prove the whole context works. Speed alone doesn't.

## Speculative decoding specifics

- Judge per-step time (ms per verify step) and accepted length separately. tok/s = a ÷ step_time.
- Take the accepted length `a` from engine counters, never from the configured draft length.
- Higher acceptance can be slower: a 7-token draft accepted 3.26 vs MTP's 2.85, yet ran 11–14% slower.
- Acceptance counters may only update on request completion (SGLang does this), so a short window sees a biased sample. Probe whole requests.
- Acceptance depends on content and temperature. Code and greedy decoding draft far better than sampled prose. Report the panel, temperature and thinking mode with every number.
- Spec on vs off can diverge because of numerics: different kernels for M = 1 vs M = k rows. Check the verify logits as `quality.md` describes before calling it a bug. A top-2 tie of 0.016 nats is not a bug.

## Output sanity

- Flag looping output (repeated shingles), failed requests, an idle GPU (<60% busy in the window), prefill inside the decode window, and KV-bound admission. A suspiciously fast result is usually broken output: a 117 tok/s "record" was a model emitting a numbered list in a loop.
- `ANSWER_DIFF` (a verdict flag) and the determinism check are described in `quality.md`.

## Memory

- On unified memory (Apple, Intel/AMD iGPU, GB10/Spark-class), GPU allocations bypass cgroup accounting. A MemAvailable delta showed 14 GiB where the real footprint was 29.4 GiB.
- Sum driver residency (Linux DRM: `drm-resident-*` in `/proc/<pid>/fdinfo`, deduplicated by `drm-client-id`) plus cgroup `anon`. For a container use `scripts/mem.sh`; for a native server, `scripts/mem.sh --pid PID` covers the PID and its children. On Apple silicon, use `scripts/mem-macos.sh <port>`.
- Track the peak with a ~1–5 s sampler, and kill the run at the cap. The host-RAM floor is a separate watchdog (`rig.md`).

## Profiling

- Profile with graphs off to get a per-kernel breakdown, but remember that graphs change launch overhead. Time the graph replay itself for the real step time.
- Read the ISA or assembly when a kernel is "at the limit". Register-region moves, spills and serialized tails hide there.
- **The sum of kernel durations, the GPU busy time and the wall time are three different numbers.** Read `profiling.md` before you turn a kernel's share of the sum into an expected speedup. ncu times compare only with other ncu times (`profiling.md`).

## Decide before you measure

- Fill in the hypothesis card (`templates/hypothesis.md`) before the run. It records the change, its quality class, the mechanism metric, the expected effect and the upper bound against the bar, the metrics to watch, and the accept and reject rule.
- Never change the rule after seeing numbers: the result is no longer evidence. If you must, write a new card with a new run name and run again.
- A result the card did not predict is a reason to look closer, not a win.
- `scripts/bench.py verdict` applies the standing rule (formulas in Noise, above):

  | Decision | Meaning |
  |---|---|
  | ACCEPT | `g ≥ bar` and `lower > 0`, no REPEAT condition; never on an uncalibrated pair verdict |
  | BELOW_BAR | `lower > 0` but `g < bar`: the gain is real but under the bar; the user decides. Never on an uncalibrated pair verdict |
  | REPEAT | `g ≥ bar` but `lower ≤ 0`; or `0 < g < bar`, `lower ≤ 0` and the CI's upper end reaches the bar with one candidate load (inconclusive: one more load of each); or drift, trend, `HOST_BUSY` in the window, or a surprise (`--predicted` rule) |
  | REJECT | no gain, a watched metric worse by more than its bar, a run not ok or flagged, or `ANSWER_DIFF` |

  CONDITIONAL is set by you on the card, when the win holds but a constraint (context, memory, quality) is not yet shown to be met.
  Your judgement still decides; the tool keeps the rule from bending.
- A win without movement in the card's mechanism metric (acceptance, step ms, bytes) is not accepted: look at it as a surprise.

## Prove the change ran

- A kernel existing, a flag set or a microbenchmark win does not show that serving used the new path. Fallbacks are common:
  - a shape the new kernel does not support;
  - a dtype guard;
  - an architecture check;
  - a graph captured before the change.
- After timing, record evidence from the real serving path for every phase and every GPU rank the change claims. It can be:
  - a short trace that shows the new kernel's name;
  - a dispatch counter;
  - a log line that only the new path prints.
- If the path did not run, a "win" measured noise and a "no change" measured the fallback. Either way the experiment says nothing about the change.
- Set `"proof"` in the run config. `scripts/bench.py` runs it after timing, keeps the output tail and flags `NO_PROOF` if it fails.

## Quality evidence

- Quality levels, the quality contract per change class, the metrics and `quality.py` are in `quality.md`. Write the contract in `THEORY.md` before the first run of a round.
- Set operator tolerances from the dtype and the operator before looking at the candidate's errors (`kernel-work.md`, correctness ladder).
- Keep four kinds of evidence separate in reports: operator correctness, dispatch coverage, quality and speed.

## Metric definitions

- **Per-GPU throughput:** total output tokens per second ÷ physical GPUs. Do not divide again by the tensor-parallel size.
- **Acceptance length:** say whether it counts accepted drafts only, or also the target's own bonus token. Also say whether it is real or simulated, and how it was averaged.
- **Tokens per step is not latency per token.** At 1,200 tok/s with 5.5 tokens per step, a step takes about 4.6 ms (5.5 ÷ 1,200), not 0.83 ms (1 ÷ 1,200).
- **Say which harness each number comes from.** Gate numbers (e.g. thinking on, first 30 s) and hill-climb numbers (thinking off) are not comparable.
- **Simulated acceptance** (a fixed accepted length forced by a test switch) isolates step cost. It never measures speculative quality. Restart without the switch before any quality run.
