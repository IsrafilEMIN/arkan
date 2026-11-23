#!/usr/bin/env python3
"""Theoretical ceilings for decode / prefill / KV from a small JSON of measured hardware and model sizes.

  python3 scripts/ceiling.py model.json

Example model.json (Ornith-1.5-35B-A3B EXL3 4bpw on an Arc B390 iGPU; sizes in GB from the checkpoint):
{
  "bandwidth_gbs": 115, "peak_tflops": 36, "mfu": 0.5,
  "dense_gb": 0.758, "experts_gb": 16.26, "top_k": 8, "n_experts": 256, "lm_head_gb": 0.382,
  "active_params_b": 2.43, "attn_layers": 10, "attn_heads": 16, "head_dim": 256,
  "kv_bytes_per_token": 10240, "draft_layer_gb": 0.03, "draft_head_gb": 0.05,
  "spec": [{"drafts": 0, "accept": 1.0}, {"drafts": 1, "accept": 1.74}, {"drafts": 2, "accept": 2.5}],
  "contexts": [4096, 32768, 131072, 262144], "concurrency": [1, 4]
}
Dense models: set experts_gb to 0. draft_head_gb is the draft LM head as read per draft step (prune it!).

Optional fields. Leave them out for a single-card model with no looped block.
  "tp": 2                      tensor-parallel size. bandwidth_gbs and peak_tflops are then PER CARD.
  "replicated_gb": 0.05        GB per step that every card reads in full (replicated norms, router, embeddings,
                               an unsharded LM head...). Everything else is taken as sharded 1/tp.
  "comm_ms_per_step": 0.4      measured communication floor per decode step: all-reduces per step x the
                               measured latency of one all-reduce at decode size. Added to every step.
  "loops": 3                   passes of a looped block per token (looped / recurrent-depth models).
  "looped_dense_gb": 0.2       part of dense_gb that belongs to the looped block; read once per pass.
  "looped_experts_gb": 10.0    part of experts_gb that belongs to the looped block. Routing is independent per
                               pass, so the experts read are the union over all passes.
  "looped_active_params_b": 1  active params of the looped block, for prefill FLOPs (once per pass).
  Count attn_layers and kv_bytes_per_token as executed per token, including every pass that has them.
"""
import json, sys


def union(m, rows):
    if not m.get("experts_gb"):
        return 0.0
    return 1 - (1 - m["top_k"] / m["n_experts"]) ** rows


def decode_step(m, drafts, ctx=0, n=1):
    rows = (drafts + 1) * n  # routed token rows in one verify step
    loops = m.get("loops", 1)
    lx, ld = m.get("looped_experts_gb", 0), m.get("looped_dense_gb", 0)
    experts = (m.get("experts_gb", 0) - lx) * union(m, rows) + lx * union(m, rows * loops)
    dense = m["dense_gb"] + (loops - 1) * ld
    kv = n * m.get("kv_bytes_per_token", 0) * ctx / 1e9 * (drafts + 1 if m.get("kv_per_verify_row") else 1)
    draft = drafts * (m.get("draft_layer_gb", 0) + m.get("draft_head_gb", m["lm_head_gb"]))  # batched over n
    total = dense + m["lm_head_gb"] + experts + kv + draft
    tp, rep = m.get("tp", 1), min(m.get("replicated_gb", 0), total)
    per_card = (total - rep) / tp + rep
    return per_card, per_card / m["bandwidth_gbs"] + m.get("comm_ms_per_step", 0) / 1e3


def decode_ceiling(m, drafts, accept, ctx=0, n=1):
    return accept * n / decode_step(m, drafts, ctx, n)[1]  # aggregate tok/s


def prefill_ceiling(m, L):
    loops = m.get("loops", 1)
    linear = 2 * (m["active_params_b"] + (loops - 1) * m.get("looped_active_params_b", 0)) * 1e9
    attn = 4 * m.get("attn_layers", 0) * m.get("attn_heads", 0) * m.get("head_dim", 0) * (L / 2)
    peak = m.get("tp", 1) * m["mfu"] * m["peak_tflops"] * 1e12
    return peak / (linear + attn + m.get("extra_flops_per_token", 0))


def main(path):
    m = json.load(open(path))
    tp = m.get("tp", 1)
    per = " per card" if tp > 1 else ""
    print(f"bandwidth {m['bandwidth_gbs']} GB/s{per}, peak {m['peak_tflops']} TFLOPS{per}, MFU {m['mfu']}")
    if tp > 1:
        print(f"tensor parallel {tp}: replicated {m.get('replicated_gb', 0)} GB/step, "
              f"communication floor {m.get('comm_ms_per_step', 0)} ms/step (decode only)")
    if m.get("loops", 1) > 1:
        print(f"looped block: {m['loops']} passes, {m.get('looped_dense_gb', 0)} GB dense + "
              f"{m.get('looped_experts_gb', 0)} GB experts per pass")
    gb, s = decode_step(m, 0, m.get("contexts", [0])[0], 1)
    print(f"c1 no-draft step at {m.get('contexts', [0])[0] // 1024}K: {gb:.3f} GB/card, {s * 1e3:.2f} ms")
    for n in m.get("concurrency", [1]):
        print(f"\nDecode ceiling, concurrency {n} (aggregate tok/s):")
        print("  drafts accept" + "".join(f"{c // 1024:>8}K" for c in m.get("contexts", [0])))
        for sp in m.get("spec", [{"drafts": 0, "accept": 1.0}]):
            row = "".join(f"{decode_ceiling(m, sp['drafts'], sp['accept'], c, n):9.0f}" for c in m.get("contexts", [0]))
            print(f"  {sp['drafts']:>6} {sp['accept']:>6}{row}")
    print("\nPrefill ceiling (tok/s, practical" + (", communication not counted" if tp > 1 else "") + "):")
    for L in m.get("contexts", [4096]):
        print(f"  {L // 1024:>4}K {prefill_ceiling(m, L):8.0f}")
    if m.get("kv_bytes_per_token"):
        kv = m["kv_bytes_per_token"] * 262144 / 1e9
        print(f"\nKV: {kv:.2f} GB per 256K-token stream" + (f" ({kv / tp:.2f} GB per card if KV is sharded)" if tp > 1 else ""))


if __name__ == "__main__":
    main(sys.argv[1]) if len(sys.argv) > 1 else sys.exit(__doc__)
