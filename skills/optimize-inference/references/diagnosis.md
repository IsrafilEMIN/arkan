# Zoom out: diagnose the cause before the next lever

The loop in `SKILL.md` climbs one lever at a time. That works while each lever hits the real bottleneck. When it does not, you treat symptoms one by one and land inside noise. Zooming out means: stop tweaking, compare the whole system with the hardware ceiling, find the root cause that explains several symptoms, and attack the largest checked gap.

## 1. When to zoom out

- **After the baseline and the ceilings,** before the first lever.
- **After every accepted lever.** The bottleneck moves, so the old diagnosis is out of date.
- **After two rejects in a row,** or one result that the hypothesis card did not predict.
- **Before you declare a plateau.** Three levers inside noise often treated symptoms of one cause that is not on the lever list.

Every zoom-out starts from a fresh measurement of the current control, never from an old trace.

## 2. The loop

1. **Zoom out:** the whole system against the hard ceiling and the practical ceiling at the current graph (`ceilings.md`), per metric and per depth bucket.
2. **Build the time budget** (section 3).
3. **Write at least two competing root theories,** each as "root X explains symptoms A, B, C" (section 5).
4. **Run a discriminating probe** on a fixed token path (section 6).
5. **A root's gap is the sum of the parts it explains.** Take the largest *checked* root gap.
6. **Name it and give the reason in one or two lines,** then attack it.
7. **Sum check** (section 8).

Rules for choosing:

- **Checked vs estimated.** A gap is checked when a probe measured it; otherwise it is estimated. An estimated gap needs a probe before it can go first.
- **The size of a known fix is not the size of the gap.** Rank by the gap, then look for the fix.
- **Parts stay listed even with no known fix.** A large gap with no fix is the reason to propose a structural change.
- **No menus of levers.** Pick the root and attack it. Ask the user for a go/no-go only above the user's threshold, asked once in section 0 and stored in `PLAN.md`. Default threshold: a redesign, multi-day work, a quality-class change, or an area the user excluded.
- **"Cheapest first" is only a tie-breaker,** and the order for the first levers before a budget exists.

## 3. Build the time budget

Split the time of the metric you chase (decode step, TTFT, prefill per token, startup) into parts.

- **Split prefill and decode first,** then rank inside each phase. A prefill kernel ranked against decode kernels is noise in both lists.
- **Budget per context-depth bucket** (`methodology.md`, context depth). The bottleneck at 100% of the context target is often not the one at short context.
- **Measured** is the part's attributed exposed time on the timeline, not its share of summed kernel time. `python3 scripts/budget.py summary TRACE --floors floors.json` gives it per device and phase (`profiling.md`).
- **Floor** is its theoretical time, from `THEORY.md` and `ceilings.md`.

```markdown
| Phase | Depth | Part | Measured (ms) | Floor (ms) | Gap (ms) | Checked / estimated | Evidence |
|---|---|---|---|---|---|---|---|
| decode | 50% | <part> | <exposed time> | <floor> | <measured − floor> | <probe name or "estimated"> | <trace, ceiling line> |
```

Parts of a decode step:

- weight read (dense layers);
- KV and attention read;
- MoE routing and experts;
- LM head and sampling;
- draft model (speculative decoding);
- communication (tensor or pipeline parallel);
- dependent-kernel chain latency and work that moves no bytes (`ceilings.md`);
- host gaps and launch;
- idle.

A part already near its floor is done, however big it is. In one 32K prefill, GEMMs were 40% of the time and already at the int8 ceiling, so more GEMM work was pointless (`levers.md`).

### Fixed and per-row cost across concurrency

Fit the step time across concurrency (`python3 scripts/workloads.py clients --n 1,2,4,8`):

```
step_ms(N) ≈ fixed_ms + N × per_row_ms
```

- **`fixed_ms`** is paid once per step: weight reads, launches, syncs, chain latency.
- **`per_row_ms`** grows with each stream: KV and attention reads, expert union growth, sampling.

A lever must cut the term that dominates at the served concurrency. Fewer bytes per weight helps `fixed_ms`; a KV format helps `per_row_ms`.

## 4. List the symptoms

Collect them from `PLAN.md`, `verdicts.jsonl`, the ledger and the harness flags:

- gaps to the ceiling, per metric and depth;
- rejects inside noise, `BELOW_BAR` results;
- surprises: results the card did not predict;
- ledger flags: `LOOP`, `REQ_FAIL`, `NEEDLE_MISS`, `TEST_FAIL`, `NO_PROOF`, `MEM_CAP`, `MEM_PROBE_FAIL`, `ON_BATTERY`, `HOST_BUSY`, `LOW_N`; verdict flags: `NOISY`, `ANSWER_DIFF`;
- checks you do yourself (`methodology.md`, output sanity): idle GPU, prefill inside the decode window, KV-bound admission;
- drift between loads of the same config;
- gate failures (needles, soak, quality evidence from `quality.md`).

## 5. Form competing root theories

For each candidate root, write:

- "root X explains symptoms A, B, C";
- the symptoms it does not explain;
- the budget parts it explains, and their summed gap;
- a prediction that differs from the other theories;
- a discriminating probe.

Keep at least two theories until a probe separates them. Prefer the root that explains the most symptoms. A theory that explains every symptom, whatever the result, predicts nothing.

## 6. Probes before levers

A probe changes nothing you will keep. It only measures a gap or separates theories. Probes are never kept or accepted.

**Run probes on a fixed token path:** teacher-forced tokens, a forced acceptance length, replayed routing. Report ms per step, never tok/s; tok/s mixes the step cost with acceptance and routing changes.

| Probe | What it does | Read it as |
|---|---|---|
| Ablation | A test-only variant removes one cost: memory bytes (weights cache-resident or zeroed), compute, syncs, lookups. | The step time the part costs. Two limits within ~20% of each other are co-limited: test the combined change as one experiment. |
| Upper bound | Untraced, in the real engine: skip or stub the part and time the whole step. | The most a fix of that part can give. The next join absorbs part of it, and copy-only time is not idle time. |
| Gain vs noise | Write the upper bound next to the bar from `methodology.md` on the card. | Below the bar: bundle it with related parts, reduce noise, or skip it. |
| Trace and replay | For offload or cache designs: record the real access trace from the engine (experts, pages or blocks touched per step at served settings), then replay it against the proposed policy offline. | Hit rate and bytes moved per step before you build anything. |
| Time cap | About 2 h of bench-only work on one part (rig or user can change it). | Stop and zoom out. |

Engines that cannot force tokens or stub a part: use a config-level stand-in (the feature off, at fixed prompt and output length). If no stand-in exists, mark the gap "estimated".

Other discriminating probes:

- **Grow batch M from 1 to 4.** If step time stays flat, the step is memory bound or fixed overhead.
- **Grow context at fixed batch.** If decode falls, KV and attention reads are a large part.
- **Compare host gaps with queue time** (`nsys stats -r cuda_kern_exec_sum`, `profiling.md`). Short execution with long host gaps means the host is the bottleneck.
- **Graphs on vs off.** The difference is CPU launch and host overhead. Per-node fill/drain and dependent-chain latency stay under graphs.
- **Speculative decoding off.** This gives the target-only step time; the rest of the step is draft cost.
- **Profile every rank.** Waiting inside the collective shows which rank is slow.
- **Repeat the control later, or on AC vs battery.** A change means the environment, not the config.
- **Check `cached_tokens`.** A nonzero value means the prompt hit the prefix cache.

## 7. Known symptom clusters

| Symptoms | Likely common cause | First probe | Levers it points to |
|---|---|---|---|
| Fusion gives ~0% under graphs; idle tensor cores at M = 1; decode close to the byte floor | Main GEMV/GEMM is memory bound (`levers.md` fusion line; `kernel-work.md` tensor-core line) | Grow M from 1 to 4; compare achieved bandwidth with measured bandwidth at the real read size | Fewer bytes per weight; speculative decoding |
| Decode far above bytes ÷ bandwidth; many small dependent kernels; graphs on | Chain latency and work that moves no bytes (`ceilings.md`, practical at the current graph) | Ablate syncs or stub small kernels on a fixed token path | Structural lever: fewer dependent steps, overlap (`levers.md`) |
| Higher acceptance but lower tok/s | Draft step cost. A 7-token draft accepted 3.26 vs MTP's 2.85, yet ran 11–14% slower (`methodology.md`) | Measure ms per verify step, spec on and off | Prune the draft LM head; shorter draft |
| c1 fine, cN stops scaling; KV-bound admission | KV pool or state slots cap concurrency (`levers.md`, hybrid models) | Check how many requests run at once; fit fixed + per-row cost | Size slots and pool; concurrent soak |
| Short-prompt TTFT high; kernels short; host gaps | Scheduler, tokenizer, chat template or sampler (`levers.md`, TTFT line) | Host gaps vs queue time | Host-side fixes before kernels; sampling on the GPU |
| Same config drifts 5–10% or more; laptop slower | Power, thermals, background load (`methodology.md`, noise) | Repeat the control on AC, idle host, fixed profile | Fix the environment before any lever |
| One rank waits inside the collective | Rank imbalance; the slowest rank sets the step (`profiling.md`) | Profile every rank, aligned on the collective | Balance shards; fix the slow rank |
| Long, variable startup | JIT cache misses or slow mmap loading (`levers.md`, startup lines) | Time a second start; check cache directories | Persistent caches; eager safetensors loading |
| OOM at some shapes only | Memory outside the framework allocator (`levers.md`) | Track the peak per shape | Route scratchpads through the allocator; pad shapes to buckets |
| A record speed with a looping flag | Broken output, not speed. A 117 tok/s "record" was a numbered list in a loop (`methodology.md`) | Read the output | None until the output is correct |

## 8. Sum check

After choosing the root, add up the predicted gains of the planned levers. Scale them down by the measured prediction ratio so far (measured gain ÷ predicted gain over accepted and rejected cards). Compare the result with the target.

- **Enough:** go on with the planned levers.
- **Short:** propose the structural change now (`levers.md`, structural lever), not after the small levers run out.

## 9. Fix at the cause

- **One change that removes the cause beats one tweak per symptom.** It is one change per experiment, except when an ablation shows two limits within ~20% of each other: then the combined change is the one experiment.
- **The hypothesis card names the root** and the symptoms the change should remove.
- **After the run, check those symptoms.** If the target moved but the symptoms stayed, the theory is partly wrong. Update it before the next lever.

## 10. Score the whole system, not one number

After each accepted lever, check all three again:

- **Speed:** every metric in section 0 of `SKILL.md`, at the depth buckets the change touches.
- **Quality:** the evidence the quality contract asks for this change class (`quality.md`).
- **Reliability:** failed requests, noise flags, memory peak against the cap, needle results.

`bench.py verdict` compares the speed metrics and `mem_peak_gib` with the control and rejects any run with a blocking flag. It does not prove quality. ACCEPT from the tool does not mean quality was checked.

A speed win that costs quality or reliability is a rejection, unless the user allowed that trade (`quality.md`, quality contract).

## 11. Record it

Add a dated `## Diagnosis` section to `THEORY.md` for each zoom-out:

- the ceilings and the budget table, per phase and depth;
- the symptom list;
- the root theories, each with a status (open, confirmed or refuted), checked or estimated, and its evidence;
- the sum check;
- the chosen root and the next probe or lever.

Keep refuted theories with the reason. Never delete them.
