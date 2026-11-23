# Computing theoretical ceilings

Measure the hardware; don't trust the spec sheet. A device-to-device copy of a large buffer gives realistic bandwidth. A large square FP16/BF16 GEMM (4096³ and 8192³) gives realistic compute; the larger one shows thermal and clock drop. Practical ceilings below assume about 100% of *measured* bandwidth and about 50% of measured peak FLOPs.

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

For a concurrency of N, dense weights are read once per step for all streams; experts follow the union of all rows' routing; KV is per stream. The aggregate ceiling therefore grows almost linearly with N until the expert union and per-stream KV dominate the bytes.

```
rows        = (k + 1) × N
step_bytes  = dense + lm_head + expert_bytes × (1 − (1 − top_k/n_experts)^rows) + N × kv_bytes(ctx) + draft_bytes
aggregate_ceiling = a × N × measured_bandwidth / step_bytes
```

Draft weights are read once per draft step for the whole batch, not once per stream.

## Tensor parallel

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

## Looped layers

Some models run a block of layers more than once per token (looped or recurrent-depth models). Count every pass:

- **Dense weights of the looped block:** read once per pass. A block of several GB does not stay in cache between passes.
- **Routed experts of a looped MoE block:** each pass routes on its own, so the experts touched are the union over passes. `rows = (k + 1) × N × passes` for that block's expert term.
- **Attention FLOPs and KV:** count every pass that has attention or writes KV. Check the model code. Some looped designs share KV across passes; others do not.
- **Prefill FLOPs:** count the block's active parameters once per pass.

`scripts/ceiling.py` takes `tp`, `replicated_gb`, `comm_ms_per_step`, `loops`, `looped_dense_gb`, `looped_experts_gb` and `looped_active_params_b` for these terms. Leave them out for a single-card model with no looped block.

## One kernel

Once you reach lever 7, ceiling each dominant kernel on its own: its arithmetic intensity against the measured machine balance, then its floor time. See `kernel-work.md`, "Roofline for one kernel". The model ceiling says how far the whole step can go. The kernel floor says which kernel still has room.

## Prefill (compute bound)

```
flops_per_token ≈ 2 × active_linear_params
                + 4 × n_full_attn_layers × n_heads × head_dim × position   (causal: average position = L/2)
                + linear-attention / SSM terms
prefill_ceiling(L) ≈ 0.5 × measured_peak_flops / mean_flops_per_token(L)
```

Int8/FP8 tensor cores double the peak for the parts that use them. For MoE, small per-expert row counts at a given chunk size lower GEMM efficiency; that is usually the biggest gap.

## TTFT, startup, KV

- **Short-prompt TTFT floor:** one forward pass (bytes ÷ bandwidth) plus tokenize and schedule. That is typically 30–60 ms on a laptop and a few ms on datacenter GPUs.
- **Startup floor:** weight bytes ÷ disk or page-cache speed, plus allocation. That is about 10 s when kernel JIT, autotune and graph-capture caches persist.
- **KV:** `bytes/token = n_kv_layers × 2 × n_kv_heads × head_dim × bytes_per_elem` (+ the draft layer's own KV). Then `max_full_length_streams = (memory_cap − weights − state − runtime) / (bytes/token × context)`.

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

**Single-user decode ceilings (practical, at 115 GB/s):**

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

`scripts/ceiling.py` does this arithmetic from a small JSON of component sizes.
