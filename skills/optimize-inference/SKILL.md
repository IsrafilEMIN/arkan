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

- `references/rig.md`: rig safety. The six invariants, `rig.json`, `scripts/rig.py`, capped scopes, the watchdog, leaving the rig as found.
- `references/logging.md`: what every run records. Run directory, ledger and request schemas, collectors, opt-in heavy logs, what the ledger gives without new runs.
- `references/quality.md`: lossless levels l0/l1/l2, the quality contract table, distribution metrics, dump formats, the determinism check and `ANSWER_DIFF`, `scripts/quality.py`.
- `references/ceilings.md`: theoretical maxima. Hard vs practical-at-current-graph ceilings, placement, pipeline split, links, per-depth ceilings, a worked example.
- `references/methodology.md`: noise bars from pooled SD, load modes, drift checks, context depth buckets, tokens-per-word calibration, measurement pitfalls.
- `references/diagnosis.md`: zooming out. Time budget per depth, symptoms, root theories, probes on a fixed token path, the sum check, known symptom clusters.
- `references/levers.md`: levers by area with measured evidence, including lever 0 (engine defaults audit), placement/format and structural levers.
- `references/gotchas.md`: engine- and hardware-specific traps.
- `references/publishing.md`: qualification gates, pinning, poster and report.
- `references/kernel-work.md`: lever 7 and custom engines. Default-off switches, ISA diff, per-kernel roofline, kernel probes, correctness ladder, the kernel inner loop.
- `references/profiling.md`: reading a timeline, `scripts/budget.py`, nsys and ncu recipes, multi-GPU joins.
- `templates/hypothesis.md`: the card you fill in before every experiment.
- `scripts/`: an engine-agnostic harness. Run every script with no arguments for its usage.
  - `bench.py`: `run`, `show`, `verdict`, `noise`, `board`, `resolve`. Drivers (`http`, `cli`), timing adapters, config `base` + deltas, test hooks.
  - `rig.py`: `detect`, `check`, `state`, `noise`. `queue.sh`: serialized queue and `status`. `mem.sh`, `mem-macos.sh`: memory probes.
  - `ceiling.py`: ceilings. `workloads.py`: depth sweep, clients, multi-turn, invariance. `budget.py`: trace to attributed time per part.
  - `quality.py`: l0/l1/l2 checks. `isa_diff.py`: per-function ISA diff of two builds.
- `examples/`: configs for several engines, a CLI driver, a `rig.json`, ceiling inputs.

## 0. Before touching anything

- **Write down the targets and constraints** the user gave. Ask only if one is missing and it changes what you do.
  - Metrics that matter: c1 decode, cN decode, prefill at several lengths, TTFT, startup.
  - Memory cap.
  - Context target: the context that must stay stable. It sets the depth buckets (short, ~25%, 50%, 100% of it; `references/methodology.md`).
  - Which quality classes are allowed: lossless only, or labelled lossy trades such as int8 prefill.
- **Inventory the rig:** `python3 scripts/rig.py detect` writes `rig.json` (platform, collectors, checks, hooks, scopes). Then `python3 scripts/rig.py check`. See `references/rig.md`.
  - Ask the user which daemons must stay alive (they become `hooks`) and which settings you must not touch (`settings.protected`).
  - Record driver, engine version, model, quantization and the current launch command.
- **Ask once, store in `PLAN.md`:**
  - the lever-decision threshold: above it you ask go/no-go. Default: a redesign, multi-day work, a quality-class change, or an area the user excluded;
  - the user's preferred report format.
- **Measure, don't trust spec sheets.** Once per rig, short microbenchmarks into `rig.json` `microbench`: bandwidth at the real read sizes, cost of one dependent kernel node, link bandwidth under real traffic, peak FLOPs at the served power cap and clocks.
- **Write the quality contract** in `THEORY.md` before the first run of a round: the class of each planned change, its per-change evidence and its margin (`references/quality.md`).
- **Calibrate noise:** run the control several times (passes in one load plus a few loads); `python3 scripts/bench.py noise`. Once per rig, A/B logging off vs on (`bench.py run --no-samplers`) to show logging costs less than the noise bar.
- **Lever 0, audit the engine's defaults:** read its flags and env defaults (grep `getenv`) for values tuned for another GPU or default-off fast paths (`references/levers.md`).
- **Read any existing experiment log for this machine and model.** Never rerun a rejected experiment without a new reason.
- **Create the working directory:**
  - `rig.json`: the rig inventory and check levels.
  - `PLAN.md`: a timestamped log of every experiment, with numbers, verdict and reason; the threshold and report format.
  - `THEORY.md`: the ceilings, the quality contract, the time budget and the current diagnosis.
  - `ledger.jsonl`: one line per run, from the harness. `runs/<run_id>/`: everything a run recorded (`references/logging.md`).
  - `queue.jsonl`: queue events from `scripts/queue.sh`.
  - `configs/`: one JSON per run.
  - `scripts/`: a copy of this skill's `scripts/`. Run the harness from the working directory, so configs reach the memory probe as `scripts/mem.sh`.
  - `hypotheses/`: one card per experiment, from `templates/hypothesis.md`, written before the run.
  - `verdicts.jsonl`: one line per accept/reject decision, from `scripts/bench.py verdict`.
  - `best-config.json`.

## 1. Ceilings first

Compute the ceilings for each metric and each depth bucket before optimising (`scripts/ceiling.py`, `references/ceilings.md`):

- **Hard ceiling:** bytes ÷ measured bandwidth (decode), FLOPs ÷ peak at the served cap (prefill).
- **Practical, at the current graph:** bytes ÷ bandwidth + dependent kernels × measured cost per node + work that moves no bytes (top-k, syncs, recurrence, sampling). It is not a floor: fusion, fewer dependent steps or overlap can go below it. The gap between the two is the structural budget.
- **Decode bytes per emitted token:** dense weights, active experts (top-k ÷ experts × expert bytes), LM head, KV at the working depth. Speculative decoding divides the target's bytes by the accepted length `a` measured from engine counters, never the configured draft length, and adds the draft's bytes.
- **Placement:** compute "as placed" (resident bytes ÷ VRAM bandwidth + non-resident bytes ÷ the bandwidth that serves them) and "if everything fit". A large gap makes a format or placement that fits the first lever; that is a quality trade the user decides.
- **Layer or pipeline split:** c1 uses one card at a time, so the ceiling is one card's bandwidth; the metric is both-cards-busy time. Tensor parallel, links, sparse or sliding-window attention and looped layers: `references/ceilings.md`.
- **TTFT, startup, KV size:** one forward pass plus tokenize and schedule; weight read plus allocation with persistent caches; KV bytes per token × layers that have KV.
- **Recompute:** ceilings carry a config hash. A change of quant, card count, placement or power cap makes them stale.
- **Per kernel, once you reach lever 7:** roofline against the measured machine balance (`references/kernel-work.md`).

Report progress as a percentage of the practical ceiling per bucket. If the user's target is above the ceiling, say so early, with the arithmetic.

## 2. Ground rules (non-negotiable)

1. **One change per experiment.** Give each its own config file, derived from the current best with `base` + deltas (`bench.py resolve` shows the result).
2. **Control for noise.** Accept and regression bars are k × the pooled SD of the compared quantity, from every control run in the ledger (`bench.py noise`); defaults in `rig.json` `noise`. Recalibrate after a driver, power-cap or engine-build change. Default: one load per config with n passes each; the measured within- vs between-load SD picks the mode (alternating loads when between-load SD is large). Details and drift checks: `references/methodology.md`.
3. **Keep the rig safe and fixed.** `rig.py check` runs before every run. A probe that ran and failed blocks the run by default; "not available" never blocks and is recorded. The rig may lower a check to warn or off. Leave the rig as found. See `references/rig.md`.
4. **Run one GPU job at a time** through `scripts/queue.sh`. The queue stops at the first failure (`--keep-going` is opt-in).
   - Wait only on a PID, the lock, or log lines written after a recorded offset. Never use `pkill -f`/`pgrep -f` or grep old log lines.
   - Detach long queues so they survive agent restarts. macOS has no `setsid`, and its `nohup` fails without a console session: use the `python3` `os.setsid()` form in `scripts/queue.sh`.
5. **Enforce the memory cap with a watchdog** that kills the run, plus the host-RAM floor and the no-progress timeout (`references/rig.md`).
   - On unified memory, GPU allocations do not show in cgroup counters or MemAvailable. Use `scripts/mem.sh` (container or `--pid PID`) or, on Apple silicon, `scripts/mem-macos.sh <port>`.
6. **Quality gates follow the contract.** Per change, collect only the cheap evidence its class needs (l0 hash, l1 distribution check, l2 labelled trade; `references/quality.md`). End-of-round gates (needles at depth, soak, long sessions, full sweep) are proposed; the user decides.
7. **Never force-kill a server mid-batch.** Abort requests, wait for the drain, then stop with a timeout. A forced stop mid-prefill has caused GPU driver faults.
8. **Verify outputs, not just speed.** The harness flags looping output, failed requests, idle GPUs and `ANSWER_DIFF` (`references/quality.md`). A suspiciously fast result is usually broken output.
9. **Logging is always on.** Every run writes a run directory and a ledger row (`references/logging.md`). Log every experiment in `PLAN.md`, including failures and why. Negative results are the most reusable output.
10. **Secrets:** never ask twice for a credential the user already saved. Never print it, and never copy it or its path into anything published.
11. **Decide the rule before the run.** Fill in a hypothesis card (`templates/hypothesis.md`) before each experiment. Never change the rule after seeing the numbers. A result the card did not predict is a reason to look closer, not a win.
12. **Prove the change ran.** A config flag, a new kernel or a default-on option does not prove that the server used it. After timing, record evidence from the real serving path in every phase the change claims: prefill, decode, verify, and every GPU rank. Use a short trace, a dispatch counter or a log line that only the new path prints. Without it, a "win" or a "no change" may measure the fallback. Set `"proof"` in the config to have `scripts/bench.py` record it.
13. **Resume from the record, not from memory.** After an agent restart, context reset, compaction or long pause, reread sections 2 and 3 of this file, then `PLAN.md`, `verdicts.jsonl`, `queue.jsonl` and the ledger. If an experiment has runs but no verdict, it is unfinished: rerun it. Never reconstruct a result you cannot find.
14. **Extend `scripts/`, don't replace it.** Add drivers, timing adapters and test hooks. If you must write your own tool, it writes ledger rows in the `references/logging.md` schema so `verdict` and `board` still work.

## 3. The loop

```
zoom out (fresh control) → ≥2 root theories → probe → largest checked root gap → card → config
   ↑                                                                                     ↓
   │                                                         bench.py run via queue.sh (ctl, cand)
   │                                                                                     ↓
   └── re-zoom ←── best-config + PLAN.md + checkpoint commit offer ←── verdict + proof ───┘
```

`python3 scripts/bench.py verdict --ctl NAME --cand NAME --predicted PCT` applies rule 2 to the ledger: paired per-prompt ratios with a CI, against bars from the pooled SD. Pass the card's predicted gain as `--predicted`; a win far above it asks for a repeat. Decisions: ACCEPT, REJECT, REPEAT, BELOW_BAR (a real gain under the bar: the user decides). The verdict is "calibrated" only with enough control loads and within-load samples (`rig.json` `noise.min_loads`, `noise.min_df`); an uncalibrated pair verdict is never ACCEPT or BELOW_BAR, so run more control loads first. Prompts stay paired on a reused server only with a rig `cache_bypass` (`references/logging.md`). A flagged run rejects; `HOST_BUSY` in a compared run asks for a repeat; NOISY and LOW_N only warn. Triple mode (`verdict CTL_A CAND CTL_B`) stays for alternating loads. Your judgement still decides; the tool keeps the rule from bending.

### Zoom out

Zoom out before the first lever, after each accepted lever, after two rejects in a row, after a surprise, and before you declare a plateau (`references/diagnosis.md`):

1. **Measure the current control fresh** against the ceilings and build the time budget per depth bucket (`scripts/budget.py`). Never reuse an old trace.
2. **Form at least two competing root theories:** "root X explains symptoms A, B, C".
3. **Run a discriminating probe** on a fixed token path (teacher-forced tokens, forced acceptance length, replayed routing; result in ms per step). Probes: ablation, upper bound, gain vs noise. Probes are never kept or accepted.
4. **A root's gap is the sum of the parts it explains.** Take the largest checked root gap. An estimated gap needs a probe before it goes first. The size of a known fix is not the size of the gap.
5. **Name it and the reason in 1-2 lines, then attack.** No menus of levers. Ask go/no-go only above the threshold in `PLAN.md`.
6. **Sum check:** the planned levers' predicted gains, scaled down by the measured prediction ratio so far, vs the target. If short, propose the structural change now.

Spend at most ~2 h of bench-only work on one part, then zoom out (`rig.json` or the user can change the cap). Record each zoom-out as a dated `## Diagnosis` section in `THEORY.md`. Keep refuted theories with the reason.

### Context depth

Per change, A/B only the depth buckets the card predicts a gain in, plus one short guard bucket (`scripts/workloads.py sweep`). Propose a full sweep at the round baseline, at round end, and when a ~20% gain lands or an attention, KV or cache change is accepted. Use real text (`references/methodology.md`).

### Lever order

A diagnosed root goes first. Without a budget yet, and as a tie-breaker, use this order, cheapest first (`references/levers.md`):

0. **Audit engine defaults:** flags and env defaults tuned for another GPU, default-off fast paths.
1. **Persistent JIT, compile and graph caches** (startup −50–70%). Also use eager safetensors loading instead of mmap where it is slow.
2. **Decode graphs** (CUDA/XPU graphs): often 2× c1 on their own.
3. **Speculative decoding:**
   - Choose the method (built-in MTP, EAGLE, a draft model, n-gram).
   - Sweep draft length per concurrency and context; the best length differs.
   - Prune the draft LM head's vocabulary.
   - Keep sampling on the GPU.
   - Make sure verify runs with decode-style attention.
4. **Concurrency and KV sizing:**
   - Set max running requests and the KV pool to N × context.
   - For hybrid SSM/GDN models, size the state slots. They, not KV, often cap concurrency.
   - Explicitly enable prefix caching and confirm `cached_tokens` > 0.
5. **Prefill:**
   - Tune chunk size; it trades throughput against decode stalls.
   - Use a faster attention library.
   - Use int8/fp8 prefill GEMMs as a labelled quality trade.
   - Avoid padding cliffs in grouped MoE GEMMs.
6. **Kernel thread and tile sizes:** defaults are often tuned for a bigger card.
7. **Kernel work:** profile, read the ISA, fix the dominant kernel. Follow `references/kernel-work.md`:
   - Pick the kernel by *exposed* time on the timeline, not by its share of summed kernel time (`references/profiling.md`).
   - Compute its own floor. The gap to the floor is what this kernel can still give.
   - One variable per version. Keep every old version; never overwrite one.
   - Correctness first, at every row count M you serve. Then an interleaved microbenchmark. Then proof it ran. Then the end-to-end A/B, which is the only test that accepts.
   - In a custom engine, put new paths behind default-off switches and check the default path with `scripts/isa_diff.py`.

### When a lever fails

- **If fusion gives nothing** under graphs, check where the time goes before you stop: inside the main kernels, or in a chain of small dependent kernels on an under-filled grid. A chain needs more blocks or fewer dependent steps, not fusion that adds grid barriers (`references/levers.md`).
- **If higher acceptance doesn't give higher tok/s,** the draft costs too much. Measure per-step time.
- **If a weird result appears,** suspect the measurement first: tokens counted per streamed chunk, prompt length not measured with the real tokenizer, cache hits, thermal state, or the battery.
- **If a kernel wins in a microbenchmark but not end to end,** check three things in order:
  - Did the new kernel run in serving (rule 12)?
  - Did the time just move to the next join? On a timeline, the consumer now waits longer.
  - Did the microbenchmark see warm caches that serving never sees? Rotate weights or flush between iterations.
- **If summed kernel time exceeds step time,** kernels overlap. A kernel's share of the sum is not time you can remove.
- **If one GPU in a tensor-parallel group is faster,** its spare time shows up as waiting inside the collective. The slowest rank sets the step. Profile every rank.

### After each kept change

Update `best-config.json` and `PLAN.md`, then offer the user a checkpoint commit to their branch.

### Plateau

Before you declare a plateau, zoom out once. Three levers inside noise often treated symptoms of one cause that is not on this list. Declare a plateau when three consecutive levers land inside noise and the zoom-out finds no new root. Write a STATUS section in `PLAN.md` with:

- best numbers vs baseline vs ceiling, per depth bucket;
- what limits further gains, with evidence;
- the latest diagnosis from `THEORY.md`: the budget, and the theories with their status;
- the remaining root gaps, checked or estimated, with the structural change each needs and its cost.

Then keep the loop alive at a slower cadence if the user said "don't stop", or hand back.

## 4. Qualify and publish

See `references/publishing.md` and `references/quality.md`.

- Propose the end-of-round gates from the quality contract; the user decides which run. Never start them on your own.
- Pin weights by revision, engine by image digest or source commit, and kernels by commit. Build the published artifact from those pins in a clean checkout, never from a dirty tree.
- Run the accepted gates on the clean build: load, chat, reasoning, tools round-trip, needles at depth, and speed.
- Then A/B the clean build against your best image to prove they match.
- Report which numbers come from which harness. Gate numbers (e.g. thinking on, first 30 s) and hill-climb numbers (thinking off) are not comparable.
- Keep four kinds of evidence apart, because none of them stands in for another:
  - operator correctness (the kernel test);
  - dispatch coverage (proof the path ran, rule 12);
  - quality (the contract's level and task results);
  - speed.
- "Not significant" does not prove two builds equivalent. To claim equivalence, set a margin before the run and use an equivalence test with enough samples (`references/quality.md`).

## 5. Reporting to the user

- **Answer a status question first,** then the detail. Give ETAs from logged durations (`bash scripts/queue.sh status`), and take timestamps from `date`, never a guess of the user's local time.
- **After each run:** a small table plus 2-3 plain sentences: what was tried, faster or not, kept or not, what next.
- **Use the user's report format** from `PLAN.md`. Build the progress board from the ledger (`python3 scripts/bench.py board`).
- **Define every label or codename** in plain words the first time you use it.
- **At the end, start with a table:** metric, baseline, now, ceiling, how it was measured (passes and loads, cold or warm, which harness).
- **Then:** what got the gains, why it stops here, the known limitations, what was not verified, and the system state you changed (settings, running servers, background processes, uncommitted code, branches that must not be deleted).
- **Define every throughput number:**
  - per-GPU throughput is total ÷ physical GPUs, never divided again by the tensor-parallel size;
  - say whether an acceptance length counts only accepted drafts or also the target's bonus token;
  - tokens per step is not latency per token.
- **When asked to free the GPU:** drain, stop the server, confirm no processes and an idle clock, and end any loop.
