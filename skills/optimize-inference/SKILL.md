---
name: optimize-inference
description: >
  Hill-climb the serving speed of a local LLM on any hardware (NVIDIA, AMD, Intel,
  Apple, unified-memory laptops, multi-GPU) and any quantization (GGUF, EXL2/EXL3,
  AWQ/GPTQ, FP8, MLX, BF16): single-user and concurrent decode tok/s, speculative
  decoding, prefill tok/s, KV cache size, startup time and TTFT, under a memory cap
  and with full-context stability. Computes the theoretical ceiling first, zooms
  out to find the one cause behind several symptoms, runs noise-controlled A/B
  experiments, keeps a ledger, and qualifies the winner before publishing it.
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

1. Measure the baseline.
2. Calculate the ceiling.
3. Zoom out: find the biggest bottleneck and the one cause behind the symptoms.
4. Change one thing, at that cause.
5. Measure it against controls.
6. Keep it or reject it, and write down why.
7. Zoom out again after each accepted change. Repeat until the remaining gap needs work out of scope, then qualify and publish.

Detailed references, read when needed:

- `references/ceilings.md`: how to compute theoretical maxima. It includes a worked example.
- `references/methodology.md`: measurement pitfalls and statistics.
- `references/diagnosis.md`: zooming out. Time budget, symptom list, competing theories, discriminating probes, known symptom clusters, whole-system score.
- `references/levers.md`: levers by area, ordered by typical payoff, with measured evidence.
- `references/gotchas.md`: engine- and hardware-specific traps.
- `references/publishing.md`: qualification gates, pinning, poster and report.
- `references/kernel-work.md`: lever 7 in detail. Per-kernel roofline, decode vs prefill kernel rules, split-K and split-KV, correctness ladder, the kernel inner loop.
- `references/profiling.md`: reading a timeline (kernel sum vs busy time vs wall time), nsys and ncu recipes that work on any engine, multi-GPU joins.
- `templates/hypothesis.md`: the card you fill in before every experiment.
- `scripts/`: an engine-agnostic harness. It has a bench, ceiling calculator, memory watchdog, serialized queue and ledger. `scripts/bench.py verdict` applies the accept rule from section 2 to the ledger.

## 0. Before touching anything

- **Write down the targets and constraints** the user gave. Ask only if one is missing and it changes what you do.
  - Metrics that matter: c1 decode, cN decode, prefill at several lengths, TTFT, startup.
  - Memory cap.
  - Context length that must stay stable.
  - Which quality changes are allowed: lossless only, or labelled lossy trades such as int8 prefill.
- **Inventory the machine:**
  - accelerator, memory type and size, and whether memory is unified;
  - driver, engine version, model, quantization, current launch command.
- **Measure, don't trust spec sheets:**
  - real memory bandwidth (device copy);
  - real matmul throughput (large GEMM);
  - clocks under load.
- **Read any existing experiment log for this machine and model.** Never rerun a rejected experiment without a new reason.
- **Create the working directory:**
  - `PLAN.md`: a timestamped log of every experiment, with numbers, verdict and reason.
  - `THEORY.md`: the ceilings, the time budget and the current diagnosis.
  - `ledger.jsonl`: one line per run, from the harness.
  - `configs/`: one JSON per run.
  - `scripts/`: a copy of this skill's `scripts/`. Run the harness from the working directory, so configs reach the memory probe as `scripts/mem.sh`.
  - `hypotheses/`: one card per experiment, from `templates/hypothesis.md`, written before the run.
  - `verdicts.jsonl`: one line per accept/reject decision, from `scripts/bench.py verdict`.
  - `best-config.json`.

## 1. Ceilings first

Compute the theoretical maximum for each metric before optimising (`scripts/ceiling.py`, `references/ceilings.md`):

- **Decode is memory-bandwidth bound.** Count the bytes read per emitted token:
  - dense weights;
  - active experts: top-k ÷ experts × expert bytes;
  - LM head;
  - KV read at the working context.
  - Divide by measured bandwidth.
  - Speculative decoding divides the target's bytes by the accepted length. It also adds the draft's bytes, and the draft's LM head is often the biggest part.
- **Prefill is compute bound.** FLOPs per token ≈ 2 × active params, plus attention at about 4 × layers × hidden × position. Divide by ~50% of measured peak for a practical ceiling.
- **TTFT floor:** one forward pass plus tokenize and schedule.
- **Startup floor:** weight read from disk or page cache plus allocation, assuming JIT and graph caches persist.
- **KV:** bytes per token per layer × the layers that actually have KV (hybrid models have few). That gives how many full-length sequences fit under the memory cap.
- **Tensor parallel (several GPUs on one model):** each card reads its shard plus every replicated tensor. Divide by that card's measured bandwidth. Then add the communication floor: all-reduces per step × the measured latency of one all-reduce at decode size. At decode the payload is small, so latency, not link bandwidth, sets this floor.
- **Looped layers (a block of layers run more than once per token):** count the block's weight bytes once per pass. Weights of a few GB do not stay in cache between passes. For a looped MoE block, the experts touched are the union over all passes. Count attention and KV for every pass that has them.
- **Per kernel, once you reach lever 7:** place each dominant kernel on the roofline. Compare its arithmetic intensity (FLOPs ÷ bytes) with the measured machine balance (peak FLOPs ÷ bandwidth). A kernel below the balance is memory bound; judge it by achieved bandwidth, not by compute use. See `references/kernel-work.md`.

Report progress as a percentage of the practical ceiling. If the user's target is above the ceiling, say so early, with the arithmetic.

## 2. Ground rules (non-negotiable)

1. **One change per experiment.** Give each its own config file. Derive new configs from the current best.
2. **Control for noise.** Run-to-run noise is typically ±5–10%.
   - Take ≥6 decode samples per run and use the median.
   - Run controls on both sides of each candidate: control, candidate, control.
   - Accept only if the candidate beats both neighbouring controls on its target metric and regresses nothing by more than ~3%.
   - Repeat any single surprising win.
3. **Keep the environment fixed.** Stay on AC power, on a fixed performance profile, with an idle host and no other GPU jobs.
   - Make the harness refuse to run otherwise.
   - Record the state at the end of each run, and void the run if it changed.
   - Restore any profile you changed when you finish, and tell the user.
4. **Run one GPU job at a time.** Serialize them with a lock (`scripts/queue.sh`).
   - Never use `pkill -f`/`pgrep -f` patterns that can match your own shell.
   - Detach long queues (`setsid nohup … &`) so they survive agent restarts. macOS has no `setsid`, and its `nohup` fails without a console session: use the `python3` `os.setsid()` form in `scripts/queue.sh`.
5. **Enforce the memory cap with a watchdog** that kills the run.
   - On unified memory, GPU allocations do not show in cgroup counters or MemAvailable. Measure driver residency (e.g. `drm-resident-*` in `/proc/<pid>/fdinfo`, or `nvidia-smi`) plus process anonymous memory. On Apple silicon, `scripts/mem-macos.sh <port>` reads the server's footprint, Metal buffers included.
6. **Stability gates.** A config is only "best" after it passes:
   - a long-context retrieval run, with needles in a ~50% then ~100% context document, found exactly;
   - a soak with concurrent full-length requests, if the KV pool is sized for N users;
   - a greedy output equivalence check, if the change claims to be lossless.
7. **Never force-kill a server mid-batch.** Abort requests, wait for the drain, then stop with a timeout. A forced stop mid-prefill has caused GPU driver faults.
8. **Verify outputs, not just speed.** Flag degenerate or looping output, failed requests and an idle GPU. A suspiciously fast result is usually broken output.
9. **Log everything in `PLAN.md`,** including failures and why they failed. Negative results are the most reusable output.
10. **Secrets:** never ask twice for a credential the user already saved. Never print it, and never copy it or its path into anything published.
11. **Decide the rule before the run.** Fill in a hypothesis card (`templates/hypothesis.md`) before each experiment:
    - the one change, and what you deliberately left the same;
    - the metric you expect to move, by how much, and why (link the ceiling gap or profile line);
    - the metrics to watch for regressions;
    - "accept if" and "reject if", written down now.
    Never change the rule after seeing the numbers. A result the card did not predict is a reason to look closer, not a win.
12. **Prove the change ran.** A config flag, a new kernel or a default-on option does not prove that the server used it. After timing, record evidence from the real serving path in every phase the change claims: prefill, decode, verify, and every GPU rank. Use a short trace, a dispatch counter or a log line that only the new path prints. Without it, a "win" or a "no change" may measure the fallback. Set `"proof"` in the config to have `scripts/bench.py` record it.
13. **Resume from the record, not from memory.** After an agent restart, context reset or long pause, read `PLAN.md`, `verdicts.jsonl` and the ledger first. If an experiment has runs but no verdict, it is unfinished: rerun it. Never reconstruct a result you cannot find.

## 3. The loop

```
baseline → profile → zoom out: diagnose the bottleneck → lever for its cause → hypothesis card → config
   ↑                                                                                                 ↓
   │                                                              A/B with controls (queue.sh ctl cand ctl)
   │                                                                                                 ↓
   └── update best-config + PLAN.md + ledger ←── bench.py verdict + proof it ran ←── accept / reject ─┘
```

`scripts/bench.py verdict ctl-a cand ctl-b` applies rule 2 to the ledger. It accepts only if the candidate beats both controls on the target metric and nothing else is worse by more than 3%. It asks for a repeat when the controls drifted apart or the win is surprisingly large. Your judgement still decides; the tool keeps the rule from bending.

### Zoom out

Zoom out before the first lever, after every accepted change, after two rejects in a row or one result the card did not predict, and before you declare a plateau. Stop tweaking and do this (`references/diagnosis.md`):

1. **Build the time budget:** each part of the step, its exposed time, its floor. The largest gap is the bottleneck; a part near its floor is done.
2. **List the symptoms:** ceiling gaps, rejects inside noise, surprises, harness flags, control drift, gate failures.
3. **Form at least two competing theories.** For each, write the symptoms it explains, the ones it does not, and a prediction the others do not make.
4. **Run a discriminating probe,** not a tweak. It changes nothing you keep; it only separates the theories.
5. **Fix at the cause** with one change. Name the theory and the symptoms it should remove on the hypothesis card.
6. **Score the whole system:** speed, quality (looping, greedy equivalence, matched-ID accuracy) and reliability (failed requests, sample spread, memory peak, needles). `bench.py verdict` compares only the speed metrics and `mem_peak_gib` with the controls, and rejects any run with a flag (`LOOP`, `REQ_FAIL`, `NEEDLE_MISS`, `NO_PROOF`, `MEM_CAP`, `MEM_PROBE_FAIL`, `ON_BATTERY`). Greedy equivalence, accuracy and sample spread are your checks: ACCEPT does not mean quality was checked.

Record each zoom-out as a dated `## Diagnosis` section in `THEORY.md`. Keep refuted theories with the reason.

### Lever order

This is the default order, cheapest first, for when the diagnosis does not point at a cause. A diagnosed cause goes first. See `references/levers.md` for evidence.

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
7. **Kernel work:** profile, read the ISA, fix the dominant kernel. Do this only after config levers plateau. Follow the inner loop in `references/kernel-work.md`:
   - Pick the kernel by *exposed* time on the timeline, not by its share of summed kernel time (`references/profiling.md`).
   - Compute its own floor: bytes ÷ bandwidth if memory bound, FLOPs ÷ practical peak if compute bound. The gap to the floor is what this kernel can still give.
   - One variable per version. Keep every old version; never overwrite one.
   - Correctness first, at every row count M you serve. Then an interleaved microbenchmark. Then proof it ran. Then the end-to-end A/B, which is the only test that accepts.

### When a lever fails

- **If kernel-count reductions (fusion) give nothing** under graphs, the time is inside the main kernels. Stop fusing.
- **If higher acceptance doesn't give higher tok/s,** the draft costs too much. Measure per-step time.
- **If a weird result appears,** suspect the measurement first: tokens counted per streamed chunk, prompt length not measured with the real tokenizer, cache hits, thermal state, or the battery.
- **If a kernel wins in a microbenchmark but not end to end,** check three things in order:
  - Did the new kernel run in serving (rule 12)?
  - Did the time just move to the next join? On a timeline, the consumer now waits longer.
  - Did the microbenchmark see warm caches that serving never sees? Rotate weights or flush between iterations.
- **If summed kernel time exceeds step time,** kernels overlap. A kernel's share of the sum is not time you can remove.
- **If one GPU in a tensor-parallel group is faster,** its spare time shows up as waiting inside the collective. The slowest rank sets the step. Profile every rank.

### Plateau

Before you declare a plateau, zoom out once. Three levers inside noise often treated symptoms of one cause that is not on this list. Declare a plateau when three consecutive levers land inside noise and the zoom-out finds no new cause. Write a STATUS section in `PLAN.md` with:

- best numbers vs baseline vs ceiling;
- what limits further gains, with evidence;
- the latest diagnosis from `THEORY.md`: the budget, and the theories with their status;
- a ranked list of the remaining levers and their estimated cost.

Then keep the loop alive at a slower cadence if the user said "don't stop", or hand back.

## 4. Qualify and publish

See `references/publishing.md`.

- Pin weights by revision, engine by image digest or source commit, and kernels by commit. Build the published artifact from those pins in a clean checkout, never from a dirty tree.
- Run the acceptance gates on the clean build: load, chat, reasoning, tools round-trip, a long-context needle, and speed.
- Then A/B the clean build against your best image to prove they match.
- Report which numbers come from which harness. Gate numbers (e.g. thinking on, first 30 s) and hill-climb numbers (thinking off, medians) are not comparable.
- Keep four kinds of evidence apart, because none of them stands in for another:
  - operator correctness (the kernel test);
  - dispatch coverage (proof the path ran, rule 12);
  - task accuracy;
  - speed.
- A small accuracy difference that is not significant does not prove the two builds are equivalent. To claim equivalence, set a margin before the run and use enough samples.

## 5. Reporting to the user

- **Start with a table:** metric, baseline, now, ceiling, how it was measured (median of N, cold or warm, which harness).
- **Then:** what got the gains, why it stops here, the known limitations, and the system state you changed (power profile, running servers, uncommitted code, branches that must not be deleted).
- **Say plainly** what was not verified.
- **Define every throughput number:**
  - per-GPU throughput is total ÷ physical GPUs, never divided again by the tensor-parallel size;
  - say whether an acceptance length counts only accepted drafts or also the target's bonus token;
  - tokens per step is not latency per token.
- **When asked to free the GPU:** drain, stop the server, confirm no processes and an idle clock, and end any loop.
