# Computing theoretical ceilings

Measure the hardware; don't trust the spec sheet. Run these short microbenchmarks once per rig and store the results in `rig.json` `microbench`:

| Input | How | `rig.json` key |
|---|---|---|
| Bandwidth at the real read size | Device copy at the sizes the engine reads per kernel (one layer's weights, one expert, one KV block), not only one large buffer. Small reads reach less. | `bw_gbs_by_read_mib` |
| Cost per chain node | A chain of dependent tiny kernels, captured in a graph if the engine uses graphs; time per node. | `chain_node_us` |
| Link bandwidth | The real exchange size between cards, under real concurrent traffic; P2P and host staging separately (Links, below; `gotchas.md`, P2P). | `link_gbs` |
| Peak FLOPs at the served cap | A large square FP16/BF16 GEMM (4096³ and 8192³) at the served power cap and clocks; the larger one shows thermal and clock drop. | `peak_tflops_at_cap` |

A platform that cannot run one of them records it as not available; use the spec value and mark that ceiling "estimated".

## Hard ceiling and practical ceiling

```
hard_step      = bytes / bandwidth
practical_step = bytes / bandwidth
               + n_dependent_kernels × chain_node_us        # measured cost per chain node
               + nonbyte_us                                  # top-k, syncs, recurrence, sampling: work that moves no bytes
structural_budget = practical_step − hard_step
```

- **The hard ceiling** is bytes ÷ bandwidth. Nothing reads fewer bytes faster.
- **The practical ceiling, at the current graph,** adds the latency of the chain of dependent kernels and the work that moves no bytes. It is not a floor: fusion, fewer dependent steps or overlap can go below it.
- **The structural budget** is the gap between the two. It is what a structural change can win (`levers.md`, structural lever).
- **Graphs remove CPU launch cost, not this chain cost.** Each node still pays its fill and drain on the GPU, and a dependent kernel cannot start before the previous one ends. Count the chain term with graphs on.

## Decode (memory bound)

Bytes read per target forward at short context:

```
B_target = dense_weight_bytes                    # attention / linear-attention, shared experts, router, norms
         + expert_bytes × (top_k / n_experts)    # MoE: only routed experts are read
         + lm_head_bytes                         # often 10–25% of the total on large vocabularies!
         + kv_bytes_per_token × context          # grows with context; dominates at long context
         + recurrent_state_bytes × 2             # SSM / GDN state read + write, if hybrid
```

Use the checkpoint's tensor sizes, which already include quantization. Don't use parameter count × bits.

With speculative decoding (k drafts, accepted length `a` tokens per step):

```
verify_bytes ≈ dense + lm_head + expert_bytes × (1 − (1 − top_k/n_experts)^(k+1))   # union of routed experts
draft_bytes  ≈ k × (draft_layer_bytes + draft_lm_head_bytes)                         # prune the draft head!
bytes_per_emitted_token = (verify_bytes + draft_bytes) / a
c1_ceiling = measured_bandwidth / bytes_per_emitted_token
```

Take `a` from the engine's acceptance counters at the served settings, never the configured draft length.

For a concurrency of N, dense weights are read once per step for all streams; experts follow the union of all rows' routing; KV is per stream. The aggregate ceiling therefore grows almost linearly with N until the expert union and per-stream KV dominate the bytes.

```
rows        = (k + 1) × N
step_bytes  = dense + lm_head + expert_bytes × (1 − (1 − top_k/n_experts)^rows) + N × kv_bytes(ctx) + draft_bytes
aggregate_ceiling = a × N × measured_bandwidth / step_bytes
```

Draft weights are read once per draft step for the whole batch, not once per stream.

## Context depth

Compute the ceiling per depth bucket (`methodology.md`, context depth), because the KV term grows with context:

- **Sparse or indexer attention:** KV bytes of the selected positions only, plus the indexer's own cost, which grows with context:

  ```
  kv_bytes(ctx) = kv_bytes_per_token × selected_tokens + indexer_bytes_per_ctx_token × ctx
  ```

- **Sliding window:** a sliding-window layer reads `min(pos, window)` positions, in KV bytes and in prefill attention FLOPs. Count full context only for the full-attention layers.

## Placement

When the model does not fit in VRAM, compute two ceilings:

```
as_placed_step = resident_bytes / vram_bw + nonresident_bytes / bw_that_serves_them   # host link, peer link, disk
if_it_fit_step = all_bytes / vram_bw
```

A large gap between them means the first lever is a format or placement that fits: fewer bits, a smaller KV dtype, or a different split. That is a quality trade the user decides (`levers.md`, placement and format; `quality.md`).

## Multi-GPU

### Tensor parallel

With the model split across `tp` GPUs, each card reads its shard plus everything that is replicated:

```
per_card_bytes = (step_bytes − replicated_bytes) / tp + replicated_bytes
step_time      = per_card_bytes / per_card_measured_bandwidth + comm_time_per_step
ceiling        = a × N / step_time
```

- **Replicated bytes:** norms, the router, embeddings and any unsharded LM head. Check which tensors your engine really shards.
- **`comm_time_per_step`** = all-reduces per step × the measured latency of one all-reduce at decode size. A Megatron-style layer has two all-reduces, one after attention and one after the MLP. Count them per executed layer.
  - At decode the payload is tiny (hidden × M × bytes), so latency sets the time, not link bandwidth.
  - Measure it with a microbenchmark of the collective your engine uses (NCCL, or custom peer-to-peer), on the same cards.
  - If `comm_time_per_step` is a large share of the step, more kernel work on one card cannot get you to the bandwidth ceiling.
- **Prefill** under TP: FLOPs split across cards, so the practical peak is `tp × per-card peak`. Communication grows with the chunk size. Measure whether it overlaps with compute before assuming it does.

### Layer or pipeline split

With layers split across cards and one request in flight (c1), only one card works at a time:

- **Ceiling:** one card's bandwidth over all bytes, plus the exchange at each split point. Two cards do not double c1.
- **Metric:** the time both cards are busy at once. More of it comes only from overlap: concurrent requests, or micro-batches in flight.

### Links

```
link_time_per_step = exchange_bytes_per_step / link_gbs
```

The faster of P2P and host staging on paper can lose under load.

## Looped layers

Some models run a block of layers more than once per token (looped or recurrent-depth models). Count every pass:

- **Dense weights of the looped block:** read once per pass. A block of several GB does not stay in cache between passes.
- **Routed experts of a looped MoE block:** each pass routes on its own, so the experts touched are the union over passes. `rows = (k + 1) × N × passes` for that block's expert term.
- **Attention FLOPs and KV:** count every pass that has attention or writes KV. Check the model code. Some looped designs share KV across passes; others do not.
- **Prefill FLOPs:** count the block's active parameters once per pass.

## One kernel

Once you reach kernel work, ceiling each dominant kernel on its own (`kernel-work.md`, "Roofline for one kernel"). The model ceiling says how far the whole step can go. The kernel floor says which kernel still has room.

## Prefill (compute bound)

```
flops_per_token ≈ 2 × active_linear_params
                + 4 × n_full_attn_layers × n_heads × head_dim × position   (causal: average position = L/2)
                + 4 × n_swa_layers × n_heads × head_dim × min(position, window)
                + linear-attention / SSM terms
prefill_ceiling(L) ≈ 0.5 × peak_flops_at_cap / mean_flops_per_token(L)   # practical peak ≈ 50% of measured peak at the served cap
```

Int8/FP8 tensor cores double the peak for the parts that use them. For MoE, small per-expert row counts at a given chunk size lower GEMM efficiency; that is usually the biggest gap (`levers.md`, MoE prefill chunk).

## TTFT, startup, KV

- **Short-prompt TTFT floor:** one forward pass (bytes ÷ bandwidth) plus tokenize and schedule. That is typically 30–60 ms on a laptop and a few ms on datacenter GPUs.
- **Startup floor:** weight bytes ÷ disk or page-cache speed, plus allocation. That is about 10 s when kernel JIT, autotune and graph-capture caches persist.
- **KV:** `bytes/token = n_kv_layers × 2 × n_kv_heads × head_dim × bytes_per_elem` (+ the draft layer's own KV). Then `max_full_length_streams = (memory_cap − weights − state − runtime) / (bytes/token × context)`.

## When ceilings go stale

Ceilings carry the hash of the config they were computed for. A change of quantization, card count, placement or power cap makes them stale: recompute before the next zoom-out.

## Worked example: Ornith-1.5-35B-A3B (Qwen3.5-MoE hybrid), EXL3 4 bpw, Intel Arc B390 iGPU

**Hardware (measured):**
- 115 GB/s copy bandwidth on 64 GB of LPDDR5X (153.6 GB/s spec).
- 35.8 TFLOPS FP16 at 4096³, dropping to 20 at 8192³.

**Model:** 40 layers: 30 GDN linear-attention plus 10 full-attention. 256 experts, top-8.

| Component | GB / target token |
|---|---:|
| Routed experts: 16.26 GB × 8/256 | 0.508 |
| Dense: GDN 0.515 + full attention 0.137 + shared expert 0.064 + router 0.042 | 0.758 |
| LM head (6-bit, 248K vocab) | 0.382 |
| **Total** | **1.648** |

**Single-user decode ceilings (hard, at 115 GB/s):**

| Mode | GB per emitted token | Ceiling |
|---|---:|---:|
| No speculation | 1.68 | 68 tok/s |
| 1 MTP draft, full draft head, a = 1.85 | 1.38 | 83 tok/s |
| 1 draft, pruned 32K-token draft head | 1.19 | 97 tok/s |
| 2 drafts, a ≈ 2.5 | 1.11 | ~103 tok/s |

The pruned draft head, about 8× fewer head bytes, was worth more than an extra draft.

**What happened in practice:**

- **c1 decode:** it reached ~53 tok/s, about 55% of the ceiling. The model's MTP head accepted only ~14% at depth 2, so the 2-draft row was unreachable. The remaining gap was the quantized GEMV kernels, at ~76 GB/s effective in the verify graph.
- **Prefill:** about 670 tok/s practical at 256K versus 628 achieved. Long-context prefill was close to its ceiling.
- **KV cache:** FP8 KV is 10,240 B/token, so 2.7 GB per 256K stream. Four full-length streams fit in about 11 GB under a 46 GiB cap.

## `scripts/ceiling.py`

It does this arithmetic from a small JSON of component sizes. Optional fields cover the terms above:

| Field | Term |
|---|---|
| `tp`, `replicated_gb`, `comm_ms_per_step` | tensor parallel |
| `loops`, `looped_dense_gb`, `looped_experts_gb`, `looped_active_params_b` | looped layers |
| `latency` {`n_dependent_kernels`, `node_us`, `nonbyte_us`} | practical ceiling at the current graph, structural budget |
| `placement` {`resident_gb`, `nonresident_gb`, `nonresident_bw_gbs`} | as placed vs if everything fit |
| `pipeline_split` | layer or pipeline split |
| `links` {`exchange_bytes_per_step`, `link_gbs`} | links |
| `sparse_attn` {`selected_tokens`, `indexer_bytes_per_ctx_token`} | sparse or indexer attention |
| `sliding_window` {`window`, `n_swa_layers`} | sliding window |
| `peak_tflops_at_cap` | prefill peak at the served cap |
| `depths` [ctx, ...] | per-depth ceilings |
| `config_hash` | staleness |

Leave out the fields that do not apply. `--out ceilings.json` writes the hard and practical ceiling per metric for `bench.py board`.
