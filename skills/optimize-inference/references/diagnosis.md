# Zoom out: diagnose the cause before the next lever

The loop in `SKILL.md` climbs one lever at a time. That works while each lever hits the real bottleneck. When it does not, you treat symptoms one by one and land inside noise. Zooming out means: stop tweaking, list every symptom, and find the one cause that explains several of them. Then fix that cause and score the whole system again.

## 1. When to zoom out

- **After the baseline and the ceilings,** before the first lever.
- **After every accepted change.** The bottleneck moves, so the old diagnosis is out of date.
- **After two rejects in a row,** or one result that the hypothesis card did not predict.
- **Before you declare a plateau.** Three levers inside noise often treated symptoms of one cause that is not on the lever list.

## 2. Build the time budget

Split the time of the metric you chase (decode step, TTFT, prefill per token, startup) into parts. For each part, record:

- **Measured:** its exposed time on the timeline, not its share of summed kernel time (`profiling.md`).
- **Floor:** its theoretical time, from `THEORY.md` and `ceilings.md`.

```markdown
| Part | Measured (ms) | Floor (ms) | Gap (ms) | Evidence |
|---|---|---|---|---|
| <part> | <exposed time> | <floor> | <measured − floor> | <profile file, ceiling line> |
```

Parts of a decode step:

- weight read (dense layers);
- KV and attention read;
- MoE routing and experts;
- LM head and sampling;
- draft model (speculative decoding);
- communication (tensor parallel);
- host gaps and launch;
- idle.

The part with the largest gap (measured − floor) is the bottleneck. A part already near its floor is done, however big it is. In one 32K prefill, GEMMs were 40% of the time and already at the int8 ceiling, so more GEMM work was pointless (`levers.md`).

## 3. List the symptoms

Collect them from `PLAN.md`, `verdicts.jsonl` and the harness flags:

- gaps to the ceiling, per metric;
- rejects inside noise;
- surprises: results the card did not predict;
- harness flags: `LOOP`, `REQ_FAIL`, `NEEDLE_MISS`, `NO_PROOF`, `MEM_CAP`, `MEM_PROBE_FAIL`, `ON_BATTERY`;
- checks you do yourself (`methodology.md`, output sanity): idle GPU, prefill inside the decode window, KV-bound admission;
- drift between the two controls of one A/B;
- stability gate failures (needles, soak, greedy equivalence).

## 4. Form competing theories

For each candidate cause, write:

- the symptoms it explains;
- the symptoms it does not explain;
- a prediction that differs from the other theories;
- a discriminating test.

Keep at least two theories until a test separates them. Prefer the cause that explains the most symptoms. A theory that explains every symptom, whatever the result, predicts nothing.

## 5. Discriminating tests (probes, not tweaks)

A probe changes nothing you will keep. It only separates theories. Examples:

- **Grow batch M from 1 to 4.** If step time stays flat, the step is memory bound or fixed overhead.
- **Grow context at fixed batch.** If decode falls, KV and attention read are a large part.
- **Compare host gaps with queue time** (`nsys stats -r cuda_kern_exec_sum`, `profiling.md`). Short execution with long host gaps means the host is the bottleneck.
- **Graphs on vs off.** The difference is launch and host overhead.
- **Speculative decoding off.** This gives the target-only step time; the rest of the step is draft cost.
- **Profile every tensor-parallel rank.** Waiting inside the collective shows which rank is slow.
- **Repeat the control an hour later, or on AC vs battery.** A change means the environment, not the config.
- **Check `cached_tokens`.** A nonzero value means the prompt hit the prefix cache.

## 6. Known symptom clusters

| Symptoms | Likely common cause | First probe | Levers it points to |
|---|---|---|---|
| Fusion gives ~0% under graphs; idle tensor cores at M = 1; decode close to the byte floor | Main GEMV/GEMM is memory bound (`levers.md` fusion line; `kernel-work.md` tensor-core line) | Grow M from 1 to 4; compare achieved bandwidth with measured bandwidth | Fewer bytes per weight; speculative decoding |
| Higher acceptance but lower tok/s | Draft step cost. A 7-token draft accepted 3.26 vs MTP's 2.85, yet ran 11–14% slower (`methodology.md`) | Measure ms per verify step, spec on and off | Prune the draft LM head; shorter draft |
| c1 fine, cN stops scaling; KV-bound admission | KV pool or state slots cap concurrency (`levers.md`, hybrid models) | Check how many requests run at once | Size slots and pool; concurrent soak |
| Short-prompt TTFT high; kernels short; host gaps | Scheduler, tokenizer, chat template or sampler (`levers.md`, TTFT line) | Host gaps vs queue time | Host-side fixes before kernels; sampling on the GPU |
| Same config drifts 5–10% or more; laptop slower | Power, thermals, background load (`methodology.md`, noise) | Repeat the control on AC, idle host, fixed profile | Fix the environment before any lever |
| One TP rank waits inside the collective | Rank imbalance; the slowest rank sets the step (`profiling.md`) | Profile every rank, aligned on the collective | Balance shards; fix the slow rank |
| Long, variable startup | JIT cache misses or slow mmap loading (`levers.md`, startup lines) | Time a second start; check cache directories | Persistent caches; eager safetensors loading |
| OOM at some shapes only | Memory outside the framework allocator (`levers.md`) | Track the peak per shape | Route scratchpads through the allocator; pad shapes to buckets |
| A record speed with a looping flag | Broken output, not speed. A 117 tok/s "record" was a numbered list in a loop (`methodology.md`) | Read the output | None until the output is correct |

## 7. Fix at the cause

- **One change that removes the cause beats one tweak per symptom.** It is still one change per experiment (`SKILL.md` rule 1).
- **The hypothesis card names the theory** and the symptoms the change should remove.
- **After the run, check those symptoms.** If the target moved but the symptoms stayed, the theory is partly wrong. Update it before the next lever.

## 8. Score the whole system, not one number

After each accepted change, check all three again:

- **Speed:** every metric in section 0 of `SKILL.md`, not only the target.
- **Quality:** looping flags; greedy equivalence for lossless claims; matched-ID accuracy for lossy trades (`methodology.md`, accuracy evidence).
- **Reliability:** failed requests, spread across samples, memory peak against the cap, needle results.

`bench.py verdict` does part of this. It compares the speed metrics and `mem_peak_gib` with both controls, and rejects any run with a flag (`LOOP`, `REQ_FAIL`, `NEEDLE_MISS`, `NO_PROOF`, `MEM_CAP`, `MEM_PROBE_FAIL`, `ON_BATTERY`). It does not check greedy equivalence, accuracy or sample spread. Run those yourself and write the result on the hypothesis card. ACCEPT from the tool does not mean quality was checked.

A speed win that costs quality or reliability is a rejection, unless the user allowed that trade in section 0.

## 9. Record it

Add a dated `## Diagnosis` section to `THEORY.md` for each zoom-out:

- the budget table;
- the symptom list;
- the theories, each with a status (open, confirmed or refuted) and its evidence;
- the next probe or lever.

Keep refuted theories with the reason. Never delete them.
