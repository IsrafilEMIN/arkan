#!/usr/bin/env python3
import hashlib, json, math, os, sys

try:
    import numpy as np
except ImportError:
    np = None

USAGE = "\n".join([
    'Quality evidence for inference changes: l0 bit identity, full-vocab KL/TV vs a measured floor, dNLL equivalence.',
    '',
    '  python3 scripts/quality.py l0 A_DIR B_DIR',
    '  python3 scripts/quality.py dist REF_DIR CAND_DIR [--floor FA_DIR FB_DIR] [--margin-ratio 2] [SAMPLING] [--buckets 0,8192,32768]',
    '  python3 scripts/quality.py oracle ORACLE_DIR CTL_DIR CAND_DIR --delta D [SAMPLING] [--buckets ...]',
    '  python3 scripts/quality.py dnll CTL.jsonl CAND.jsonl --margin NATS',
    '  python3 scripts/quality.py experts REF.jsonl CAND.jsonl [--floor FA.jsonl FB.jsonl] [--margin-ratio 2]',
    '  python3 scripts/quality.py size FA_DIR FB_DIR --delta D [--z 1.645] [SAMPLING]',
    '  python3 scripts/quality.py mcnemar A.jsonl B.jsonl',
    'SAMPLING: --temperature T (default 1, > 0) --top-k K (0 = off) --top-p P (1 = off) --temp-last',
    'Common: --boot B (2000) --seed S (0) --min-prompts N (5; fewer prompts in a bucket = LOW_N = FAIL)',
    '        --vocab N (declared full vocab; dist, oracle and size need it or a per-row "full_vocab")',
    'Exit: 0 PASS or REPORT (numbers only, no gate), 1 FAIL, 2 usage or data error. numpy needed except l0, mcnemar.',
    '',
    'l0       PASS when every key is on both sides with equal values; prints the first differing row. Input per side,',
    '         first found: fingerprints.jsonl {"prompt_id","pos","phase","sha"}; bench requests.jsonl (key pass, kind,',
    "         prompt_id, path; value output_sha12); a dump index.jsonl (sha256 of each row's raw bytes).",
    'dist     Per step, over the FULL vocab after the served sampling transform: KL(ref||cand) and TV, median/p99/max',
    '         per depth bucket, KL inf share, argmax flip rate, near-tie share (ref top-2 logit gap < floor p99 logit',
    '         noise), flips_out (flips that are not near ties). --floor = two valid control runs differing only in',
    '         reduction order, routing replayed. Gate (paired non-inferiority, block bootstrap by prompt_id):',
    '         one-sided 95% upper bound of median(cand) - margin_ratio * median(floor) <= 0 in every bucket and "all".',
    '         Gate stat KL; with top-k/top-p it is TV (KL is undefined/inf where cand drops a token ref keeps).',
    'oracle   d = div(oracle||cand) - div(oracle||ctl) per row (div KL, TV with truncation); PASS when the 95% upper',
    '         bound of mean d < delta. Buckets informational.',
    'dnll     dNLL = logprob_ctl - logprob_cand of the true next token on held-out REAL text (> 0: cand worse).',
    '         TOST: PASS when the 90% bootstrap CI of mean dNLL lies inside (-margin, +margin); also ppl ratio.',
    'experts  Per layer mean Jaccard and exact-set share. --floor gates disagreement (1 - Jaccard) like dist, mean stat.',
    'size     n = ceil((z * sigma / (delta / 2))^2) sequences; sigma = SD over prompts of per-prompt mean floor KL (TV).',
    '         Prints raw n and n clamped to >= --min-prompts (use the clamped n).',
    'mcnemar  Exact binomial on discordant pairs + 95% CI of pass-rate difference B - A. FAIL when p < 0.05 and B',
    '         worse; else REPORT: no detected loss, not equivalence (read the CI).',
    'Order: temperature, top-k, top-p (vLLM/HF); --temp-last: top-k, top-p, temperature (llama.cpp chain).',
    '',
    'Formats (match by keys; see references/quality.md):',
    '  dump dir: index.jsonl {"prompt_id","pos","depth","file","offset","vocab","dtype":"f16|f32"} + raw little-endian',
    '    binaries (vocab values at file+offset); "full_vocab" (or --vocab) is required for dist, oracle, size. Rows',
    '    without a declared full vocab, with "topk"/"other", or with vocab < full vocab are refused: truncated logits',
    '    underestimate KL/TV (data-processing inequality).',
    '  dnll: {"prompt_id","pos","token_id","logprob"}   experts: {"prompt_id","pos","layer","ids":[...]}',
    '  tasks: {"id","pass":bool}',
    'Buckets: depth edges, e.g. 0,8192,32768 -> [0,8192) [8192,32768) [32768,inf); default only "all".',
])

DTYPES = {"f16": ("<f2", 2), "f32": ("<f4", 4)}
DPI_MSG = ("truncated logits (top-k dumps or 'other' bins) underestimate KL and TV: merging tokens can only "
           "lower a divergence (data-processing inequality), so a truncated dump cannot show that a change is "
           "rounding-level. Dump full-vocab logits, or compute full-vocab KL/TV per row inside the engine.")
NUMPY_MSG = "quality.py needs numpy for this subcommand: python3 -m pip install --user numpy"


class DataError(Exception):
    pass


def read_jsonl(path):
    try:
        f = open(path)
    except OSError as e:
        raise DataError(f"cannot read {path}: {e}")
    with f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except ValueError as e:
                raise DataError(f"{path}:{n}: bad JSON ({e})")


def need(row, keys, path):
    for k in keys:
        if k not in row:
            raise DataError(f"{path}: row lacks {k!r}: {json.dumps(row)[:200]}")


def check_full_vocab(row, full_vocab, path, required=False):
    if "topk" in row or "other" in row:
        raise DataError(f"{path}: row has 'topk'/'other' fields. {DPI_MSG}")
    fv = row.get("full_vocab") or full_vocab
    if required and not fv:
        raise DataError(f"{path}: no declared full vocabulary (row 'full_vocab' or --vocab N). {DPI_MSG}")
    if fv and int(row["vocab"]) < int(fv):
        raise DataError(f"{path}: vocab {row['vocab']} < full vocab {fv}. {DPI_MSG}")


def load_index(d, full_vocab=None, required=False):
    path = os.path.join(d, "index.jsonl")
    if not os.path.isfile(path):
        raise DataError(f"{d}: no index.jsonl (full-logit dump dir expected)")
    rows = {}
    for r in read_jsonl(path):
        need(r, ("prompt_id", "pos", "file", "offset", "vocab", "dtype"), path)
        if r["dtype"] not in DTYPES:
            raise DataError(f"{path}: dtype {r['dtype']!r} not in {sorted(DTYPES)}")
        check_full_vocab(r, full_vocab, path, required)
        k = (str(r["prompt_id"]), int(r["pos"]))
        if k in rows:
            raise DataError(f"{path}: duplicate row {k}")
        rows[k] = r
    if not rows:
        raise DataError(f"{path}: empty")
    return rows


class LogitReader:
    def __init__(self, d, max_open=32):
        self.d, self.max_open, self.fh = d, max_open, {}

    def raw(self, r):
        path = os.path.join(self.d, r["file"])
        f = self.fh.get(path)
        if f is None:
            if len(self.fh) >= self.max_open:
                self.close()
            try:
                f = self.fh[path] = open(path, "rb")
            except OSError as e:
                raise DataError(f"cannot read {path}: {e}")
        size = int(r["vocab"]) * DTYPES[r["dtype"]][1]
        f.seek(int(r["offset"]))
        buf = f.read(size)
        if len(buf) != size:
            raise DataError(f"{path}: short read at offset {r['offset']} ({len(buf)} of {size} bytes)")
        return buf

    def get(self, r):
        x = np.frombuffer(self.raw(r), dtype=DTYPES[r["dtype"]][0]).astype(np.float64)
        if np.isnan(x).any() or not np.isfinite(x.max()):
            raise DataError(f"{self.d}: NaN or +inf logits at {r['prompt_id']}/{r['pos']}")
        return x

    def close(self):
        for f in self.fh.values():
            f.close()
        self.fh = {}


class Sampling:
    def __init__(self, temperature=1.0, top_k=0, top_p=1.0, temp_last=False):
        if not temperature > 0:
            raise DataError("--temperature must be > 0 (greedy: use the flip rate and --temperature 1)")
        if not 0 < top_p <= 1 or top_k < 0:
            raise DataError("--top-p must be in (0, 1], --top-k >= 0")
        self.temperature, self.top_k, self.top_p, self.temp_last = temperature, top_k, top_p, temp_last
        self.truncates = top_k > 0 or top_p < 1

    def label(self):
        order = "top-k,top-p,temp" if self.temp_last else "temp,top-k,top-p"
        return f"T={self.temperature} top_k={self.top_k or 'off'} top_p={self.top_p} order={order}"


def log_softmax(x):
    y = x - x.max()
    return y - math.log(np.exp(y).sum())


def truncate(lp, top_k, top_p):
    keep = np.isfinite(lp)
    if top_k and top_k < lp.size:
        m = np.zeros(lp.size, bool)
        m[np.argpartition(lp, lp.size - top_k)[lp.size - top_k:]] = True
        keep &= m
    if top_p < 1:
        idx = np.flatnonzero(keep)
        order = idx[np.argsort(-lp[idx], kind="stable")]
        p = np.exp(lp[order])
        n = int(np.searchsorted(np.cumsum(p / p.sum()), top_p)) + 1
        m = np.zeros(lp.size, bool)
        m[order[:min(n, order.size)]] = True
        keep &= m
    out = np.full(lp.size, -np.inf)
    out[keep] = lp[keep]
    return log_softmax(out)


def served_logprobs(logits, s):
    if s.temp_last:
        lp = log_softmax(logits)
        if s.truncates:
            lp = truncate(lp, s.top_k, s.top_p)
        return log_softmax(lp / s.temperature) if s.temperature != 1 else lp
    lp = log_softmax(logits / s.temperature)
    return truncate(lp, s.top_k, s.top_p) if s.truncates else lp


def kl(lp, lq):
    m = np.isfinite(lp)
    if not np.isfinite(lq[m]).all():
        return math.inf
    return max(0.0, float(np.dot(np.exp(lp[m]), lp[m] - lq[m])))


def tv(lp, lq):
    return 0.5 * float(np.abs(np.exp(lp) - np.exp(lq)).sum())


def top2(x):
    i = np.argpartition(x, x.size - 2)[x.size - 2:]
    i = i[np.argsort(-x[i])]
    return int(i[0]), int(i[1]), float(x[i[0]] - x[i[1]])


def row_metrics(a, b, s):
    if a.size != b.size:
        raise DataError(f"vocab differs between sides ({a.size} vs {b.size}). {DPI_MSG}")
    if a.size < 2:
        raise DataError("vocab < 2")
    lp, lq = served_logprobs(a, s), served_logprobs(b, s)
    i0, i1, gap = top2(a)
    la, lb = log_softmax(a), log_softmax(b)
    return {"kl": kl(lp, lq), "tv": tv(lp, lq), "flip": float(np.argmax(a) != np.argmax(b)), "gap": gap,
            "noise": float(max(abs(la[i0] - lb[i0]), abs(la[i1] - lb[i1])))}


def qrank(a, q):
    a = np.asarray(a, dtype=np.float64)
    if a.size == 0:
        return math.nan
    k = min(a.size - 1, max(0, math.ceil(q * a.size) - 1))
    return float(np.partition(a, k)[k])


def median(a):
    return qrank(a, 0.5)


def mean(a):
    return float(np.mean(a))


def noninferiority(cg, fg, ratio, boot, rng, stat=median):
    ck, fk = sorted(cg), sorted(fg)
    paired = ck == fk
    out = np.empty(boot)
    for b in range(boot):
        ic = rng.integers(0, len(ck), len(ck))
        jf = ic if paired else rng.integers(0, len(fk), len(fk))
        c = np.concatenate([cg[ck[i]] for i in ic])
        f = np.concatenate([fg[fk[j]] for j in jf])
        out[b] = stat(c) - ratio * stat(f)
    return qrank(out, 0.95), paired


def boot_mean(sums, counts, boot, rng, chunk=256):
    sums, counts = np.asarray(sums, np.float64), np.asarray(counts, np.float64)
    n, out = sums.size, []
    for start in range(0, boot, chunk):
        idx = rng.integers(0, n, (min(chunk, boot - start), n))
        out.append(sums[idx].sum(1) / counts[idx].sum(1))
    return np.concatenate(out)


def group(values, pids):
    g = {}
    for v, p in zip(values, pids):
        g.setdefault(p, []).append(v)
    return {p: np.asarray(v, np.float64) for p, v in g.items()}


def sums_counts(values, pids):
    g = group(values, pids)
    return [float(v.sum()) for v in g.values()], [v.size for v in g.values()]


def binom_two_sided(k, n):
    if n == 0:
        return 1.0
    k = min(k, n - k)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def compare_dirs(ref_dir, cand_dir, s, full_vocab=None):
    ri, ci = load_index(ref_dir, full_vocab, True), load_index(cand_dir, full_vocab, True)
    keys = [k for k in ri if k in ci]
    if not keys:
        raise DataError(f"no (prompt_id, pos) rows in common between {ref_dir} and {cand_dir}")
    cols = {c: [] for c in ("kl", "tv", "flip", "gap", "noise")}
    rr, cr = LogitReader(ref_dir), LogitReader(cand_dir)
    try:
        for k in keys:
            m = row_metrics(rr.get(ri[k]), cr.get(ci[k]), s)
            for c in cols:
                cols[c].append(m[c])
    finally:
        rr.close()
        cr.close()
    out = {c: np.asarray(v, np.float64) for c, v in cols.items()}
    out["pid"] = [k[0] for k in keys]
    out["pos"] = [k[1] for k in keys]
    out["depth"] = np.asarray([int(ri[k].get("depth", k[1])) for k in keys])
    out["unmatched"] = (len(ri) - len(keys), len(ci) - len(keys))
    return out


def parse_buckets(text):
    edges = sorted({int(x) for x in text.split(",") if x.strip()})
    return [0] + [e for e in edges if e > 0]


def bucket_indices(depth, edges):
    out = [("all", np.arange(depth.size))]
    if edges:
        b = np.searchsorted(edges, depth, side="right") - 1
        for i, lo in enumerate(edges):
            hi = edges[i + 1] if i + 1 < len(edges) else "inf"
            out.append((f"[{lo},{hi})", np.flatnonzero(b == i)))
    return out


def take(rows, col, idx):
    return rows[col][idx], [rows["pid"][i] for i in idx]


def summary(rows, idx, tie):
    kl_, tv_ = rows["kl"][idx], rows["tv"][idx]
    flips = rows["flip"][idx]
    s = {"rows": idx.size, "prompts": len({rows["pid"][i] for i in idx})}
    if idx.size == 0:
        return s
    s.update(kl_med=median(kl_), kl_p99=qrank(kl_, 0.99), kl_max=float(kl_.max()),
             kl_inf=float(np.isinf(kl_).mean()), tv_med=median(tv_), tv_p99=qrank(tv_, 0.99),
             tv_max=float(tv_.max()), flip=float(flips.mean()))
    if tie is not None:
        near = rows["gap"][idx] < tie
        s["near_tie"] = float(near.mean())
        s["flips_out"] = int((flips.astype(bool) & ~near).sum())
    return s


def fmt(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "na"
    if isinstance(x, float):
        return "inf" if math.isinf(x) else f"{x:.4g}"
    return str(x)


def table(headers, rows):
    cells = [headers] + [[fmt(c) for c in r] for r in rows]
    w = [max(len(r[i]) for r in cells) for i in range(len(headers))]
    for r in cells:
        print("  ".join(c.rjust(w[i]) for i, c in enumerate(r)))


def verdict(ok, cmd, detail):
    word = {True: "PASS", False: "FAIL", None: "REPORT"}[ok]
    print(f"{word} {cmd}: {detail}")
    return 0 if ok in (True, None) else 1


def load_fingerprints(path):
    if os.path.isdir(path):
        for name in ("fingerprints.jsonl", "requests.jsonl", "index.jsonl"):
            if os.path.isfile(os.path.join(path, name)):
                return fingerprints_from(os.path.join(path, name), path)
        raise DataError(f"{path}: no fingerprints.jsonl, requests.jsonl or index.jsonl")
    return fingerprints_from(path, os.path.dirname(path) or ".")


def fingerprints_from(file, d):
    out = {}
    if os.path.basename(file) == "index.jsonl":
        reader = LogitReader(d)
        try:
            for k, r in load_index(d).items():
                out[k] = r["dtype"] + ":" + hashlib.sha256(reader.raw(r)).hexdigest()
        finally:
            reader.close()
        return "logit-hash", out
    kind = None
    for r in read_jsonl(file):
        if "sha" in r:
            need(r, ("prompt_id", "pos", "phase"), file)
            kind, k, v = "fingerprints", (str(r["prompt_id"]), int(r["pos"]), str(r["phase"])), r["sha"]
        elif r.get("output_sha12"):
            kind = "output_sha12"
            k = (r.get("pass"), r.get("kind"), str(r.get("prompt_id")), json.dumps(r.get("path"), sort_keys=True))
            v = r["output_sha12"]
        else:
            continue
        if k in out:
            raise DataError(f"{file}: duplicate key {k}")
        out[k] = v
    if not out:
        raise DataError(f"{file}: no fingerprint rows")
    return kind, out


def cmd_l0(pos, o):
    a_kind, a = load_fingerprints(pos[0])
    b_kind, b = load_fingerprints(pos[1])
    if a_kind != b_kind:
        raise DataError(f"different fingerprint kinds: {a_kind} vs {b_kind}")
    common = [k for k in a if k in b]
    if not common:
        raise DataError("no keys in common")
    diff = [k for k in common if a[k] != b[k]]
    only_a, only_b = len(a) - len(common), len(b) - len(common)
    ok = not diff and not only_a and not only_b
    detail = f"{a_kind}: {len(common)} common, {len(diff)} differ, {only_a} only in A, {only_b} only in B"
    rc = verdict(ok, "l0", detail)
    if diff:
        print(f"first differing row: {diff[0]}  A={a[diff[0]]}  B={b[diff[0]]}")
    if only_a or only_b:
        print("rows missing on one side: the compared paths are not covered on both sides")
    return rc


def cmd_dist(pos, o):
    s, edges = o["sampling"], o["buckets"]
    stat = "tv" if s.truncates else "kl"
    floor = compare_dirs(o["floor"][0], o["floor"][1], s, o["vocab"]) if o["floor"] else None
    tie = qrank(floor["noise"], 0.99) if floor else None
    rows = compare_dirs(pos[0], pos[1], s, o["vocab"])
    rng = np.random.default_rng(o["seed"])
    print(f"sampling {s.label()}; gate stat {stat}; matched {len(rows['pid'])} rows; "
          f"unmatched ref/cand {rows['unmatched']}")
    if s.truncates:
        print("top-k/top-p truncation: KL is undefined (inf) where the candidate drops a token the reference "
              "keeps; the gate uses TV")
    if tie is not None:
        print(f"near-tie threshold (floor p99 logit noise) {fmt(tie)}")
    fb = dict(bucket_indices(floor["depth"], edges)) if floor else {}
    out, fails = [], []
    for name, idx in bucket_indices(rows["depth"], edges):
        sm = summary(rows, idx, tie)
        fmed = bound = upper = None
        state = "-"
        if floor:
            fidx = fb[name]
            fprompts = len({floor["pid"][i] for i in fidx})
            if min(sm["prompts"], fprompts) < o["min_prompts"]:
                state = "LOW_N"
            else:
                fmed = median(floor[stat][fidx])
                bound = o["margin_ratio"] * fmed
                upper, paired = noninferiority(group(*take(rows, stat, idx)), group(*take(floor, stat, fidx)),
                                               o["margin_ratio"], o["boot"], rng)
                state = ("PASS" if upper <= 0 else "FAIL") + ("" if paired else " (unpaired)")
            if not state.startswith("PASS"):
                fails.append(f"{name} {state.split()[0]}")
        out.append([name, sm["rows"], sm["prompts"], sm.get("kl_med"), sm.get("kl_p99"), sm.get("kl_max"),
                    sm.get("kl_inf"), sm.get("tv_med"), sm.get("tv_p99"), sm.get("tv_max"), sm.get("flip"),
                    sm.get("near_tie"), sm.get("flips_out"), fmed, bound, upper, state])
    if not floor:
        rc = verdict(None, "dist", "no --floor: numbers only; not l1 evidence")
    else:
        rc = verdict(not fails, "dist", f"95% upper bound of median({stat}) - {o['margin_ratio']} x floor <= 0 "
                     + ("in every bucket" if not fails else "failed: " + ", ".join(fails)))
    table(["bucket", "rows", "prompts", "kl_med", "kl_p99", "kl_max", "kl_inf", "tv_med", "tv_p99", "tv_max",
           "flip", "near_tie", "flips_out", f"floor_{stat}", "bound", "ub(c-r*f)", "gate"], out)
    return rc


def cmd_oracle(pos, o):
    if o["delta"] is None:
        raise DataError("oracle needs --delta")
    s = o["sampling"]
    stat = "tv" if s.truncates else "kl"
    oc = compare_dirs(pos[0], pos[2], s, o["vocab"])
    ok_ = compare_dirs(pos[0], pos[1], s, o["vocab"])
    at = {(p, q): i for i, (p, q) in enumerate(zip(ok_["pid"], ok_["pos"]))}
    keep = [(i, at[(p, q)]) for i, (p, q) in enumerate(zip(oc["pid"], oc["pos"])) if (p, q) in at]
    if not keep:
        raise DataError("no rows common to oracle, control and candidate")
    ic = np.asarray([i for i, _ in keep])
    d = oc[stat][ic] - ok_[stat][np.asarray([j for _, j in keep])]
    pids = [oc["pid"][i] for i in ic]
    depth = oc["depth"][ic]
    rng = np.random.default_rng(o["seed"])
    print(f"sampling {s.label()}; d = {stat}(oracle||cand) - {stat}(oracle||ctl); {len(keep)} rows")
    out, upper_all = [], None
    for name, idx in bucket_indices(depth, o["buckets"]):
        if idx.size == 0:
            out.append([name, 0, 0, None, None, None, None])
            continue
        sub = [pids[i] for i in idx]
        ub = qrank(boot_mean(*sums_counts(d[idx], sub), o["boot"], rng), 0.95)
        if name == "all":
            upper_all = ub
        out.append([name, idx.size, len(set(sub)), mean(d[idx]), median(d[idx]), qrank(d[idx], 0.99), ub])
    nprompts = len(set(pids))
    if nprompts < o["min_prompts"]:
        rc = verdict(False, "oracle", f"LOW_N: {nprompts} prompts < {o['min_prompts']}")
    else:
        rc = verdict(upper_all < o["delta"], "oracle",
                     f"95% upper bound of mean d {fmt(upper_all)} vs delta {fmt(o['delta'])} (needs <)")
    table(["bucket", "rows", "prompts", "mean_d", "median_d", "p99_d", "ub_mean"], out)
    return rc


def finite_lp(r, path):
    lp = float(r["logprob"])
    if not math.isfinite(lp) or lp > 1e-6:
        raise DataError(f"{path}: logprob must be finite and <= 0, got {r['logprob']} at "
                        f"{r['prompt_id']}/{r['pos']}")
    return lp


def cmd_dnll(pos, o):
    if o["margin"] is None:
        raise DataError("dnll needs --margin NATS")
    ctl = {}
    for r in read_jsonl(pos[0]):
        need(r, ("prompt_id", "pos", "token_id", "logprob"), pos[0])
        ctl[(str(r["prompt_id"]), int(r["pos"]))] = (int(r["token_id"]), finite_lp(r, pos[0]))
    d, nll_c, nll_k, pids, cand_only = [], 0.0, 0.0, [], 0
    for r in read_jsonl(pos[1]):
        need(r, ("prompt_id", "pos", "token_id", "logprob"), pos[1])
        k = (str(r["prompt_id"]), int(r["pos"]))
        if k not in ctl:
            cand_only += 1
            continue
        tid, lk = ctl.pop(k)
        if tid != int(r["token_id"]):
            raise DataError(f"token_id differs at {k}: both logs must score the same real text")
        lc = finite_lp(r, pos[1])
        d.append(lk - lc)
        nll_k -= lk
        nll_c -= lc
        pids.append(k[0])
    if not d:
        raise DataError("no (prompt_id, pos) rows in common")
    n = len(d)
    boots = boot_mean(*sums_counts(d, pids), o["boot"], np.random.default_rng(o["seed"]))
    m, lo, hi = sum(d) / n, qrank(boots, 0.05), qrank(boots, 0.95)
    nprompts = len(set(pids))
    if nprompts < o["min_prompts"]:
        rc = verdict(False, "dnll", f"LOW_N: {nprompts} prompts < {o['min_prompts']}")
    else:
        inside = -o["margin"] < lo and hi < o["margin"]
        rc = verdict(inside, "dnll", f"TOST: 90% CI [{fmt(lo)}, {fmt(hi)}] nats/token "
                     f"{'inside' if inside else 'not inside'} +-{fmt(o['margin'])}")
    print(f"unmatched ctl/cand rows {len(ctl)}/{cand_only}")
    table(["tokens", "prompts", "nll_ctl", "nll_cand", "dnll", "ci90_lo", "ci90_hi", "ppl_ratio", "ppl_lo",
           "ppl_hi"], [[n, nprompts, nll_k / n, nll_c / n, m, lo, hi, math.exp(m), math.exp(lo), math.exp(hi)]])
    return rc


def expert_agreement(ref_path, cand_path):
    ref = {}
    for r in read_jsonl(ref_path):
        need(r, ("prompt_id", "pos", "layer", "ids"), ref_path)
        ref[(str(r["prompt_id"]), int(r["pos"]), int(r["layer"]))] = frozenset(r["ids"])
    out = []
    for r in read_jsonl(cand_path):
        need(r, ("prompt_id", "pos", "layer", "ids"), cand_path)
        k = (str(r["prompt_id"]), int(r["pos"]), int(r["layer"]))
        if k not in ref:
            continue
        a, b = ref[k], frozenset(r["ids"])
        union = a | b
        out.append((k[2], k[0], len(a & b) / len(union) if union else 1.0, float(a == b)))
    if not out:
        raise DataError(f"no (prompt_id, pos, layer) rows in common between {ref_path} and {cand_path}")
    return out


def cmd_experts(pos, o):
    rows = expert_agreement(pos[0], pos[1])
    out = []
    for layer in sorted({r[0] for r in rows}):
        sub = [r for r in rows if r[0] == layer]
        out.append([layer, len(sub), len({r[1] for r in sub}), sum(r[2] for r in sub) / len(sub),
                    sum(r[3] for r in sub) / len(sub)])
    out.append(["all", len(rows), len({r[1] for r in rows}), sum(r[2] for r in rows) / len(rows),
                sum(r[3] for r in rows) / len(rows)])
    if not o["floor"]:
        rc = verdict(None, "experts", "no --floor: agreement only")
    else:
        frows = expert_agreement(o["floor"][0], o["floor"][1])
        cg = group([1 - r[2] for r in rows], [r[1] for r in rows])
        fg = group([1 - r[2] for r in frows], [r[1] for r in frows])
        if min(len(cg), len(fg)) < o["min_prompts"]:
            rc = verdict(False, "experts", f"LOW_N: fewer than {o['min_prompts']} prompts")
        else:
            upper, paired = noninferiority(cg, fg, o["margin_ratio"], o["boot"],
                                           np.random.default_rng(o["seed"]), stat=mean)
            fdis = 1 - sum(r[2] for r in frows) / len(frows)
            rc = verdict(upper <= 0, "experts",
                         f"95% upper bound of disagreement - {o['margin_ratio']} x floor ({fmt(fdis)}) = "
                         f"{fmt(upper)} (needs <= 0){'' if paired else ', unpaired'}")
    table(["layer", "rows", "prompts", "jaccard", "exact_share"], out)
    return rc


def cmd_size(pos, o):
    if o["delta"] is None:
        raise DataError("size needs --delta")
    s = o["sampling"]
    stat = "tv" if s.truncates else "kl"
    rows = compare_dirs(pos[0], pos[1], s, o["vocab"])
    per = [float(v.mean()) for v in group(rows[stat], rows["pid"]).values()]
    if len(per) < 2:
        raise DataError("size needs at least 2 pilot prompts")
    sigma = float(np.std(per, ddof=1))
    raw_n = math.ceil((o["z"] * sigma / (o["delta"] / 2)) ** 2)
    n = max(raw_n, o["min_prompts"])
    rc = verdict(None, "size", f"n = {n} sequences for delta {fmt(o['delta'])} at z {o['z']} "
                 f"(raw {raw_n}, clamped to >= --min-prompts {o['min_prompts']})")
    table(["pilot_prompts", "rows", f"mean_{stat}", "sigma_per_prompt", "delta", "z", "n_raw", "n"],
          [[len(per), len(rows["pid"]), float(np.mean(per)), sigma, o["delta"], o["z"], raw_n, n]])
    return rc


def load_tasks(path):
    out = {}
    for r in read_jsonl(path):
        need(r, ("id", "pass"), path)
        k = str(r["id"])
        if k in out:
            raise DataError(f"{path}: duplicate id {k}")
        out[k] = bool(r["pass"])
    return out


def mcnemar(a, b):
    ids = [k for k in a if k in b]
    if not ids:
        raise DataError("no ids in common")
    n = len(ids)
    lost = sum(1 for k in ids if a[k] and not b[k])
    won = sum(1 for k in ids if b[k] and not a[k])
    diff = (won - lost) / n
    se = math.sqrt(max(0.0, (won + lost) - (won - lost) ** 2 / n)) / n
    return {"n": n, "a_rate": sum(a[k] for k in ids) / n, "b_rate": sum(b[k] for k in ids) / n, "b": lost,
            "c": won, "p": binom_two_sided(lost, lost + won), "diff": diff, "lo": diff - 1.96 * se,
            "hi": diff + 1.96 * se}


def cmd_mcnemar(pos, o):
    m = mcnemar(load_tasks(pos[0]), load_tasks(pos[1]))
    worse = m["p"] < 0.05 and m["b"] > m["c"]
    rc = verdict(False if worse else None, "mcnemar", f"exact p {fmt(m['p'])}; B - A {fmt(m['diff'])} "
                 f"[{fmt(m['lo'])}, {fmt(m['hi'])}]" + ("" if worse else "; no detected loss, not equivalence"))
    table(["items", "pass_A", "pass_B", "A_only", "B_only", "p_exact", "diff", "ci95_lo", "ci95_hi"],
          [[m["n"], m["a_rate"], m["b_rate"], m["b"], m["c"], m["p"], m["diff"], m["lo"], m["hi"]]])
    return rc


COMMANDS = {
    "l0": (cmd_l0, 2, False), "dist": (cmd_dist, 2, True), "oracle": (cmd_oracle, 3, True),
    "dnll": (cmd_dnll, 2, True), "experts": (cmd_experts, 2, True), "size": (cmd_size, 2, True),
    "mcnemar": (cmd_mcnemar, 2, False),
}
FLAGS = {
    "--floor": ("floor", 2, str), "--margin-ratio": ("margin_ratio", 1, float),
    "--temperature": ("temperature", 1, float), "--top-k": ("top_k", 1, int), "--top-p": ("top_p", 1, float),
    "--temp-last": ("temp_last", 0, bool), "--buckets": ("buckets", 1, parse_buckets), "--delta": ("delta", 1, float),
    "--margin": ("margin", 1, float), "--z": ("z", 1, float), "--boot": ("boot", 1, int), "--seed": ("seed", 1, int),
    "--min-prompts": ("min_prompts", 1, int), "--vocab": ("vocab", 1, int),
}
DEFAULTS = {"floor": None, "margin_ratio": 2.0, "temperature": 1.0, "top_k": 0, "top_p": 1.0, "temp_last": False,
            "buckets": None, "delta": None, "margin": None, "z": 1.645, "boot": 2000, "seed": 0, "min_prompts": 5,
            "vocab": None}


def parse_args(argv):
    if not argv or argv[0] not in COMMANDS:
        raise ValueError("unknown subcommand")
    pos, o, i = [], dict(DEFAULTS), 1
    while i < len(argv):
        a = argv[i]
        if a.startswith("--"):
            if a not in FLAGS:
                raise ValueError(f"unknown flag {a}")
            key, n, typ = FLAGS[a]
            if n == 0:
                o[key] = True
            else:
                vals = argv[i + 1:i + 1 + n]
                if len(vals) < n:
                    raise ValueError(f"{a} needs {n} value(s)")
                vals = [typ(v) for v in vals]
                o[key] = vals if n > 1 else vals[0]
            i += 1 + n
        else:
            pos.append(a)
            i += 1
    if len(pos) != COMMANDS[argv[0]][1]:
        raise ValueError(f"{argv[0]} takes {COMMANDS[argv[0]][1]} paths")
    if o["boot"] < 1 or o["min_prompts"] < 1:
        raise ValueError("--boot and --min-prompts must be >= 1")
    return argv[0], pos, o


def main(argv):
    if any(a in ("-h", "--help") for a in argv):
        print(USAGE)
        return 0
    try:
        cmd, pos, o = parse_args(argv)
    except ValueError as e:
        print(f"{USAGE}\n\nerror: {e}", file=sys.stderr)
        return 2
    fn, _, needs_np = COMMANDS[cmd]
    if needs_np and np is None:
        print(NUMPY_MSG, file=sys.stderr)
        return 2
    try:
        if needs_np:
            o["sampling"] = Sampling(o["temperature"], o["top_k"], o["top_p"], o["temp_last"])
        return fn(pos, o)
    except DataError as e:
        print(f"data error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
