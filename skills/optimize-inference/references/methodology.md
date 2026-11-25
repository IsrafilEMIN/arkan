# Measurement methodology

Most "wins" and "regressions" in inference tuning are measurement errors. In every case below, a check like this changed a conclusion.

## Counting

- **Count tokens with the tokenizer or the server's usage stats, not streamed chunks.** With speculative decoding, engines emit several tokens per SSE chunk; counting chunks under-reported MTP decode. Use `stream_options: {include_usage: true}` or `continuous_usage_stats`, or re-tokenize the output.
- **Size prompts with the real tokenizer.** "Random word" documents were ~3.5 tokens per word, not ~1.3–1.9, so nominal "32K/128K" cells were really 58K/232K.
- **Build prompts before the clock starts.** Make them unique per run, with a random prefix, so prefix caching cannot hit, unless you are measuring cache hits deliberately.
- **Decode tok/s:** completion tokens after the first token ÷ time since the first token.
- **Prefill tok/s:** prompt tokens ÷ TTFT on a cold, unique prompt. Report cold and warm (cache-hit) separately; never publish a cache-hit prefill as prefill.
- **Concurrent throughput (cN):** total completion tokens across N streams ÷ wall time from first start to last finish. Per-stream sums overstate it when streams don't overlap. Verify the server actually ran N at once (`max_running`, state slots).

## Noise

- Expect ±5–10% run-to-run. Sources include:
  - thermals and clocks;
  - power source (a laptop on battery or a balanced profile ran 8–10% slower);
  - background CPU load (a laptop RTX 4080 went 107 → 75 tok/s under light CPU load);
  - prompt content, because acceptance depends on text type.
- Take ≥6 decode samples and use the median. Use a fixed, seeded prompt panel; random prompts moved acceptance from 2.4 to 3.7 and made c1 comparisons pure noise.
- **Interleave runs:** control, candidate, control. Compare a candidate only with its neighbours. Drift over an hour can exceed the effect you are measuring: the same config measured 53.8 and then 49.5 an hour apart.
- **When comparing engines,** run them on the same card on the same day, back to back. Accept "B is faster" only if a bootstrap 95% CI of median(B)/median(A) is above 1.0.
- Discard cold first runs and the first boot after a JIT cache miss (36 vs 90 tok/s on one vLLM boot).
- Microbenchmarks need interleaved min-of-N timing; clock ramp-up made one kernel look 2.5× slower than it was.

## Order runs by server state

- **A load is the costly, noisy step:** weight load, JIT and graph capture, allocator state. Count loads: one per state in the run order, not one per test. Example: 4 tests × ON/OFF with control, candidate, control is 3 loads, not 12.
- **List every test for the experiment before the first run:**
  - built-in timing;
  - needles at ~50% and ~100% context (`--long N,N`, one load);
  - greedy equivalence;
  - accuracy evals;
  - profiling;
  - proof (`"proof"`).
- Put the extra tests in the config's `tests` list, so they run in the same load. A failed test flags `TEST_FAIL`. Keep the same order in every state: position in the load changes thermals and cache state.
- **Bracket at state level:** control (all tests) → candidate (all tests) → control (all tests). `bench.py verdict` reads the three runs as usual.
- **Several candidates share controls:** control, A, control, B, control. That is 5 loads for 2 candidates, not 6, and each candidate has a control on both sides.
- A trailing control can be the next experiment's leading control only if the control config did not change and the gap is short. Drift is real: the same config gave 53.8 and 49.5 an hour apart.
- **An option that is a request field needs no reload:** `extra_body`, per-request sampling or draft settings. Use two configs with the same `launch` and run with `BENCH_FLAGS="--reuse"`. The harness reuses the server only if `.bench-server.json` records the same `launch` and `base_url`. A launch flag or env var needs a reload.
- Reused runs have no `startup_s`, and their memory peak covers only that run. Measure startup and peak memory on fresh loads.
- Never split one state's tests across loads to save time. Never compare a test from one load with the same test from a load on another day.

## Speculative decoding specifics

- Judge per-step time (ms per verify step) and accepted length separately. tok/s = a ÷ step_time.
- Higher acceptance can be slower: a 7-token draft accepted 3.26 vs MTP's 2.85, yet ran 11–14% slower.
- Acceptance counters may only update on request completion, so a short window sees a biased sample. Probe whole requests.
- Acceptance depends on content and temperature. Code and greedy decoding draft far better than sampled prose. Report the panel, temperature and thinking mode with every number.
- A greedy equivalence check (spec on vs off) can diverge because of numerics: different kernels for M=1 vs M=k rows. Compare logits at the divergence point before calling it a bug. A top-2 tie of 0.016 nats is not a bug.

## Long context

- A fixed decode window can end inside a long prefill. Use a dedicated long-context run: a cold request, then a warm same-document request.
- Retrieval needles (3 random codes at different depths, answered exactly) prove the whole context works. Speed alone doesn't.

## Output sanity

- Flag looping output (repeated shingles), failed requests, an idle GPU (<60% busy in the window), prefill inside the decode window, and KV-bound admission. A 117 tok/s "record" was a model emitting a numbered list in a loop.

## Memory

- On unified memory (Apple, Intel/AMD iGPU, GB10/Spark-class), GPU allocations bypass cgroup accounting. A MemAvailable delta showed 14 GiB where the real footprint was 29.4 GiB.
- Sum driver residency (Linux DRM: `drm-resident-*` in `/proc/<pid>/fdinfo`, deduplicated by `drm-client-id`) plus cgroup `anon`.
- Track the peak with a ~1–5 s sampler, and kill the run at the cap.

## Profiling

- Profile with graphs off to get a per-kernel breakdown, but remember that graphs change launch overhead. Time the graph replay itself for the real step time.
- Profile prefill by stage (GEMM, attention, MoE, linear attention, norms/Hadamards) before picking the next lever.
- Debug builds that remove work (e.g. skipping dequantization) change code generation, so they are not valid lower bounds.
- Read the ISA or assembly when a kernel is "at the limit". Register-region moves, spills and serialized tails hide there.
- **The sum of kernel durations, the GPU busy time and the wall time are three different numbers.** Read `profiling.md` before you turn a kernel's share of the sum into an expected speedup.
- ncu locks clocks to base by default and replays kernels. Compare its times only with other ncu times.

## Decide before you measure

- Fill in the hypothesis card (`templates/hypothesis.md`) before the run. It records:
  - the one change;
  - the expected effect;
  - the metrics to watch;
  - the accept and reject rule.
- If you change the rule after seeing numbers, the result is no longer evidence. Write a new card and run again.
- `scripts/bench.py verdict` applies the standing rule: beat both controls, nothing watched worse than both controls by more than 3%, and a repeat for drift or for a surprising win. It also prints a bootstrap 95% CI for c1 as information. An interval that includes 1.0 means the win could be noise, even if the medians beat both controls.

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

## Accuracy evidence

- Set operator tolerances from the dtype and the operator before looking at the candidate's errors (`kernel-work.md`, correctness ladder).
- At model level, freeze all of these:
  - the dataset version and split;
  - the prompt template;
  - the parser;
  - max output tokens;
  - the seed.

  Compare matched question IDs and report which ones changed from correct to wrong and from wrong to correct. Never drop failed or truncated cases to improve a score.
- A small difference that is not significant does not show that the builds are equivalent. To claim equivalence, set a margin first and use enough samples.
- Keep four kinds of evidence separate in reports: operator correctness, dispatch coverage, task accuracy and speed.

## Metric definitions

- **Per-GPU throughput:** total output tokens per second ÷ physical GPUs. Do not divide again by the tensor-parallel size.
- **Acceptance length:** say whether it counts accepted drafts only, or also the target's own bonus token. Also say whether it is real or simulated, and how it was averaged.
- **Tokens per step is not latency per token.** At 1,200 tok/s with 5.5 tokens per step, a step takes about 4.6 ms (5.5 ÷ 1,200), not 0.83 ms (1 ÷ 1,200).
- **Simulated acceptance** (a fixed accepted length forced by a test switch) isolates step cost. It never measures speculative quality. Restart without the switch before any accuracy run.
