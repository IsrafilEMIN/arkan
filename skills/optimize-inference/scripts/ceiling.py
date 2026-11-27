#!/usr/bin/env python3
"""Theoretical ceilings for decode / prefill / KV from a small JSON of measured hardware and model sizes.

  python3 scripts/ceiling.py model.json [--out ceilings.json]

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
"accept" is the accepted length a from engine counters (tokens per verify step), never the configured draft length.
The FIRST spec row is the served setting: it is used for the per-depth rows and for --out.
Measure bandwidth_gbs at the real read size (rig.json microbench.bw_gbs_by_read_mib), not a datasheet peak.

Two ceilings per decode step:
  hard       = bytes / bandwidth (+ link transfers, + comm_ms_per_step). Nothing can go below it.
  practical  = hard + n dependent kernels x measured cost per chain node + work that moves no bytes
               ("at the current graph", needs the "latency" block). NOT a floor: fusion, fewer dependent steps or
               overlap can go below it. practical - hard = structural budget.
Prefill: hard = peak FLOPs (MFU 1), practical = peak x mfu.

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
  "kv_per_verify_row": true    KV is read once per verify row (no shared-prefix attention kernel).
  "extra_flops_per_token": 0   prefill FLOPs per token not covered by params and attention.
  "pipeline_split": true       layer or pipeline split over cards: at c1 one card works at a time, so the ceiling
                               uses ONE card's bandwidth_gbs for all bytes (tp is ignored for bytes). The metric
                               to watch is the time both cards are busy.
  "placement": {"resident_gb": 2.1, "nonresident_gb": 0.9, "nonresident_bw_gbs": 25}
                               GB read per decode step (c1, no draft) from VRAM and from the host or link that
                               serves the non-resident part; the two should add up to the computed step bytes
                               (a warning is printed when they differ by more than 5%). Decode steps are computed "as placed" (the non-resident
                               bytes pay nonresident_bw_gbs); "if everything fit" is printed next to it. A large gap
                               makes a format or placement that fits the first lever (a quality trade: the user decides).
  "latency": {"n_dependent_kernels": 900, "node_us": 4.5, "nonbyte_us": 300}
                               dependent kernels per decode step (one chain), measured cost per chain node (rig.json
                               microbench.chain_node_us) and per-step work that moves no bytes (top-k, syncs,
                               recurrence, sampling) in us. Gives the practical ceiling.
  "sparse_attn": {"selected_tokens": 2048, "indexer_bytes_per_ctx_token": 128}
                               sparse / indexer attention: full-attention layers read KV of the selected positions
                               only, plus indexer bytes that grow with context (summed over layers). Indexer FLOPs
                               in prefill are not counted.
  "sliding_window": {"window": 4096, "n_swa_layers": 30}
                               n_swa_layers of attn_layers attend min(pos, window) positions (KV bytes and prefill
                               attention FLOPs); only full-attention layers grow with context. Needs attn_layers.
  "links": {"exchange_bytes_per_step": 65536, "link_gbs": 12}
                               bytes exchanged between cards per decode row (scaled by rows per step) over the link
                               bandwidth measured under real concurrent traffic (P2P vs host staging).
  "peak_tflops_at_cap": 28     peak measured at the served power cap and clocks; replaces peak_tflops for prefill.
  "depths": [256, 32768, 65536, 131072]
                               context depths for the per-depth table (served spec row, concurrency 1).
  "context_target": 131072     context the depth percentages refer to (default max(depths)); d<pct> names the rows.
  "config_hash": "3f2a..."     ledger config_hash of the config these ceilings describe. Quant, card count,
                               placement or power-cap changes make the ceilings stale: recompute.

--out ceilings.json writes {"config_hash": ..., "metrics": {metric: {"hard": x, "practical": y}}} for bench.py board.
Metrics: c1_decode and c<N>_aggregate (tok/s at contexts[0], served spec row), prefill_<L> (tok/s, L in contexts),
decode_step_ms_d<pct> (ms per step, lower is better) and prefill_tps_d<pct> per depth.
"""
import json, sys


def union(m, rows):
    if not m.get("experts_gb"):
        return 0.0
    return 1 - (1 - m["top_k"] / m["n_experts"]) ** rows


def attended(L, cap=None):
    if cap is None or L <= cap:
        return L / 2
    return cap - cap * cap / (2 * L)


def kv_gb(m, ctx):
    kvt = m.get("kv_bytes_per_token", 0)
    sp, sw = m.get("sparse_attn") or {}, m.get("sliding_window") or {}
    full_ctx = min(ctx, sp["selected_tokens"]) if sp.get("selected_tokens") else ctx
    n_swa = sw.get("n_swa_layers", 0)
    if n_swa:
        layers = m.get("attn_layers") or sys.exit("sliding_window needs attn_layers")
        b = kvt / layers * ((layers - n_swa) * full_ctx + n_swa * min(ctx, sw["window"]))
    else:
        b = kvt * full_ctx
    return (b + sp.get("indexer_bytes_per_ctx_token", 0) * ctx) / 1e9


def decode_step(m, drafts, ctx=0, n=1):
    rows = (drafts + 1) * n
    loops = m.get("loops", 1)
    lx, ld = m.get("looped_experts_gb", 0), m.get("looped_dense_gb", 0)
    experts = (m.get("experts_gb", 0) - lx) * union(m, rows) + lx * union(m, rows * loops)
    dense = m["dense_gb"] + (loops - 1) * ld
    kv = n * kv_gb(m, ctx) * (drafts + 1 if m.get("kv_per_verify_row") else 1)
    draft = drafts * (m.get("draft_layer_gb", 0) + m.get("draft_head_gb", m["lm_head_gb"]))
    total = dense + m["lm_head_gb"] + experts + kv + draft
    if m.get("pipeline_split"):
        per_card = total
    else:
        tp, rep = m.get("tp", 1), min(m.get("replicated_gb", 0), total)
        per_card = (total - rep) / tp + rep
    s = per_card / m["bandwidth_gbs"] + m.get("comm_ms_per_step", 0) / 1e3
    pl = m.get("placement")
    if pl:
        s += pl["nonresident_gb"] * (1 / pl["nonresident_bw_gbs"] - 1 / m["bandwidth_gbs"])
    li = m.get("links")
    if li:
        s += li["exchange_bytes_per_step"] * rows / 1e9 / li["link_gbs"]
    lat = m.get("latency") or {}
    practical = s + (lat.get("n_dependent_kernels", 0) * lat.get("node_us", 0) + lat.get("nonbyte_us", 0)) / 1e6
    return per_card, s, practical


def decode_ceiling(m, drafts, accept, ctx=0, n=1, practical=False):
    return accept * n / decode_step(m, drafts, ctx, n)[2 if practical else 1]


def prefill_ceiling(m, L, mfu=None):
    loops = m.get("loops", 1)
    linear = 2 * (m["active_params_b"] + (loops - 1) * m.get("looped_active_params_b", 0)) * 1e9
    layers = m.get("attn_layers", 0)
    sp, sw = m.get("sparse_attn") or {}, m.get("sliding_window") or {}
    n_swa = sw.get("n_swa_layers", 0)
    pos = (layers - n_swa) * attended(L, sp.get("selected_tokens")) + (n_swa * attended(L, sw["window"]) if n_swa else 0)
    attn = 4 * m.get("attn_heads", 0) * m.get("head_dim", 0) * pos
    peak = m.get("tp", 1) * (m["mfu"] if mfu is None else mfu) * m.get("peak_tflops_at_cap", m["peak_tflops"]) * 1e12
    return peak / (linear + attn + m.get("extra_flops_per_token", 0))


def depth_pct(m, d):
    return round(100 * d / (m.get("context_target") or max(m["depths"])))


def ceilings(m):
    sp = m.get("spec", [{"drafts": 0, "accept": 1.0}])[0]
    c0 = m.get("contexts", [0])[0]
    out = {}
    for n in m.get("concurrency", [1]):
        key = "c1_decode" if n == 1 else f"c{n}_aggregate"
        out[key] = {"hard": round(decode_ceiling(m, sp["drafts"], sp["accept"], c0, n), 1),
                    "practical": round(decode_ceiling(m, sp["drafts"], sp["accept"], c0, n, True), 1)}
    for L in m.get("contexts", []):
        out[f"prefill_{L}"] = {"hard": round(prefill_ceiling(m, L, 1.0), 1), "practical": round(prefill_ceiling(m, L), 1)}
    for d in m.get("depths", []):
        _, h, p = decode_step(m, sp["drafts"], d, 1)
        pct = depth_pct(m, d)
        out[f"decode_step_ms_d{pct}"] = {"hard": round(h * 1e3, 3), "practical": round(p * 1e3, 3)}
        out[f"prefill_tps_d{pct}"] = {"hard": round(prefill_ceiling(m, max(d, 1), 1.0), 1),
                                      "practical": round(prefill_ceiling(m, max(d, 1)), 1)}
    return out


def main(path, out=None):
    m = json.load(open(path))
    tp = m.get("tp", 1)
    per = " per card" if tp > 1 or m.get("pipeline_split") else ""
    print(f"bandwidth {m['bandwidth_gbs']} GB/s{per}, peak {m['peak_tflops']} TFLOPS{per}, MFU {m['mfu']}")
    if m.get("peak_tflops_at_cap"):
        print(f"peak at the served power cap: {m['peak_tflops_at_cap']} TFLOPS{per} (used for prefill)")
    if tp > 1 and not m.get("pipeline_split"):
        print(f"tensor parallel {tp}: replicated {m.get('replicated_gb', 0)} GB/step, "
              f"communication floor {m.get('comm_ms_per_step', 0)} ms/step (decode only)")
    if m.get("pipeline_split"):
        print("pipeline/layer split: c1 uses one card at a time, so all bytes pay ONE card's bandwidth; "
              "watch the time both cards are busy")
    if m.get("loops", 1) > 1:
        print(f"looped block: {m['loops']} passes, {m.get('looped_dense_gb', 0)} GB dense + "
              f"{m.get('looped_experts_gb', 0)} GB experts per pass")
    if m.get("links"):
        li = m["links"]
        print(f"links: {li['exchange_bytes_per_step']} B per row over {li['link_gbs']} GB/s (added to every step)")
    if m.get("sparse_attn"):
        sp = m["sparse_attn"]
        print(f"sparse attention: KV of {sp.get('selected_tokens')} selected positions + "
              f"{sp.get('indexer_bytes_per_ctx_token', 0)} indexer B per context token")
    if m.get("sliding_window"):
        sw = m["sliding_window"]
        print(f"sliding window: {sw['n_swa_layers']} of {m.get('attn_layers')} attention layers see min(pos, {sw['window']})")
    c0 = m.get("contexts", [0])[0]
    gb, s, p = decode_step(m, 0, c0, 1)
    print(f"c1 no-draft step at {c0 // 1024}K: {gb:.3f} GB/card, {s * 1e3:.2f} ms")
    lat = m.get("latency")
    if lat:
        print(f"  practical at the current graph: {p * 1e3:.2f} ms ({lat.get('n_dependent_kernels', 0)} dependent kernels x "
              f"{lat.get('node_us', 0)} us + {lat.get('nonbyte_us', 0)} us without bytes); "
              f"structural budget {(p - s) * 1e3:.2f} ms/step")
    pl = m.get("placement")
    if pl:
        nb, placed = pl["nonresident_bw_gbs"], s
        fit = decode_step(dict(m, placement=None), 0, c0, 1)[1]
        given = pl["resident_gb"] + pl["nonresident_gb"]
        print(f"placement: {pl['nonresident_gb']} of {gb:.3f} GB/step served at {nb} GB/s -> as placed "
              f"{placed * 1e3:.2f} ms ({1 / placed:.0f} tok/s), if everything fit {fit * 1e3:.2f} ms "
              f"({1 / fit:.0f} tok/s), x{placed / fit:.2f}. Decode tables below are as placed.")
        if abs(given - gb) > 0.05 * gb:
            print(f"warning: placement resident_gb + nonresident_gb = {given:.3f} GB differs from the computed step bytes "
                  f"{gb:.3f} GB/card by more than 5%; check the placement numbers")
    for n in m.get("concurrency", [1]):
        for practical in ([False, True] if lat else [False]):
            label = "practical at the current graph" if practical else "aggregate tok/s"
            print(f"\nDecode ceiling, concurrency {n} ({label}):")
            print("  drafts accept" + "".join(f"{c // 1024:>8}K" for c in m.get("contexts", [0])))
            for sp in m.get("spec", [{"drafts": 0, "accept": 1.0}]):
                row = "".join(f"{decode_ceiling(m, sp['drafts'], sp['accept'], c, n, practical):9.0f}"
                              for c in m.get("contexts", [0]))
                print(f"  {sp['drafts']:>6} {sp['accept']:>6}{row}")
    print("\nPrefill ceiling (tok/s, practical" + (", communication not counted" if tp > 1 else "") + "; hard = MFU 1):")
    for L in m.get("contexts", [4096]):
        print(f"  {L // 1024:>4}K {prefill_ceiling(m, L):8.0f}  hard {prefill_ceiling(m, L, 1.0):8.0f}")
    if m.get("depths"):
        sp = m.get("spec", [{"drafts": 0, "accept": 1.0}])[0]
        print(f"\nPer depth (c1, drafts {sp['drafts']}, accept {sp['accept']}; context target "
              f"{m.get('context_target') or max(m['depths'])}):")
        print("  bucket    depth   KV GB  hard ms  prac ms  hard tok/s  prac tok/s  prefill tok/s")
        for d in m["depths"]:
            _, h, p = decode_step(m, sp["drafts"], d, 1)
            print(f"  d{depth_pct(m, d):<5} {d:>8} {kv_gb(m, d):7.3f} {h * 1e3:8.2f} {p * 1e3:8.2f} "
                  f"{sp['accept'] / h:11.0f} {sp['accept'] / p:11.0f} {prefill_ceiling(m, max(d, 1)):14.0f}")
    if m.get("kv_bytes_per_token"):
        kv = kv_gb(m, 262144)
        print(f"\nKV: {kv:.2f} GB per 256K-token stream" + (f" ({kv / tp:.2f} GB per card if KV is sharded)" if tp > 1 else ""))
    if out:
        if not m.get("config_hash"):
            print("\nwarning: no config_hash in the model JSON; bench.py board cannot tell when these ceilings are stale")
        with open(out, "w") as f:
            json.dump({"config_hash": m.get("config_hash"), "metrics": ceilings(m)}, f, indent=1)
        print(f"\nwrote {out}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 1 and not a[0].startswith("-"):
        main(a[0])
    elif len(a) == 3 and a[1] == "--out":
        main(a[0], a[2])
    else:
        sys.exit(__doc__)
