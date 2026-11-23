# Kernel work (lever 7)

Start here only after the config levers plateau (`SKILL.md`, section 3). Kernel work costs the most and goes wrong most quietly.

Most of this file is design rules from common GPU-kernel practice. Unlike `levers.md`, they were **not** measured in this skill's hill-climbs, except where a line says so. Treat them as priors to test with the loop below, not as results.

## The inner loop

1. **Profile a warmed step with graphs on.** Find the kernel with the most *exposed* time: time that nothing else overlaps. See `profiling.md`.
2. **Write down the shapes it really sees.** List M, K, N and the dtypes for every phase you serve:
   - prefill chunk;
   - decode, M = 1;
   - speculative verify, M = k;
   - concurrency N, M = N or N × k.

   Under tensor parallel, use the shard shape on one card, not the full model shape.
3. **Roofline it** (next section). Compute the kernel's floor time and the gap to it.
4. **Fill in a hypothesis card** (`templates/hypothesis.md`). Change one variable, for example:
   - vector width;
   - block size;
   - split factor;
   - tile shape;
   - pipeline stages;
   - data layout.

   Mechanical edits that support that one change are fine. A second tactic is not.
5. **Make a new version.** Use `kernels/<name>/v<K+1>/`. Never edit an older version, and keep the ones that regressed. They are part of the record.
6. **Run the correctness ladder** (below) at every M you serve.
7. **Microbenchmark** against the previous version (rules below). Record achieved bandwidth or FLOPs next to the floor.
8. **Build it into the engine and prove it runs** in serving (`SKILL.md` rule 12).
9. **Run the end-to-end A/B with controls** (`queue.sh ctl cand ctl`, then `bench.py verdict`). This is the only step that accepts. A microbenchmark win alone is not a win.
10. **Log it** in `PLAN.md`, including the rejects and why they failed.

Stop work on one kernel when either is true:

- three versions in a row land inside noise (the plateau rule, applied per kernel);
- its remaining gap to its floor is smaller than the next kernel's gap.

## Roofline for one kernel

For a matmul of M×K by K×N:

```
flops     ≈ 2 × M × K × N
bytes     ≈ M×K×act_bytes + K×N×weight_bytes (+ scales) + M×N×out_bytes
intensity = flops / bytes
balance   = measured_peak_flops (for the unit the kernel really uses) / measured_bandwidth
```

- **Below the balance, the kernel is memory bound.** Its floor is `bytes / measured_bandwidth`. Judge it by achieved bandwidth (`bytes / kernel_time`).
- **Above the balance, it is compute bound.** Its floor is `flops / practical_peak`.
- **Decode at M = 1** has an intensity of about 1 FLOP per byte with 16-bit weights. That is about two orders of magnitude below the balance of any recent GPU. No tuning makes it compute bound. Speculative verify at M = k raises intensity about k times. For small k it stays memory bound.
- **Use the peak of the unit the kernel really runs on.** If the card has no tensor cores for the dtype (bf16 on Volta or Turing, for example), use the FP16 or FP32 peak the code actually uses.
- **A reference point from this skill's own run:** the B390 verify-graph GEMVs reached about 76 of 115 GB/s, roughly 66% of measured copy bandwidth (`ceilings.md`). Published guidance for decode weight-load kernels aims at 60% of peak bandwidth or more. Below 40% usually means too few blocks or uncoalesced loads.

## Decode matmul (small M)

- **Fill the card.** A grid of `ceil(N / BLOCK_N)` blocks is too small whenever `N / BLOCK_N` is below the SM count. Aim for at least 2–4 blocks per SM.
  - Under tensor parallel, each card sees N/tp (column-parallel) or K/tp (row-parallel). Grids shrink, so check the grid per card.
- **Use split-K when the grid is too small.** Split the reduction over more blocks:

  ```
  S ≈ ceil(SMs × blocks_per_SM_target / (M_blocks × N_blocks))
  ```

  Keep each split at least about 512–1024 K elements, or the extra reduction costs more than it saves. If you need run-to-run determinism, fix the reduction order.
- **Use wide loads:** the widest aligned loads (128-bit), contiguous along K, coalesced across the warp. Check them in the SASS.
- **Fuse dequantization into the main loop** for weight-only quantized formats. A separate dequant pass reads the weights twice and erases the gain from quantization.
- **For storage-only dtypes, convert on load and accumulate in FP32.** These are dtypes the card has no math for, such as bf16 before Ampere. Read the SASS to see the conversion cost. In CUDA 12.8, bf16 → fp32 below sm_90 is a single `mov.b32` (`cuda_bf16.hpp`, `__internal_device_bfloat162float`), so the cost is in the loads, not the conversion.
- **Do not chase tensor-core use in decode.** Idle tensor cores at M = 1 are a symptom of being memory bound, not a fault.
- **Launch overhead mostly disappears under graphs.** In this skill's runs, three fusions under graphs were correct and gave 0% (`levers.md`). Reach for persistent kernels or fusion against launch overhead only where graphs are not available.

## Decode attention

- **Split along the KV sequence** (split-KV, "flash-decoding"), not along queries: M is 1, or k when verifying.
- **Keep the running max and sum of exponentials for each split in FP32,** and combine the splits with a log-sum-exp (LSE) merge. Adding up normalised partial outputs without the LSE correction gives wrong probabilities, silently.
- **KV bytes per step** = `n_kv_layers × 2 × n_kv_heads × head_dim × past_len × bytes`. At long context this can exceed the weight bytes. Then more matmul work gains nothing; profile the split first.
- **Read KV with vectorised loads,** contiguous along the sequence. With paged KV, check that the page-table lookup keeps loads coalesced.
- **Order the KV append:**
  - in plain decode, write the new K/V after the reads of the past;
  - in tree verify, make each row see exactly the rows it depends on.
- **Run verify (M = k) as decode-style attention.** This skill measured it: with verify rows run as decode queries, SGLang on the B70 reached 82.6 tok/s at c1, against 75.7 for vLLM on the same card (`levers.md`).

## Prefill

- **Try a library first:** use large tiles, tensor cores and FP32 accumulation, from cuBLAS(Lt), CUTLASS, hipBLASLt or oneDNN, before writing your own. This skill measured a hand-written flash attention at 48 TFLOPS against a library's 61 (`levers.md`).
- **MoE grouped GEMMs** see few rows per expert at a given chunk size. Avoid padding cliffs. This is measured in `levers.md`.
- **Align the chunk size** with the tile M of the GEMM and attention kernels. A mismatch forces masked partial tiles on every chunk.

## Tensor-core shapes differ by generation

Do not copy tile rules from one generation to another. Check the PTX ISA guide for your target.

| Generation | fp16 MMA shape | Notes |
|---|---|---|
| Volta (sm_70) | `mma.sync` m8n8k4; `wmma` 16×16×16 | no bf16 MMA, no async copy |
| Ampere (sm_80) and later | `mma.sync` m16n8k16 | adds `cp.async` |
| Hopper (sm_90) | — | adds `wgmma` and TMA |

## Correctness ladder

Keep the 4-level lossless check in `levers.md`:

1. weights bit-identical;
2. each layer against fp64;
3. graph against eager;
4. model KL.

Add these checks:

- **Set tolerances per dtype before you look at the candidate's errors.**
  - bf16 has 8 significant bits and fp16 has 11, so a bf16 path needs a looser tolerance than fp16. It must never get the FP32 one.
  - A stronger test: compare old and new against an FP32 or FP64 reference, and require the new error to be no worse than the old.
- **Split reductions:** test split factors 1, 2, 4, 8 and one that is not a power of two, each against the unsplit result.
- **Integer outputs must match exactly:** expert IDs, indices, offsets. For top-k, compare the selected *sets*, because slot order can differ on ties.
- **Edge rows:**
  - an empty batch (M = 0);
  - padded or masked rows;
  - the largest M you serve;
  - graph buffers reused across replays.
- **Rounding points:** folding norms, RoPE, residual adds or quantization into one kernel can round differently even when the algebra is equal. Test the original rounding, not just the formula.
- **Run `compute-sanitizer` once on each new kernel** (`--tool memcheck`, then `racecheck`).

## Reading the ISA

- **`nvcc -Xptxas -v`** prints registers, spills and shared memory per kernel. A spill in a hot kernel is the first suspect.
- **`-lineinfo`** lets ncu map stalls to source lines without a debug build. Debug builds change code generation (`methodology.md`).
- **`cuobjdump -sass`** or **`nvdisasm`** show what the compiler actually emitted. Look for:
  - the load width you meant (128-bit global loads);
  - conversion instructions;
  - predicated or serialized tails;
  - per-element register moves. This skill measured one on the B70: the LM head went from 4.05 to 1.72 ms after removing them (`levers.md`).

## Microbenchmark rules

These extend `methodology.md` (interleaved min-of-N, clock ramp-up):

- **Use the shapes serving uses,** per card, at every M from step 2.
- **Make caches look like serving.** Rotate through weight buffers larger than the L2, or flush between iterations, so every iteration reads from DRAM. A weight that sits in L2 makes a GEMV look several times faster than it is.
- **Run old and new in the same process,** interleaved. Report the min and the median, with the clocks fixed or recorded.
- **A microbenchmark explains; it does not accept.** Only the end-to-end A/B accepts.
