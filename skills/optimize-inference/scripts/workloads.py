#!/usr/bin/env python3
import hashlib, json, os, random, statistics, sys, threading, time

USAGE = """Workloads against a running server: context-depth sweep, concurrent clients, multi-turn sessions,
together vs alone, full-context soak. Standard library only; talks to the engine through bench.Client (http or cli
driver).

  python3 scripts/workloads.py sweep --context N [--buckets 0.0,0.25,0.5,1.0] [--text FILE] [--questions 4] [--max-tokens 256]
  python3 scripts/workloads.py clients --n 1,2,4,8 [--text FILE] [--max-tokens 256]
  python3 scripts/workloads.py multiturn --turns K [--interleave M] [--text FILE]
  python3 scripts/workloads.py invariance --n N
  python3 scripts/workloads.py soak --n N --context C [--needles 3] [--rounds 1] [--text FILE] [--max-tokens 256]

Common options:
  --config configs/x.json --out-dir DIR   standalone use (the server must already be up). Inside a bench.py run
                                          (config "tests" entry) BENCH_CONFIG, BENCH_RUN_DIR and BENCH_PASS are read
                                          from the environment instead.
  --text FILE        real text (repeated or cut to length). Without it a built-in filler is used and a warning is
                     printed: filler skews MoE routing and sparse attention, so its numbers are not "real text".
  --seed S           prompt seed (default 0). Prompt prefixes come from (seed, pass, workload, item), never the clock:
                     ctl and cand get the same prompts per pass, different passes never hit the prefix cache.
  --tpw X            tokens per word. Default: calibrated once from the server's prompt_tokens (two short requests).
  --rig rig.json     read noise.min_tokens (LOW_N bar, default 64) and cache_bypass (invariance).
  --prompt-tokens T  prompt length for clients (default 512), multiturn first turn (default 2048), invariance (256).

sweep: depth buckets are fractions of --context (the section-0 context target); bucket 0.0 is a short prompt
  (--short, default 512 tokens). Each bucket: one long prefill (max_tokens 1, cold) gives prefill_tps_d<pct>;
  then --questions short questions on the cached prefix give decode samples. decode_step_ms_d<pct> is the engine's
  step_ms (weighted by steps) when it reports one, else ms per generated token after the first. low_n_d<pct> = 1
  when fewer decode steps than the LOW_N bar were measured (raise --questions or --max-tokens).
  Bucket depth = fraction x context minus --max-tokens and 128 tokens of room for the question.
clients: for each N, --rounds (default 2) rounds of N concurrent requests started together. clients<N>_aggregate =
  completion tokens / wall time of the rounds; clients<N>_per_stream = mean per-request decode tok/s; TTFT p50/p99.
multiturn: each conversation grows by the answer plus --turn-tokens (default 256) of new text and a question per
  turn; --interleave M conversations take turns (switching evicts or keeps cache slots). Per turn: prompt tokens,
  reused (cached_tokens) vs freshly processed tokens, TTFT. reusable = the previous turn's prompt + completion.
invariance: N prompts at temperature 0, first one at a time, then all N together; invariance_same = share of
  prompts whose output_sha12 is identical. Uses rig.json cache_bypass "request_field" when set, else the together
  run hits a warm prefix cache (the path differs in cache state too; the warning says so).
soak: --rounds (default 1) rounds of N concurrent requests started together, each a different full-length document
  (--context minus --max-tokens, 128 tokens of question room and 16 per needle) with --needles (default 3) random
  codes at evenly spaced depths (the bench.py --long needle convention), at temperature 0. A code counts as found
  only when it appears verbatim in the answer. Any missed code or failed request exits non-zero, so a config
  "tests" entry flags TEST_FAIL. soak_needles = codes planted = N x rounds x needles; a failed request's codes count
  as missed.

Output: one row per request appended to <run_dir>/requests.jsonl (requests.jsonl schema plus "test", "workload",
"wall_ms"); flat numeric metrics in <run_dir>/tests/<name>/metrics.json, <name> = env BENCH_TEST_NAME or the
subcommand. Metric names: decode_step_ms_d<pct>, decode_ms_per_token_d<pct>, decode_steps_d<pct>, prefill_tps_d<pct>,
prefill_tokens_d<pct>, cached_share_d<pct>, low_n_d<pct>, clients<N>_aggregate, clients<N>_per_stream,
clients<N>_ttft_p50_ms, clients<N>_ttft_p99_ms, multiturn_reused_tokens, multiturn_fresh_tokens,
multiturn_reusable_tokens, multiturn_reuse_share, multiturn_ttft_ms_t<k>, invariance_same, invariance_n,
invariance_bypass, soak_n, soak_rounds, soak_needles, soak_found, soak_missed, soak_prompt_tokens (median),
soak_ttft_p50_ms, soak_ttft_p99_ms, real_text, failed. A failed request is logged with "error" and counted in
failed."""

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench

SUBS = {
    "sweep": {"context", "buckets", "questions", "max_tokens", "short"},
    "clients": {"n", "max_tokens", "prompt_tokens", "rounds"},
    "multiturn": {"turns", "interleave", "max_tokens", "prompt_tokens", "turn_tokens"},
    "invariance": {"n", "max_tokens", "prompt_tokens"},
    "soak": {"n", "context", "needles", "rounds", "max_tokens"},
}
COMMON = {"config", "out_dir", "text", "seed", "tpw", "rig"}
REQUIRED = {"sweep": {"context"}, "clients": {"n"}, "multiturn": {"turns"}, "invariance": {"n"},
            "soak": {"n", "context"}}
QUESTIONS = [
    "Summarize the text above in detail, section by section.",
    "List the main claims of the text above and explain each one.",
    "Explain the text above to a beginner, step by step, with examples.",
    "Write a careful critique of the text above: what is weak, what is missing, what is strong.",
    "Which questions does the text above leave open? Discuss each one at length.",
    "Rewrite the key ideas of the text above as a structured study guide.",
]
FILLER = ("the system model memory cache request token layer kernel step value result time data user server path "
          "under over before after while because which where when first second large small fast slow new old "
          "read write load store measure report change keep test run build check compare explain reach move hold "
          "river city market garden letter window history music science theory method design question answer").split()


def parse(argv):
    if not argv or argv[0] not in SUBS:
        sys.exit(USAGE)
    sub, o, i = argv[0], {}, 1
    while i < len(argv):
        k = argv[i]
        if not k.startswith("--") or i + 1 >= len(argv):
            sys.exit(USAGE)
        o[k[2:].replace("-", "_")] = argv[i + 1]
        i += 2
    if set(o) - SUBS[sub] - COMMON or REQUIRED[sub] - set(o):
        sys.exit(USAGE)
    return sub, o


def pctl(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, max(0, int(round(q * len(xs) + 0.5)) - 1))] if xs else None


def sha12(text):
    return hashlib.sha256(text.encode()).hexdigest()[:12]


class Run:
    def __init__(self, sub, o):
        self.sub = sub
        cfg_path = os.environ.get("BENCH_CONFIG") or o.get("config") or sys.exit(USAGE)
        self.cfg = bench.load_config(cfg_path)
        self.run_dir = os.environ.get("BENCH_RUN_DIR") or o.get("out_dir") or sys.exit(USAGE)
        self.pass_ = int(os.environ.get("BENCH_PASS", "0"))
        self.name = os.environ.get("BENCH_TEST_NAME") or sub
        self.seed = int(o.get("seed", 0))
        self.lock = threading.Lock()
        self.failed = 0
        rig_path = o.get("rig", "rig.json")
        self.rig = json.load(open(rig_path)) if os.path.exists(rig_path) else {}
        self.min_tokens = (self.rig.get("noise") or {}).get("min_tokens", 64)
        self.real = bool(o.get("text"))
        if self.real:
            self.words = open(o["text"], encoding="utf-8", errors="replace").read().split()
            if not self.words:
                sys.exit(f"{o['text']} has no words")
        else:
            print("warning: no --text: using built-in filler. Filler skews MoE routing and sparse attention; "
                  "these numbers are not real-text numbers.", file=sys.stderr)
            rng = random.Random(f"filler-{self.seed}")
            self.words = [rng.choice(FILLER) + ("." if rng.random() < 0.08 else "") for _ in range(50000)]
        self.tpw = float(o["tpw"]) if o.get("tpw") else None
        os.makedirs(self.run_dir, exist_ok=True)

    def prefix(self, tag):
        return f"[workloads {self.name} seed {self.seed} pass {self.pass_} {tag}]\n"

    def text(self, tokens, tag):
        n = max(1, int(tokens / (self.tpw or 1.3)))
        start = random.Random(f"{self.seed}-{self.pass_}-{tag}").randrange(len(self.words))
        w, L = self.words, len(self.words)
        return " ".join(w[(start + i) % L] for i in range(n))

    def chat(self, client, messages, max_tokens, prompt_id, batch=1, cache="cold", temperature=None, extra=None):
        t0 = time.time()
        try:
            r = client.chat(messages, max_tokens, temperature=temperature, seed=self.seed, extra=extra, kind="test",
                            prompt_id=prompt_id, pass_=self.pass_)
        except Exception as e:
            r = {"error": f"{type(e).__name__}: {e}", "prompt_id": prompt_id, "pass": self.pass_}
        t1 = time.time()
        if r.get("error"):
            with self.lock:
                self.failed += 1
            print(f"request {prompt_id} failed: {r['error']}", file=sys.stderr)
        if not r.get("output_sha12") and r.get("text") is not None:
            r["output_sha12"] = sha12(r["text"])
        r["wall_ms"] = round((t1 - t0) * 1000, 1)
        row = {k: v for k, v in r.items() if k not in ("text", "_mono", "tokens")}
        path = dict(row.get("path") or {})
        path.update(batch=batch, cache=cache)
        path.setdefault("chunk", None)
        row.update(test=self.name, workload=self.sub, path=path)
        with self.lock:
            bench.append_jsonl(os.path.join(self.run_dir, "requests.jsonl"), row)
        r["_t0"], r["_t1"] = t0, t1
        return r

    def calibrate(self, client):
        if self.tpw:
            return
        pts = []
        for n in (200, 2000):
            body = " ".join(self.words[i % len(self.words)] for i in range(n))
            r = self.chat(client, user(self.prefix(f"calibrate-{n}") + body), 1, f"calibrate-{n}")
            pts.append(r.get("prompt_tokens"))
        if all(pts) and pts[1] > pts[0]:
            self.tpw = (pts[1] - pts[0]) / 1800
            print(f"tokens per word: {self.tpw:.3f} (from server prompt_tokens)")
        else:
            self.tpw = 1.3
            print("warning: server gave no prompt_tokens; tokens per word set to 1.3 (pass --tpw)", file=sys.stderr)

    def write_metrics(self, metrics):
        metrics.update(real_text=int(self.real), failed=self.failed)
        d = os.path.join(self.run_dir, "tests", self.name)
        os.makedirs(d, exist_ok=True)
        flat = {k: round(v, 4) if isinstance(v, float) else v for k, v in metrics.items() if v is not None}
        with open(os.path.join(d, "metrics.json"), "w") as f:
            json.dump(flat, f, indent=1, sort_keys=True)
        print(f"wrote {os.path.join(d, 'metrics.json')}")


def user(content):
    return [{"role": "user", "content": content}]


def ttft(r):
    return r.get("ttft_ms") if r.get("ttft_ms") is not None else r.get("wall_ms")


def cell(v, w, p=1):
    return f"{v:>{w}.{p}f}" if v is not None else f"{'-':>{w}}"


def sweep(run, o):
    ctx, q_n = int(o["context"]), int(o.get("questions", 4))
    mt, short = int(o.get("max_tokens", 256)), int(o.get("short", 512))
    buckets = [float(b) for b in o.get("buckets", "0.0,0.25,0.5,1.0").split(",")]
    c = bench.Client(run.cfg)
    run.calibrate(c)
    m = {}
    print(f"{'bucket':>7} {'depth':>8} {'prefill tok/s':>14} {'step ms':>8} {'ms/token':>9} {'steps':>6} {'cached':>7}")
    for f in buckets:
        pct = round(f * 100)
        depth = short if f == 0 else max(short, int(f * ctx) - mt - 128)
        doc = run.prefix(f"sweep-d{pct}") + run.text(depth, f"sweep-d{pct}")
        pre = run.chat(c, user(doc + "\n\nReply with the single word OK."), 1, f"sweep-d{pct}-prefill", cache="cold")
        pt, t = pre.get("prompt_tokens"), ttft(pre)
        if not pre.get("error") and pt and t:
            m[f"prefill_tps_d{pct}"], m[f"prefill_tokens_d{pct}"] = pt / t * 1000, pt
        step_time = step_n = tok_time = tok_n = 0.0
        shares = []
        for q in range(q_n):
            r = run.chat(c, user(doc + "\n\n" + QUESTIONS[q % len(QUESTIONS)]), mt, f"sweep-d{pct}-q{q}", cache="warm")
            ct = r.get("completion_tokens") or 0
            if r.get("error") or ct < 2:
                continue
            steps = ct - 1
            if r.get("decode_ms"):
                tok_time, tok_n = tok_time + r["decode_ms"], tok_n + steps
            if r.get("step_ms"):
                n_steps = r["decode_ms"] / r["step_ms"] if r.get("decode_ms") else steps
                step_time, step_n = step_time + r["step_ms"] * n_steps, step_n + n_steps
            if r.get("cached_tokens") is not None and r.get("prompt_tokens"):
                shares.append(r["cached_tokens"] / r["prompt_tokens"])
        per_tok = tok_time / tok_n if tok_n else None
        step = step_time / step_n if step_n else per_tok
        n_samples = int(step_n or tok_n)
        m[f"decode_ms_per_token_d{pct}"], m[f"decode_step_ms_d{pct}"] = per_tok, step
        m[f"decode_steps_d{pct}"], m[f"low_n_d{pct}"] = n_samples, int(n_samples < run.min_tokens)
        share = statistics.mean(shares) if shares else None
        m[f"cached_share_d{pct}"] = share
        if share is not None and share < 0.5:
            print(f"warning: d{pct} questions reused only {share:.0%} of the prompt from cache: decode samples paid "
                  "a fresh prefill", file=sys.stderr)
        if n_samples < run.min_tokens:
            print(f"LOW_N: d{pct} has {n_samples} decode steps (< {run.min_tokens})", file=sys.stderr)
        print(f"{'d' + str(pct):>7} {pt or depth:>8} {cell(m.get(f'prefill_tps_d{pct}'), 14, 0)} {cell(step, 8, 2)} "
              f"{cell(per_tok, 9, 2)} {n_samples:>6} {cell(share, 7, 2)}")
    run.write_metrics(m)


def clients(run, o):
    ns = [int(x) for x in o["n"].split(",")]
    mt, pt_len, rounds = int(o.get("max_tokens", 256)), int(o.get("prompt_tokens", 512)), int(o.get("rounds", 2))
    run.calibrate(bench.Client(run.cfg))
    m = {}
    print(f"{'N':>4} {'aggregate tok/s':>16} {'per stream':>11} {'TTFT p50 ms':>12} {'TTFT p99 ms':>12}")
    for n in ns:
        toks = wall = 0.0
        per_stream, ttfts = [], []
        for rd in range(rounds):
            out = [None] * n
            barrier = threading.Barrier(n)

            def worker(i, n=n, rd=rd, out=out, barrier=barrier):
                c = bench.Client(run.cfg)
                tag = f"clients-n{n}-r{rd}-s{i}"
                msgs = user(run.prefix(tag) + run.text(pt_len, tag) + "\n\n" + QUESTIONS[i % len(QUESTIONS)])
                barrier.wait()
                out[i] = run.chat(c, msgs, mt, tag, batch=n)

            threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            ok = [r for r in out if r and not r.get("error")]
            if not ok:
                continue
            toks += sum(r.get("completion_tokens") or 0 for r in ok)
            wall += max(r["_t1"] for r in ok) - min(r["_t0"] for r in ok)
            for r in ok:
                ct = r.get("completion_tokens") or 0
                if r.get("decode_ms") and ct > 1:
                    per_stream.append((ct - 1) / r["decode_ms"] * 1000)
                if ttft(r) is not None:
                    ttfts.append(ttft(r))
        m[f"clients{n}_aggregate"] = toks / wall if wall else None
        m[f"clients{n}_per_stream"] = statistics.mean(per_stream) if per_stream else None
        m[f"clients{n}_ttft_p50_ms"], m[f"clients{n}_ttft_p99_ms"] = pctl(ttfts, 0.5), pctl(ttfts, 0.99)
        print(f"{n:>4} {cell(m[f'clients{n}_aggregate'], 16)} {cell(m[f'clients{n}_per_stream'], 11)} "
              f"{cell(m[f'clients{n}_ttft_p50_ms'], 12)} {cell(m[f'clients{n}_ttft_p99_ms'], 12)}")
    run.write_metrics(m)


def multiturn(run, o):
    k_n, m_n = int(o["turns"]), int(o.get("interleave", 1))
    mt, first, grow = int(o.get("max_tokens", 256)), int(o.get("prompt_tokens", 2048)), int(o.get("turn_tokens", 256))
    c = bench.Client(run.cfg)
    run.calibrate(c)
    convs = [user(run.prefix(f"multiturn-c{j}") + run.text(first, f"multiturn-c{j}") + "\n\n" + QUESTIONS[0])
             for j in range(m_n)]
    prev = [0] * m_n
    reused = fresh = reusable = 0
    cached_reported = True
    m = {}
    print(f"{'turn':>4} {'prompt tok':>10} {'reusable':>9} {'reused':>8} {'fresh':>8} {'TTFT ms':>9}")
    for k in range(k_n):
        rows = []
        for j in range(m_n):
            r = run.chat(c, convs[j], mt, f"multiturn-c{j}-t{k}", cache="warm" if k else "cold")
            if r.get("error"):
                prev[j] = 0
                continue
            pt, ct, cached = r.get("prompt_tokens") or 0, r.get("completion_tokens") or 0, r.get("cached_tokens")
            if k:
                reusable += prev[j]
                if cached is None:
                    cached_reported = False
                else:
                    reused, fresh = reused + cached, fresh + pt - cached
            rows.append((pt, prev[j] if k else 0, cached, ttft(r)))
            convs[j] = convs[j] + [{"role": "assistant", "content": r.get("text") or ""},
                                   {"role": "user", "content": run.text(grow, f"multiturn-c{j}-t{k}") + "\n\n"
                                    + QUESTIONS[(k + 1) % len(QUESTIONS)]}]
            prev[j] = pt + ct
        if not rows:
            continue
        ts = [x[3] for x in rows if x[3] is not None]
        t = statistics.median(ts) if ts else None
        m[f"multiturn_ttft_ms_t{k}"] = t
        with_cache = [x for x in rows if x[2] is not None]
        med = lambda xs: statistics.median(xs) if xs else None
        print(f"{k:>4} {cell(med([x[0] for x in rows]), 10, 0)} {cell(med([x[1] for x in rows]), 9, 0)} "
              f"{cell(med([x[2] for x in with_cache]), 8, 0)} {cell(med([x[0] - x[2] for x in with_cache]), 8, 0)} "
              f"{cell(t, 9)}")
    m["multiturn_reusable_tokens"] = reusable
    if cached_reported and k_n > 1:
        m.update(multiturn_reused_tokens=reused, multiturn_fresh_tokens=fresh,
                 multiturn_reuse_share=reused / reusable if reusable else None)
    elif k_n > 1:
        print("warning: the engine does not report cached_tokens; reuse is not available (read it from TTFT growth)",
              file=sys.stderr)
    run.write_metrics(m)


def invariance(run, o):
    n, mt, pt_len = int(o["n"]), int(o.get("max_tokens", 128)), int(o.get("prompt_tokens", 256))
    run.calibrate(bench.Client(run.cfg))
    bypass = run.rig.get("cache_bypass") or {}
    extra = bypass.get("request_field") if bypass.get("mode") == "request_field" else None
    cache = "bypass" if extra else "warm"
    if not extra:
        print("warning: no rig.json cache_bypass request_field: the together run hits a warm prefix cache, so a "
              "difference may come from the cache state, not from batching", file=sys.stderr)
    prompts = [user(run.prefix(f"invariance-p{i}") + run.text(pt_len, f"invariance-p{i}") + "\n\n"
                    + QUESTIONS[i % len(QUESTIONS)]) for i in range(n)]
    c = bench.Client(run.cfg)
    alone = [run.chat(c, p, mt, f"invariance-p{i}", batch=1, cache="bypass" if extra else "cold", temperature=0,
                      extra=extra) for i, p in enumerate(prompts)]
    together = [None] * n
    barrier = threading.Barrier(n)

    def worker(i):
        cl = bench.Client(run.cfg)
        barrier.wait()
        together[i] = run.chat(cl, prompts[i], mt, f"invariance-p{i}", batch=n, cache=cache, temperature=0, extra=extra)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    pairs = [(a, b) for a, b in zip(alone, together) if not a.get("error") and b and not b.get("error")]
    same = sum(a.get("output_sha12") == b.get("output_sha12") for a, b in pairs)
    for i, (a, b) in enumerate(zip(alone, together)):
        if b and a.get("output_sha12") != b.get("output_sha12"):
            print(f"invariance-p{i}: alone {a.get('output_sha12')} together {b.get('output_sha12')}")
    print(f"identical outputs alone vs together: {same}/{len(pairs)}")
    run.write_metrics({"invariance_same": same / len(pairs) if pairs else None, "invariance_n": len(pairs),
                       "invariance_bypass": int(bool(extra))})


def soak(run, o):
    n, ctx, k = int(o["n"]), int(o["context"]), int(o.get("needles", 3))
    rounds, mt = int(o.get("rounds", 1)), int(o.get("max_tokens", 256))
    depth = ctx - mt - 128 - 16 * k
    run.calibrate(bench.Client(run.cfg))
    found = missed = 0
    ttfts, pts = [], []
    print(f"{'round':>5} {'ok':>4} {'found':>9} {'TTFT p50 ms':>12} {'TTFT max ms':>12}")
    for rd in range(rounds):
        out = [None] * n
        barrier = threading.Barrier(n)
        docs = []
        for i in range(n):
            tag = f"soak-r{rd}-s{i}"
            words = run.text(depth, tag).split()
            codes = bench.plant_needles(words, random.Random(f"{run.seed}-{run.pass_}-{tag}-needles"), k)
            docs.append((tag, user(run.prefix(tag) + " ".join(words) + bench.NEEDLE_QUESTION), codes,
                         bench.Client(run.cfg)))

        def worker(i, out=out, barrier=barrier, docs=docs):
            tag, msgs, codes, c = docs[i]
            barrier.wait()
            out[i] = run.chat(c, msgs, mt, tag, batch=n, temperature=0), codes

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        hits_rd, ts = 0, []
        for i, (r, codes) in enumerate(out):
            lost = codes if r.get("error") else bench.missing_needles(r.get("text") or "", codes)
            hits_rd += k - len(lost)
            if lost:
                print(f"NEEDLE_MISS soak-r{rd}-s{i}: {k - len(lost)}/{k} found, missing {' '.join(lost)}",
                      file=sys.stderr)
            if not r.get("error"):
                ts += [ttft(r)] if ttft(r) is not None else []
                pts += [r["prompt_tokens"]] if r.get("prompt_tokens") else []
        found, missed, ttfts = found + hits_rd, missed + n * k - hits_rd, ttfts + ts
        print(f"{rd:>5} {len([r for r, _ in out if not r.get('error')]):>4} {f'{hits_rd}/{n * k}':>9} "
              f"{cell(pctl(ts, 0.5), 12)} {cell(max(ts) if ts else None, 12)}")
    run.write_metrics({"soak_n": n, "soak_rounds": rounds, "soak_needles": found + missed, "soak_found": found,
                       "soak_missed": missed, "soak_prompt_tokens": statistics.median(pts) if pts else None,
                       "soak_ttft_p50_ms": pctl(ttfts, 0.5), "soak_ttft_p99_ms": pctl(ttfts, 0.99)})
    if missed:
        sys.exit(f"soak failed: {missed}/{found + missed} code(s) missed, {run.failed} request(s) failed")


def main(argv):
    sub, o = parse(argv)
    run = Run(sub, o)
    {"sweep": sweep, "clients": clients, "multiturn": multiturn, "invariance": invariance, "soak": soak}[sub](run, o)
    if run.failed:
        sys.exit(f"{run.failed} request(s) failed")


if __name__ == "__main__":
    main(sys.argv[1:])
