---
name: optimize-inference
description: >
  Hill-climb the serving speed of a local LLM on any hardware (NVIDIA, AMD, Intel,
  Apple, unified-memory laptops, multi-GPU) and any quantization (GGUF, EXL2/EXL3,
  AWQ/GPTQ, FP8, MLX, BF16): single-user and concurrent decode tok/s, speculative
  decoding, prefill tok/s, KV cache size, startup time and TTFT, under a memory cap
  and with full-context stability. Computes the theoretical ceiling first, zooms
  out to find the one cause behind several symptoms, runs noise-controlled A/B
  experiments with a written quality contract, keeps a ledger, and qualifies the
  winner before publishing it.
  Use when asked to optimise, tune, speed up, benchmark or hill-climb
  a model server (vLLM, SGLang, llama.cpp, ExLlama/TabbyAPI, MLX, TensorRT-LLM,
  or a custom engine), to find the maximum possible tok/s on a machine, or to
  publish a tuned recipe. Also covers the kernel-level loop once config levers
  plateau: per-kernel roofline, one-variable kernel changes, proof the new code ran.
  Triggers: hill climb, tok/s, decode speed, prefill speed, MTP, EAGLE, draft model,
  speculative decoding, KV cache, TTFT, startup time, theoretical maximum,
  kernel tuning, roofline, nsys, ncu, tensor parallel, root cause, bottleneck.
---

# Optimize inference (hill-climbing a model server)

You improve how fast a model server runs on one machine, with evidence.
The loop is:

1. Inventory the rig, write the targets and the quality contract, calibrate noise.
2. Calculate the ceilings.
3. Zoom out: find the root cause with the largest checked gap.
4. Change one thing, at that cause.
5. Measure it against the control.
6. Keep it or reject it, and write down why.
7. Zoom out again after each accepted change. Repeat until the remaining gap needs work out of scope, then qualify and publish.

Detailed references, read when needed:

- `references/rig.md`: rig safety. The six invariants, `rig.json`, `scripts/rig.py`, `scripts/queue.sh`, the watchdog, leaving the rig as found.
- `references/logging.md`: the working directory, run directory, ledger and request schemas, the harness scripts, logger cost.
- `references/quality.md`: lossless levels, the quality contract table, distribution metrics, dump formats, the determinism check, `scripts/quality.py`.
- `references/ceilings.md`: theoretical maxima per metric, depth, placement and GPU split, with a worked example.
- `references/methodology.md`: counting, noise bars, the verdict, loads, the stability gate, context depth, proof, metric definitions.
- `references/diagnosis.md`: zooming out. Time budget, symptoms, root theories, probes, known symptom clusters, the sum check.
- `references/levers.md`: levers by area with measured evidence.
- `references/gotchas.md`: engine- and hardware-specific traps.
- `references/publishing.md`: qualification gates, pinning, poster and report.
- `references/kernel-work.md`: lever 7 and custom engines.
- `references/profiling.md`: reading a timeline, `scripts/budget.py`, nsys and ncu recipes, multi-GPU joins.
- `templates/hypothesis.md`: the card you fill in before every experiment.
- `scripts/`: an engine-agnostic harness (listing: `references/logging.md`, Harness scripts). Run every script with no arguments for its usage.
- `examples/`: configs for several engines, a CLI driver, a `rig.json`, ceiling inputs.

## Terms

- **c1, cN:** decode with one stream, and aggregate decode with N concurrent streams.
- **C:** the context target, the context that must stay stable. Depth buckets are short, ~25%, 50% and 100% of C.
- **l0, l1, l2:** quality levels: exact bits, rounding-level difference, labelled lossy trade (`references/quality.md`, Levels).
- **Load:** one server start (weight load, JIT, graph capture). A pass is one run of the prompt panel inside a load.
- **`sd_within`, `sd_load`:** pooled SD between passes of one load, and between load means (`references/methodology.md`, Calibrate the noise).
- **Bar:** the accept and regression threshold, k × t × `sd_load` scaled by the load counts.
- **ACCEPT, REJECT, REPEAT, BELOW_BAR:** `bench.py verdict` decisions. BELOW_BAR is a real gain under the bar; the user decides (`references/methodology.md`, Decide before you measure).
- **`a`:** the accepted length per speculative step, from engine counters.
- **Stability gate:** needles at C/2 and C, plus a concurrent soak when the config sizes the KV pool for N users (rule 6).

## 0. Before touching anything

- **Write down the targets and constraints** the user gave. Ask only if one is missing and it changes what you do: the metrics that matter (c1, cN, prefill at several lengths, TTFT, startup), the memory cap, C, and the allowed quality classes (lossless only, or labelled lossy trades such as int8 prefill).
- **Inventory the rig:** `python3 scripts/rig.py detect`, then `python3 scripts/rig.py check` (`references/rig.md`). Ask which daemons must stay alive and which settings you must not touch. Record driver, engine version, model, quantization and the current launch command.
- **Ask once, store in `PLAN.md`:** the go/no-go threshold (default: `references/diagnosis.md`, 2. The loop) and the user's preferred report format.
- **Measure, don't trust spec sheets:** run the microbenchmarks once per rig (`references/ceilings.md`).
- **Write the quality contract** in `THEORY.md` before the first run of a round (`references/quality.md`, Quality contract).
- **Calibrate noise** (`references/methodology.md`, Calibrate the noise) and measure logger cost once per rig (`references/logging.md`, Logger cost).
- **Lever 0:** audit the engine's defaults (`references/levers.md`, Lever 0: audit the engine's defaults).
- **Read any existing experiment log for this machine and model.** Never rerun a rejected experiment without a new reason.
- **Create the working directory** (`references/logging.md`, Working directory).

## 1. Ceilings first

Compute the hard and the practical ceiling for each metric and each depth bucket before optimising, with placement and GPU split, and recompute when they go stale (`scripts/ceiling.py`, `references/ceilings.md`). Report progress as a percentage of the practical ceiling per bucket. If the user's target is above the ceiling, say so early, with the arithmetic.

## 2. Ground rules (non-negotiable)

1. **One change per experiment.** Each gets its own config, derived from the current best with `base` + deltas (`bench.py resolve` shows the result).
2. **Control for noise.** Bars come from the pooled SD of every control run in the ledger (`references/methodology.md`, Noise; Loads).
3. **Keep the rig safe and fixed.** `rig.py check` runs before every run. Leave the rig as found (`references/rig.md`).
4. **Run one GPU job at a time** through `scripts/queue.sh`; never wait with `pkill -f`/`pgrep -f` or old log lines. Detach long queues; on macOS use the `python3` `start_new_session=True` form in `scripts/queue.sh`, not `setsid nohup` (`references/rig.md`, Six invariants; `references/gotchas.md`, General).
5. **Enforce the memory cap with a watchdog** (`references/rig.md`, Watchdog during a run). On unified memory, use the memory probes (`references/methodology.md`, Memory).
6. **Quality gates follow the contract** (`references/quality.md`). A config is "best" only after ACCEPT and a stability gate pass. Needles and soak are run flags (`--long`, `--soak`) on the candidate run only; the gate is not optional (`references/methodology.md`, Loads). Other end-of-round gates are proposed; the user decides (`references/publishing.md`, 4. Check the stability gate, propose the rest).
7. **Never force-kill a server mid-batch.** Abort requests, wait for the drain, then stop with a timeout (`references/gotchas.md`, General).
8. **Verify outputs, not just speed** (`references/methodology.md`, Output sanity).
9. **Logging is always on** (`references/logging.md`). Log every experiment in `PLAN.md`, including failures and why. Negative results are the most reusable output.
10. **Secrets:** never ask twice for a credential the user already saved. Never print it, and never copy it or its path into anything published.
11. **Decide the rule before the run** with a hypothesis card (`references/methodology.md`, Decide before you measure).
12. **Prove the change ran** in every phase and rank it claims (`references/methodology.md`, Prove the change ran).
13. **Resume from the record, not from memory.** After an agent restart, context reset, compaction or long pause, reread sections 2 and 3 of this file, then `PLAN.md`, `verdicts.jsonl`, `queue.jsonl` and the ledger. If an experiment has runs but no verdict, it is unfinished: rerun it. Never reconstruct a result you cannot find.
14. **Extend `scripts/`, don't replace it** (`references/logging.md`, Your own tools).

## 3. The loop

```
zoom out (fresh control) → ≥2 root theories → probe → largest checked root gap → card → config
   ↑                                                                                     ↓
   │                                                         bench.py run via queue.sh (ctl, cand)
   │                                                                                     ↓
   └── re-zoom ←── best-config + PLAN.md + commit offer ←── verdict + proof + gate ───────┘
```

Decide with `python3 scripts/bench.py verdict --ctl NAME --cand NAME --predicted PCT` (`references/methodology.md`, The verdict statistics; Decide before you measure). How the gate runs and how `verdict` sees a gate failure: `references/methodology.md`, Loads.

**Zoom out** at each trigger and in the order of `references/diagnosis.md` (1. When to zoom out; 2. The loop).

**Context depth:** which buckets to A/B per change, and when to propose a full sweep: `references/methodology.md`, Context depth.

### Lever order

A diagnosed root goes first. If the model does not fit, first compare placement "as placed" vs "if everything fit" (`references/levers.md`, Placement and format). Without a budget yet, and as a tie-breaker, use this order, cheapest first (`references/levers.md`):

0. **Audit engine defaults.**
1. **Persistent JIT, compile and graph caches;** eager safetensors loading where mmap is slow.
2. **Decode graphs** (CUDA/XPU graphs).
3. **Speculative decoding:** method (built-in MTP, EAGLE, a draft model, n-gram), draft length per concurrency and context, a pruned draft LM head, sampling on the GPU, decode-style verify.
4. **Concurrency and KV sizing:** max running requests, KV pool of N × context, state slots for hybrid models, prefix caching.
5. **Prefill:** chunk size, a faster attention library, int8/fp8 GEMMs as a labelled trade, no padding cliffs in grouped MoE GEMMs.
6. **Kernel thread and tile sizes.**
7. **Kernel work:** profile, read the ISA, fix the dominant kernel (`references/kernel-work.md`).

**When a lever fails:** weird result or surprise win → suspect the measurement first (`references/methodology.md`); fusion gives nothing under graphs, higher acceptance without higher tok/s, or a microbenchmark win absent end to end (three checks in order) → `references/diagnosis.md`, 7. Known symptom clusters.

### After each kept change

After ACCEPT and a stability gate pass (rule 6), update `best-config.json` and `PLAN.md`, and offer the user a checkpoint commit to their branch.

### Plateau

Zoom out once before you declare a plateau. Declare it when three consecutive levers land inside noise and the zoom-out finds no new root. Write a STATUS section in `PLAN.md` with:

- best numbers vs baseline vs ceiling, per depth bucket, from a config that passed the stability gate;
- what limits further gains, with evidence;
- the latest diagnosis from `THEORY.md`: the budget, and the theories with their status;
- the remaining root gaps, checked or estimated, with the structural change each needs and its cost.

Then keep the loop alive at a slower cadence if the user said "don't stop", or hand back.

## 4. Qualify and publish

Follow `references/publishing.md`: the stability gate is a precondition, the other gates are proposed, and the published build is pinned, built clean and A/B-checked against your best image.

## 5. Reporting to the user

- **Answer a status question first,** then the detail. Give ETAs from logged durations (`bash scripts/queue.sh status`), and take timestamps from `date`, never a guess of the user's local time.
- **After each run:** a small table plus 2-3 plain sentences: what was tried, faster or not, kept or not, what next.
- **Use the user's report format** from `PLAN.md`. Build the progress board from the ledger (`python3 scripts/bench.py board`).
- **Define every label or codename** in plain words the first time you use it, and every throughput number (`references/methodology.md`, Metric definitions).
- **At the end, start with a table:** metric, baseline, now, ceiling, how it was measured (passes and loads, cold or warm, which harness).
- **Then:** what got the gains, why it stops here, the known limitations, what was not verified, and the system state you changed (settings, running servers, background processes, uncommitted code, branches that must not be deleted).
- **When asked to free the GPU:** drain, stop the server, confirm no processes and an idle clock, and end any loop.
