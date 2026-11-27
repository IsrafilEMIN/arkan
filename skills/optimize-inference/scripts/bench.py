#!/usr/bin/env python3
"""Engine-agnostic hill-climb benchmark for any OpenAI-compatible server (vLLM, SGLang, llama.cpp server,
TabbyAPI, MLX-LM server, LM Studio, Ollama's /v1 ...) or any engine behind a small CLI driver. Standard library only.

  python3 scripts/bench.py run configs/NAME.json [--passes N] [--long N[,N...]] [--skip-cN] [--reps 6] [--reuse]
                                                 [--determinism] [--no-samplers] [--rig rig.json]
  python3 scripts/bench.py show [ledger.jsonl]
  python3 scripts/bench.py verdict --ctl NAME --cand NAME [--since ISO] [--metric c1_decode] [--watch m1,m2]
                                   [--predicted PCT] [--surprise-ratio 2] [--ledger ledger.jsonl] [--rig rig.json]
  python3 scripts/bench.py verdict CTL_A CAND CTL_B [--metric ...] [--watch ...] [--predicted PCT] [--ledger ...]
                                                    (triple mode)
  python3 scripts/bench.py noise [--ledger ledger.jsonl] [--rig rig.json]    (pooled SD per config hash x metric)
  python3 scripts/bench.py board [--baseline NAME] [--ceilings ceilings.json] [--ledger ledger.jsonl]
  python3 scripts/bench.py resolve configs/NAME.json                        (print the resolved config)

Run from the working directory (rig.json, ledger.jsonl, configs/, runs/ live there). rig.py is imported from this
script's directory; without it the run still happens and records "rig.py" under not_available.

run options
  --passes N     timed passes inside one load (default: config "passes", else 1). Each pass repeats ttft, c1, cN,
                 prefill and tests with fresh prompt prefixes, so the prefix cache cannot hit between passes.
  --long N,...   one long-context needle retrieval per length after the passes (e.g. 65536,131072).
  --skip-cN      skip the concurrency test.   --reps 6   c1 requests per pass.
  --reuse        skip stop+launch if the server is healthy and .bench-server.json records the same launch,
                 base_url and env (use it for request-field options, e.g. an extra_body toggle).
  --determinism  send the 6 panel prompts twice, greedy, with the rig's cache bypass; sets "deterministic".
  --no-samplers  no rig.Sampler (and so no host-RAM watchdog): only for the once-per-rig logging-cost A/B.
  --rig PATH     rig.json (default rig.json; missing -> rig.py detected defaults).

Config (JSON; the notes after "<-" are explanation only, not JSON):
  {
    "name": "ctl-a",                              <- unique run name (ledger key)
    "base": "configs/best.json",                  <- optional: start from this config, then apply the keys below
    "set": {"memory.cap_gib": 40}, "unset": ["tests"],    <- dotted-path edits of the base
    "args_set": {"--ubatch-size": "1024", "--flag-only": true, "--gone": null},  <- edit the launch argv
    "args_del": ["--no-mmap"],                     <- remove a launch flag (and its value)
    "env": {"K": "V"},                             <- exported to launch, stop, health and the cli driver
    "driver": "http",                              <- "http" (OpenAI-compatible, default) or "cli"
    "cli": ["python3", "examples/cli-driver.py", "--url", "http://127.0.0.1:8080"],   <- driver "cli" only
    "base_url": "http://127.0.0.1:8000",
    "model": "my-model",                           <- served model name
    "launch": ["docker", "run", "-d", "..."],      <- optional; omit to benchmark an already-running server
    "stop":   ["docker", "stop", "-t", "60", "srv"],  <- optional; without it a pidfile server is killed by PID
    "pidfile": "server.pid",                       <- native server PID (the launch must rewrite it)
    "container": "srv",                            <- docker container name (default: launch "--name")
    "engine_log": "server.log",                    <- engine log; offsets are recorded per request and test
    "timings": "openai",                           <- "openai" | "llamacpp" | {"regex": {"step_ms": "..(num).."}}
    "health": ["curl", "-sf", "http://127.0.0.1:8000/health"],   <- optional health command (exit 0 = up)
    "health_timeout_s": 900,
    "identity": {"binary": "/path/engine", "repo": "/path/src"},   <- hashed into identity.json
    "claims": null,                                <- "l0" | "l1" | "l2" | null: the candidate's quality claim
    "passes": 3,
    "seed": 1,                                     <- prompt-prefix seed; keep it equal across ctl and cand
    "cards": [0, 1],                               <- cards for rig.py preflight (default: all)
    "concurrency": 4,                              <- N for the cN test
    "prefill_lengths": [4096, 32768],              <- approximate prompt tokens for cold prefill
    "extra_body": {"chat_template_kwargs": {"enable_thinking": false}},  <- merged into every request
    "temperature": 0.6,
    "token_log": {"top_logprobs": 5},              <- ask for logprobs; written to runs/<id>/tokens.jsonl
    "no_progress_s": 600,                          <- override rig.json watchdog.no_progress_s
    "chunk": null,                                 <- optional: engine prefill chunk, recorded in request paths
    "memory": {"cap_gib": 46, "probe": ["bash", "scripts/mem.sh", "--pid", "{pid}"], "interval_s": 3},
    "preflight": [["systemctl", "is-active", "fan-guard"]],   <- must exit 0 before launch and at the end
    "tests": [{"name": "sweep", "cmd": ["python3", "scripts/workloads.py", "sweep", "--context", "65536"],
               "timeout_s": 1800, "once": false}],
    "proof": ["bash", "proof.sh"], "proof_timeout_s": 300
  }

base and deltas: "base" is read relative to the working directory, else to the config's directory, and may chain.
Other keys override the base (dicts merge deeply, lists replace). args_set/args_del edit the LAST occurrence of a
flag in "launch" ("--flag value", "--flag=value" or a bare flag; true = bare flag, null/false = remove); a new flag is
appended. A shell launch must pass engine args as list items after the script, e.g.
  ["bash", "-c", "nohup \\"$@\\" > server.log 2>&1 < /dev/null & echo $! > server.pid", "launch", "engine", "--flag", "v"]
The resolved config is stored as runs/<id>/config.resolved.json; config_hash = sha256 of it without "name".

Drivers. http: streams /v1/chat/completions; token counts come from the server's usage (never streamed chunks).
cli: per request the harness writes ONE JSON object to the command's stdin
  {"messages": [...], "max_tokens": int, "temperature": float, "seed": int|null, "extra": {...}}
and reads ONE JSON object from its stdout
  {"text": str, "prompt_tokens": int, "completion_tokens": int, "ttft_ms": float, "decode_ms": float, "engine": {...}}
(the driver may keep a persistent engine process behind it; "engine" may carry "usage", "timings", "logprobs").
The whole cli request is bounded by the no-progress timeout. See examples/cli-driver.py.
Timings adapters: openai (usage, cached_tokens from prompt_tokens_details), llamacpp ("timings": predicted_ms,
draft_n, draft_n_accepted, cache_n), regex (applied to the engine_log bytes written during each request; values of
step_ms are medianed, others summed; per-request attribution is exact only at c1).

Run directory runs/<name>-<UTC %Y%m%dT%H%M%S>/:
  config.resolved.json  identity.json (host, bench sha, binary sha256, repo commit+dirty, server models)
  requests.jsonl  one row per request:
    {"run_id","pass","kind":"warmup|ttft|c1|cN|prefill|long|determinism|test","prompt_id","prompt_sha","seed",
     "prompt_tokens","completion_tokens","cached_tokens","ttft_ms","decode_ms","decode_tps","step_ms","draft_n",
     "draft_accepted","finish_reason","output_sha12","loop","t_start","t_end",
     "path":{"batch","chunk","cache":"cold|warm|bypass"},"engine":{...raw adapter fields...}}
  samples.jsonl (rig.Sampler, 1 s)  events.jsonl (launch, phases, watchdogs, flags)  tokens.jsonl (token_log)
  tests/<name>/ (log.pass<P>.txt, metrics.json -> metrics.pass<P>.json)  proof.txt

Prompts. Every prompt starts with "[run-seed S pass P prompt ID] " (ID = prompt id, e.g. c1-3, prefill-4096; P = pass
inside the run): ctl and cand get the same prompts per pass; passes get different prefixes. With --reuse or an
attached server and a rig.json cache_bypass mode request_field or flush_cmd, the prefixes stay identical and the
bypass is applied to every timed request (path.cache = "bypass"). Without a bypass, P continues from
.bench-server.json "passes_used" so no prompt repeats on the same server; verdict then pairs nothing (prompt_sha
differs) and falls back to per-pass samples.
Filler documents use the tokens per word calibrated once per run from the server's prompt_tokens (two filler sizes;
fallback 1.6, recorded as not available). .bench-server.json also lists the server "pids" (pidfile, docker top)
so rig.py check and queue.sh allow our own server on the cards.

Ledger row (ledger.jsonl, schema 2): {"schema": 2, "run_id", "run_dir", "name", "config_hash", "time", "ok", "flags",
"not_available", "passes", "metrics", "metrics_passes", "per_prompt", "deterministic", "identity", "state_start",
"state_end", "phases", "tests", "proof", "startup_s", "mem_peak_gib", "host_ram_min_gib", "reused_server", ...}.
Metrics (median over passes; c1_decode = median of all c1 samples): ttft_short_ms, c1_decode, c<N>_aggregate
(wall clock), prefill_<L> (prompt_tokens / TTFT on a cold document), step_ms and accept_len when the engine reports
them, and test metrics "<test>.<metric>" from tests/<name>/metrics.json (flat JSON of numbers, read after each pass).
per_prompt: {prompt_id: {field: [per-pass values]}}. Old rows without "schema" stay readable by show and verdict.

Flags: LOOP, REQ_FAIL, ON_BATTERY, MEM_CAP, MEM_PROBE_FAIL, NEEDLE_MISS, TEST_FAIL, NO_PROOF, RIG_BLOCK (preflight
blocked: run not started, ok=false), HOST_FLOOR (host-RAM floor watchdog stopped the run), NO_PROGRESS (no token for
no_progress_s: abort, stop), STATE_CHANGED (power limit or persistence changed: run void), HOST_BUSY (CPU/disk above
the idle baseline in the timed window), LOW_N (< min_samples c1 samples or < min_tokens per sample). A check or
collector that a platform lacks goes into "not_available", never into flags. Exit code 1 when ok is false.
MEM_PROBE_FAIL: the memory probe failed after the server became healthy, so the cap was not enforced. "{pid}" in the
probe is replaced by the pidfile's PID. Set no_progress_s above the longest expected prefill.

Preflight: rig.py preflight (cards idle, host RAM floor, safety hooks, on AC power, ...) plus config "preflight"
commands; a failed blocking check writes a RIG_BLOCK row and exits 1. rig.json checks.<name>.level decides what blocks:
on_ac (default block) also sets ON_BATTERY at the end of the run only when its level is block; host_ram_floor at
level block lets the watchdog stop the server. Machine state (rig.state) is recorded at start and end.

Test hooks run after each pass (or only the first with "once": true), with env BENCH_BASE_URL, BENCH_MODEL,
BENCH_RUN, BENCH_RUN_ID, BENCH_RUN_DIR, BENCH_CONFIG (resolved config path), BENCH_PASS, BENCH_ENGINE_LOG,
BENCH_LOG_OFFSET (engine-log byte offset at test start), BENCH_TEST_NAME. Non-zero exit or timeout flags TEST_FAIL.
proof runs once after everything, while the server is up; it must exit 0 only if the changed code path really ran.
The server is left running after a run (the next run's launch stops it first); stop it yourself when done.

--determinism uses rig.json "cache_bypass": request_field (merged into both sends), flush_cmd (run before each send),
reload (prints how to compare two control loads; deterministic stays null), none (not available).

verdict. Pair mode reads every ok load of --ctl and --cand (since --since); triple mode the latest CTL_A, CAND,
CTL_B rows (the candidate must also beat each control). Gain g (%, positive = better): paired per-prompt ratios
(geometric mean over prompts) plus totals (total tokens / total time); metrics without per-prompt data, or prompts
that differ between ctl and cand (reused server without cache bypass: printed as "unpaired"), use per-pass samples.
Noise from the ledger (ok rows with the control's config_hash, last rig.json noise.window rows): sd_within = pooled
SD between passes of one load (df = sum(passes - 1)); sd_load = SD of the load means between loads.
Calibrated when the control hash has >= noise.min_loads (default 3) ok loads AND df >= noise.min_df (default 4).
  t          = t(0.975, df = control loads - 1) / 1.96: widens bar and CI while sd_load rests on few loads
               (3 loads: x2.19, 6 loads: x1.31, > 30 loads: x1)
  bar        = max(k x t x sd_load x sqrt(1/L_ctl + 1/L_cand), floor_pct)      (k = noise.k, default 2.5)
  se_total   = sqrt(se_prompt^2 + sd_load^2 x (1/L_ctl + 1/L_cand))  (se_prompt = bootstrap SD over prompts)
  lower      = g - 1.96 x t x se_total;   the printed CI is g +- 1.96 x t x se_total
  drift      = newest control load in the window vs the mean of the other window control loads;
               REPEAT if |x - mean| > max(k x sd_load x sqrt(1 + 1/(L-1)), floor_pct)
  trend      = first vs last pass of a window load; REPEAT if above max(k x sqrt(2) x sd_within, floor_pct)
  Window = the selected candidate loads plus the control loads from the last control load before the first
  selected candidate load onward; drift, trend and HOST_BUSY look only there (older flagged loads are ignored).
  Uncalibrated: bar 3%, drift and trend 5%, se_total = se_prompt (the CI is prompt-only), marked "uncalibrated".
  An uncalibrated pair verdict is never ACCEPT or BELOW_BAR: it asks for more control loads (or the triple).
  Surprise: with --predicted PCT, REPEAT when g > --surprise-ratio (default 2) x PCT and the candidate has < 2 loads;
  without it, REPEAT when g > 10% and the candidate has 1 load.
  ACCEPT     g >= bar and lower > 0, no REPEAT condition.
  BELOW_BAR  lower > 0 but g < bar: the gain is real but under the bar; the user decides.
  REPEAT     g >= bar but lower <= 0; or 0 < g < bar, lower <= 0, upper >= bar with one candidate load (inconclusive:
             one more load of each); or drift, trend, HOST_BUSY or surprise: run one more load in reverse order (BA).
  REJECT     anything else: no gain, a watched metric worse by more than its bar, a run not ok / flagged, ANSWER_DIFF.
  Watched by default: c1_decode, c<N>_aggregate, prefill_<L>, step_ms, mem_peak_gib (--watch replaces the list).
  NOISY (per-pass SD above the bar) and LOW_N are watch-only. ANSWER_DIFF: the candidate claims l0, the control is
  known deterministic (--determinism), and a greedy answer (determinism, long, prefill rows) differs on the same
  prompt and compute path; with unpaired prompts it is reported as not available. The verdict row (with se_total,
  se_prompt, se_load, ci, bar_pct, calibrated) goes to verdicts.jsonl next to the ledger.
noise prints the pooled SDs; board prints the progress table from the ledger (ok loads only, + verdicts, +
ceilings.json from ceiling.py: % of hard and practical ceiling; test metrics match ceilings by their name without
the test prefix).

Import API (nothing runs at import): load_config(path) -> resolved dict; Client(cfg).chat(messages, max_tokens,
temperature=None, seed=None, extra=None, kind="test", prompt_id=None, pass_=0, batch=1, cache="cold") -> one
requests.jsonl-shaped dict plus "text" (it does not write; failures raise, NoProgress on timeout);
append_jsonl(path, row).
"""
import datetime, hashlib, json, math, os, platform, random, re, shlex, signal, socket, statistics, string, subprocess
import sys, threading, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
PROMPTS = [
    "Write a Python implementation of an LRU cache with O(1) get and put, with docstrings and tests.",
    "Explain, step by step, how TCP congestion control works, including slow start and fast recovery.",
    "Write a short story (about 600 words) about a lighthouse keeper who finds a message in a bottle.",
    "Compare B-trees and LSM-trees for a write-heavy database workload. Use a table and give a recommendation.",
    "Write a bash script that backs up a directory to a timestamped tar.gz and keeps only the last 7 backups.",
    "Summarise the causes and consequences of the 1929 stock market crash in five paragraphs.",
]
WORDS = ("river stone paper cloud engine garden silver market winter orange signal harbor violet "
         "candle forest mirror thunder copper meadow lantern").split()
NOISE_DEFAULTS = {"k": 2.5, "floor_pct": 0.3, "window": 20, "min_samples": 6, "min_tokens": 64, "min_loads": 3,
                  "min_df": 4}
FALLBACK = {"bar": 3.0, "drift": 5.0, "surprise": 10.0}
Z95 = 1.96
T975 = {1: 12.71, 2: 4.30, 3: 3.18, 4: 2.78, 5: 2.57, 6: 2.45, 7: 2.36, 8: 2.31, 9: 2.26, 10: 2.23, 12: 2.18, 15: 2.13,
        20: 2.09, 30: 2.04}


def t_scale(df):
    if df is None or df < 1:
        return T975[1] / Z95
    keys = [d for d in T975 if d <= df]
    return (T975[max(keys)] if df <= 30 else Z95) / Z95


WATCH_FLAGS = {"LOW_N", "NOISY"}
REPEAT_FLAGS = {"HOST_BUSY"}
VOID_FLAGS = {"RIG_BLOCK", "HOST_FLOOR", "NO_PROGRESS", "STATE_CHANGED", "MEM_CAP", "ON_BATTERY"}
LOWER_IS_BETTER = {"ttft_short_ms", "startup_s", "mem_peak_gib", "step_ms"}
SERVER_STATE = ".bench-server.json"
DELTA_KEYS = ("base", "set", "unset", "args_set", "args_del")
_LOCK = threading.Lock()


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def now_iso(ms=False):
    return datetime.datetime.now().astimezone().isoformat(timespec="milliseconds" if ms else "seconds")


def parse_time(s):
    d = datetime.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    return d if d.tzinfo else d.astimezone()


def numeric(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and not (isinstance(v, float) and math.isnan(v))


def append_jsonl(path, row):
    line = json.dumps(row, default=str) + "\n"
    with _LOCK, open(path, "a") as f:
        f.write(line)


def read_jsonl(path):
    out = []
    if not path or not os.path.exists(path):
        return out
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    pass
    return out


def sha12(text):
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:12]


def read_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError, TypeError):
        return default


def _merge(base, over):
    out = dict(base)
    for k, v in over.items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def _dotted(cfg, key, value=None, delete=False):
    parts, d = key.split("."), cfg
    for p in parts[:-1]:
        if not isinstance(d.get(p), dict):
            if delete:
                return
            d[p] = {}
        d = d[p]
    if delete:
        d.pop(parts[-1], None)
    else:
        d[parts[-1]] = value


def _is_flag(x):
    return x.startswith("-") and not re.match(r"-\d", x)


def _edit_args(launch, args_set, args_del, where):
    argv = [str(x) for x in launch]
    shell = len(argv) >= 3 and argv[1] == "-c"
    first = 3 if shell else 1

    def find(flag):
        for i in range(len(argv) - 1, first - 1, -1):
            if argv[i] == flag or argv[i].startswith(flag + "="):
                return i
        return None

    def span(i, flag):
        return 2 if argv[i] == flag and i + 1 < len(argv) and not _is_flag(argv[i + 1]) else 1

    def fail(flag, what):
        sys.exit(f"{where}: cannot {what} {flag}: not found in launch. A shell launch must pass engine args as list "
                 "items after the script (see examples/config-mlx-macos.json)")

    for flag in args_del:
        i = find(flag)
        if i is None:
            fail(flag, "delete")
        del argv[i:i + span(i, flag)]
    for flag, val in args_set.items():
        i = find(flag)
        if val is None or val is False:
            if i is not None:
                del argv[i:i + span(i, flag)]
            continue
        new = [flag] if val is True else [flag, str(val)]
        if i is None:
            if shell and len(argv) == 3:
                fail(flag, "set")
            argv.extend(new)
        else:
            argv[i:i + span(i, flag)] = new
    return argv


def load_config(path, _seen=()):
    ap = os.path.abspath(path)
    if ap in _seen:
        sys.exit(f"config base cycle at {path}")
    cfg = read_json(path)
    if not isinstance(cfg, dict):
        sys.exit(f"cannot read config {path}")
    out = {}
    if cfg.get("base"):
        b = cfg["base"]
        bp = b if os.path.exists(b) else os.path.join(os.path.dirname(path), b)
        out = load_config(bp, _seen + (ap,))
        if "name" not in cfg:
            sys.exit(f"{path}: a config with a base needs its own name")
    out = _merge(out, {k: v for k, v in cfg.items() if k not in DELTA_KEYS})
    for k in cfg.get("unset") or []:
        _dotted(out, k, delete=True)
    for k, v in (cfg.get("set") or {}).items():
        _dotted(out, k, v)
    if cfg.get("args_set") or cfg.get("args_del"):
        if not out.get("launch"):
            sys.exit(f"{path}: args_set/args_del need a launch command")
        out["launch"] = _edit_args(out["launch"], cfg.get("args_set") or {}, cfg.get("args_del") or [], path)
    if "name" not in out:
        sys.exit(f"{path}: missing name")
    return out


def config_hash(cfg):
    return hashlib.sha256(json.dumps({k: v for k, v in cfg.items() if k != "name"}, sort_keys=True).encode()).hexdigest()


def rig_noise(rig):
    return {**NOISE_DEFAULTS, **((rig or {}).get("noise") or {})}


class NoProgress(Exception):
    pass


class Abort(Exception):
    pass


def looping(text, n=8, thresh=0.5):
    w = text.split()
    grams = [tuple(w[i:i + n]) for i in range(max(0, len(w) - n))]
    return len(grams) > 50 and 1 - len(set(grams)) / len(grams) > thresh


def adapt(timings, engine, log_slice):
    out = {}
    usage = engine.get("usage") or {}
    det = usage.get("prompt_tokens_details") or {}
    if numeric(det.get("cached_tokens")):
        out["cached_tokens"] = det["cached_tokens"]
    if timings == "llamacpp":
        t = engine.get("timings") or {}
        pn, pms = t.get("predicted_n"), t.get("predicted_ms")
        out["draft_n"], out["draft_accepted"] = t.get("draft_n"), t.get("draft_n_accepted")
        steps = pn - (out["draft_accepted"] or 0) if numeric(pn) else None
        out["step_ms"] = pms / steps if numeric(pms) and steps and steps > 0 else None
        if numeric(t.get("cache_n")):
            out["cached_tokens"] = t["cache_n"]
        if numeric(t.get("prompt_n")):
            out["prompt_tokens"] = t["prompt_n"] + (t.get("cache_n") or 0)
        if numeric(pn):
            out["completion_tokens"] = pn
    elif isinstance(timings, dict) and "regex" in timings:
        extra = {}
        for key, pat in timings["regex"].items():
            vals = []
            for m in re.finditer(pat, log_slice or "", re.M):
                try:
                    vals.append(float(m.group(1)))
                except (IndexError, TypeError, ValueError):
                    pass
            if vals:
                v = statistics.median(vals) if key == "step_ms" else sum(vals)
                if key in ("step_ms", "draft_n", "draft_accepted"):
                    out[key] = v
                else:
                    extra[key] = v
        if extra:
            engine["regex"] = extra
    return out


class Client:
    def __init__(self, cfg, run_id=None, no_progress_s=None):
        self.cfg = cfg
        self.base = (cfg.get("base_url") or "http://127.0.0.1:8000").rstrip("/")
        self.driver = cfg.get("driver", "http")
        if self.driver not in ("http", "cli") or (self.driver == "cli" and not cfg.get("cli")):
            raise ValueError('driver must be "http" or "cli" (with a "cli" command)')
        self.run_id = run_id or os.environ.get("BENCH_RUN_ID")
        self.no_progress_s = float(no_progress_s or cfg.get("no_progress_s") or 600)
        self.timings = cfg.get("timings", "openai")
        self.engine_log = cfg.get("engine_log")
        self.env = dict(os.environ, **{k: str(v) for k, v in (cfg.get("env") or {}).items()})
        tl = cfg.get("token_log")
        self.top_logprobs = int(tl.get("top_logprobs", 0)) if isinstance(tl, dict) else None

    def healthy(self):
        if self.cfg.get("health"):
            try:
                return subprocess.run(self.cfg["health"], capture_output=True, timeout=30, env=self.env).returncode == 0
            except (OSError, subprocess.TimeoutExpired):
                return False
        if self.driver == "cli":
            try:
                self.chat("Say hello.", 1, kind="warmup", prompt_id="health")
                return True
            except Exception:
                return False
        return bool(self.models())

    def models(self):
        if self.driver != "http":
            return []
        try:
            with urllib.request.urlopen(self.base + "/v1/models", timeout=5) as r:
                return [m.get("id") for m in json.loads(r.read() or b"{}").get("data") or []]
        except Exception:
            return []

    def log_offset(self):
        try:
            return os.path.getsize(self.engine_log) if self.engine_log else None
        except OSError:
            return None

    def log_slice(self, off):
        if off is None:
            return ""
        try:
            with open(self.engine_log, "rb") as f:
                f.seek(off)
                return f.read(8 << 20).decode("utf-8", "replace")
        except OSError:
            return ""

    def chat(self, messages, max_tokens, temperature=None, seed=None, extra=None, kind="test", prompt_id=None,
             pass_=0, batch=1, cache="cold"):
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        temp = self.cfg.get("temperature", 0.6) if temperature is None else temperature
        body_extra = _merge(self.cfg.get("extra_body") or {}, extra or {})
        off0 = self.log_offset()
        t_start, m0 = now_iso(ms=True), time.monotonic()
        r = (self._cli if self.driver == "cli" else self._http)(messages, max_tokens, temp, seed, body_extra)
        m1, t_end = time.monotonic(), now_iso(ms=True)
        engine = r.get("engine") or {}
        a = adapt(self.timings, engine, self.log_slice(off0) if isinstance(self.timings, dict) else "")
        pt = r.get("prompt_tokens") if numeric(r.get("prompt_tokens")) else a.get("prompt_tokens")
        ct = r.get("completion_tokens") if numeric(r.get("completion_tokens")) else a.get("completion_tokens")
        dm = r.get("decode_ms")
        text = r.get("text") or ""
        row = {"run_id": self.run_id, "pass": pass_, "kind": kind, "prompt_id": prompt_id,
               "prompt_sha": sha12(json.dumps(messages, sort_keys=True)), "seed": seed,
               "prompt_tokens": pt, "completion_tokens": ct, "cached_tokens": a.get("cached_tokens"),
               "ttft_ms": round(r["ttft_ms"], 2) if numeric(r.get("ttft_ms")) else None,
               "decode_ms": round(dm, 2) if numeric(dm) else None,
               "decode_tps": round((ct - 1) / (dm / 1000), 3) if numeric(ct) and ct > 1 and numeric(dm) and dm > 0 else None,
               "step_ms": round(a["step_ms"], 4) if numeric(a.get("step_ms")) else None,
               "draft_n": a.get("draft_n"), "draft_accepted": a.get("draft_accepted"),
               "finish_reason": r.get("finish_reason"), "output_sha12": sha12(text), "loop": looping(text),
               "t_start": t_start, "t_end": t_end,
               "path": {"batch": batch, "chunk": self.cfg.get("chunk"), "cache": cache},
               "engine": engine, "text": text, "_mono": (m0, m1)}
        if r.get("tokens"):
            row["tokens"] = r["tokens"]
        return row

    def _http(self, messages, max_tokens, temp, seed, extra):
        body = {"model": self.cfg.get("model"), "messages": messages, "max_tokens": max_tokens, "stream": True,
                "stream_options": {"include_usage": True}, "temperature": temp}
        if seed is not None:
            body["seed"] = seed
        if self.top_logprobs is not None:
            body["logprobs"] = True
            if self.top_logprobs:
                body["top_logprobs"] = self.top_logprobs
        body.update(extra)
        req = urllib.request.Request(self.base + "/v1/chat/completions", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        t0, t_first, text, usage, timings, finish, toks = time.monotonic(), None, [], {}, None, None, []
        try:
            with urllib.request.urlopen(req, timeout=self.no_progress_s) as r:
                for raw in r:
                    line = raw.decode("utf-8", "replace").strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    ev = json.loads(data)
                    if ev.get("usage"):
                        usage = ev["usage"]
                    if ev.get("timings"):
                        timings = ev["timings"]
                    for ch in ev.get("choices") or []:
                        if ch.get("finish_reason"):
                            finish = ch["finish_reason"]
                        d = ch.get("delta") or {}
                        piece = (d.get("content") or "") + (d.get("reasoning_content") or d.get("reasoning") or "")
                        if piece:
                            if t_first is None:
                                t_first = time.monotonic()
                            text.append(piece)
                        for t in (ch.get("logprobs") or {}).get("content") or []:
                            toks.append([t.get("token"), t.get("logprob"),
                                         [[x.get("token"), x.get("logprob")] for x in t.get("top_logprobs") or []]])
        except (socket.timeout, TimeoutError) as e:
            raise NoProgress(f"no bytes for {self.no_progress_s:.0f} s") from e
        except urllib.error.URLError as e:
            if isinstance(e.reason, (socket.timeout, TimeoutError)):
                raise NoProgress(f"no response for {self.no_progress_s:.0f} s") from e
            raise
        t_end = time.monotonic()
        if t_first is None:
            t_first = t_end
        engine = {"usage": usage}
        if timings is not None:
            engine["timings"] = timings
        return {"text": "".join(text), "ttft_ms": (t_first - t0) * 1000, "decode_ms": (t_end - t_first) * 1000,
                "prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens"),
                "finish_reason": finish, "engine": engine, "tokens": toks}

    def _cli(self, messages, max_tokens, temp, seed, extra):
        if self.top_logprobs is not None:
            extra = dict(extra, logprobs=True, **({"top_logprobs": self.top_logprobs} if self.top_logprobs else {}))
        req = {"messages": messages, "max_tokens": max_tokens, "temperature": temp, "seed": seed, "extra": extra}
        try:
            p = subprocess.run(self.cfg["cli"], input=json.dumps(req), capture_output=True, text=True, env=self.env,
                               timeout=self.no_progress_s)
        except subprocess.TimeoutExpired as e:
            raise NoProgress(f"cli driver gave no result in {self.no_progress_s:.0f} s") from e
        if p.returncode != 0:
            raise RuntimeError(f"cli driver rc={p.returncode}: {p.stderr.strip()[-400:]}")
        try:
            out = json.loads(p.stdout)
        except ValueError as e:
            raise RuntimeError(f"cli driver printed no JSON object: {p.stdout.strip()[-200:]!r}") from e
        out.setdefault("engine", {})
        out["tokens"] = out["engine"].get("logprobs")
        return out


def on_ac():
    try:
        if sys.platform == "darwin":
            return "AC Power" in subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True).stdout
        import glob
        vals = [open(p).read().strip() for p in glob.glob("/sys/class/power_supply/*/online")]
        return not vals or "1" in vals
    except Exception:
        return True


def read_pid(path):
    try:
        with open(path) as f:
            return int(f.read().split()[0])
    except (OSError, ValueError, IndexError):
        return None


def kill_pid(pid, timeout_s=60):
    try:
        group = os.getpgid(pid) == pid and pid != os.getpgrp()
    except OSError:
        return

    def send(sig):
        (os.killpg if group else os.kill)(pid, sig)
    try:
        send(signal.SIGTERM)
    except OSError:
        return
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except OSError:
            return
        time.sleep(0.5)
    try:
        send(signal.SIGKILL)
    except OSError:
        pass


def container_name(cfg):
    if cfg.get("container"):
        return cfg["container"]
    launch = [str(x) for x in cfg.get("launch") or []]
    if launch[:1] != ["docker"] and launch[:1] != ["podman"]:
        return None
    for i, x in enumerate(launch):
        if x == "--name" and i + 1 < len(launch):
            return launch[i + 1]
        if x.startswith("--name="):
            return x.split("=", 1)[1]
    return None


def server_pids(cfg, env):
    pids = []
    pid = read_pid(cfg["pidfile"]) if cfg.get("pidfile") else None
    if pid:
        pids.append(pid)
    name = container_name(cfg)
    if name:
        tool = "podman" if (cfg.get("launch") or [""])[0] == "podman" else "docker"
        try:
            p = subprocess.run([tool, "top", name, "-eo", "pid"], capture_output=True, text=True, timeout=30, env=env)
            pids += [int(x) for x in p.stdout.split() if x.isdigit()] if p.returncode == 0 else []
        except (OSError, subprocess.TimeoutExpired):
            pass
    return sorted(set(pids))


def file_identity(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        st = os.stat(path)
        return {"path": path, "sha256": h.hexdigest(), "size": st.st_size,
                "mtime": datetime.datetime.fromtimestamp(st.st_mtime).astimezone().isoformat(timespec="seconds")}
    except OSError as e:
        return {"path": path, "error": repr(e)}


def repo_identity(path):
    def git(*a):
        p = subprocess.run(["git", "-C", path, *a], capture_output=True, text=True, timeout=60)
        return p.stdout if p.returncode == 0 else None
    try:
        head, diff = git("rev-parse", "HEAD"), git("diff", "HEAD")
        return {"path": path, "commit": head and head.strip(), "dirty": bool(diff),
                "diff_sha12": sha12(diff) if diff else None}
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"path": path, "error": repr(e)}


def state_changes(a, b):
    if not a or not b:
        return []
    before = {g.get("index"): g for g in a.get("gpus") or []}
    out = []
    for g in b.get("gpus") or []:
        o = before.get(g.get("index"))
        for k in ("power_limit_w", "persistence"):
            if o and o.get(k) is not None and g.get(k) is not None and o[k] != g[k]:
                out.append(f"gpu{g.get('index')} {k} {o[k]} -> {g[k]}")
    return out


def import_rig():
    try:
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        import rig
        return rig, None
    except Exception as e:
        return None, repr(e)


class MemWatch(threading.Thread):
    def __init__(self, mcfg, pidfile, env, on_trip):
        super().__init__(daemon=True)
        self.mcfg, self.pidfile, self.env, self.on_trip = mcfg, pidfile, env, on_trip
        self.peak, self.tripped, self.probe_failed, self.server_up, self.stop = 0, False, False, False, threading.Event()

    def cmd(self):
        cmd = [str(x) for x in self.mcfg["probe"]]
        if any("{pid}" in x for x in cmd):
            pid = read_pid(self.pidfile) if self.pidfile else None
            if not pid:
                return None
            cmd = [x.replace("{pid}", str(pid)) for x in cmd]
        return cmd

    def run(self):
        cap = self.mcfg.get("cap_gib", 1e9) * 2**30
        while not self.stop.wait(self.mcfg.get("interval_s", 3)):
            cmd = self.cmd()
            try:
                if cmd is None:
                    raise OSError("no PID in the pidfile for {pid}")
                p = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=self.env)
                rc, out, err = p.returncode, p.stdout.strip(), p.stderr.strip()
            except Exception as e:
                rc, out, err = None, "", repr(e)
            if rc != 0 or not out.isdigit():
                if self.server_up and not self.probe_failed:
                    self.probe_failed = True
                    log(f"MEMORY PROBE FAILED (rc={rc}, stdout={out[:80]!r}, stderr={err[:300]!r}); "
                        "the memory cap is not enforced while it fails")
                continue
            b = int(out)
            self.peak = max(self.peak, b)
            if b > cap and not self.tripped:
                self.tripped = True
                log(f"MEMORY CAP EXCEEDED: {b / 2**30:.1f} GiB > {cap / 2**30:.1f} GiB")
                self.on_trip()


def filler(n_words, rng):
    return " ".join(rng.choice(WORDS) for _ in range(max(1, n_words)))


class Bench:
    def __init__(self, cfg, rig_path, samplers):
        self.cfg, self.name, self.t0 = cfg, cfg["name"], time.monotonic()
        stamp = f"{self.name}-{time.strftime('%Y%m%dT%H%M%S', time.gmtime())}"
        self.dir, k = os.path.join("runs", stamp), 1
        while os.path.exists(self.dir):
            k += 1
            self.dir = os.path.join("runs", f"{stamp}-{k}")
        self.run_id = os.path.basename(self.dir)
        os.makedirs(self.dir)
        self.cfg_path = os.path.abspath(os.path.join(self.dir, "config.resolved.json"))
        with open(self.cfg_path, "w") as f:
            json.dump(cfg, f, indent=1, sort_keys=True)
        self.flags, self.na = [], []
        self.res = {"schema": 2, "run_id": self.run_id, "run_dir": self.dir, "name": self.name,
                    "config_hash": config_hash(cfg), "time": now_iso(), "ok": False, "flags": self.flags,
                    "not_available": self.na, "passes": 0, "metrics": {}, "metrics_passes": {}, "per_prompt": {},
                    "deterministic": None, "identity": {}, "state_start": None, "state_end": None, "phases": {},
                    "tests": {}, "proof": None, "startup_s": None, "mem_peak_gib": None, "host_ram_min_gib": None,
                    "reused_server": False, "claims": cfg.get("claims")}
        self.rigmod, err = import_rig()
        self.rig = {}
        if self.rigmod:
            try:
                self.rig = self.rigmod.load(rig_path) or {}
            except Exception as e:
                self.na.append(f"rig.load ({e!r})")
                self.rig = read_json(rig_path, {}) or {}
        else:
            self.na.append(f"rig.py ({err})")
            self.rig = read_json(rig_path, {}) or {}
        self.noise = rig_noise(self.rig)
        nps = cfg.get("no_progress_s") or (self.rig.get("watchdog") or {}).get("no_progress_s") or 600
        self.client = Client(cfg, run_id=self.run_id, no_progress_s=nps)
        self.samplers, self.sampler, self.watch = samplers, None, None
        self.floor_hit = threading.Event()
        self.seed, self.pass_offset, self.tpw, self.tok_any = cfg.get("seed", 1), 0, 1.6, False
        self.bypass = None
        self.allow_pids = []

    def path(self, *p):
        return os.path.join(self.dir, *p)

    def event(self, event, **kw):
        append_jsonl(self.path("events.jsonl"), {"t": now_iso(ms=True), "event": event, **kw})

    def flag(self, f, why=""):
        if f not in self.flags:
            self.flags.append(f)
            self.event("flag", flag=f, why=why)

    def phase(self, name):
        log("phase", name)
        self.event("phase", name=name)
        if self.sampler:
            try:
                self.sampler.phase(name)
            except Exception:
                pass

    def prefix(self, p, pid):
        return f"[run-seed {self.seed} pass {p + self.pass_offset} prompt {pid}] "

    def add_pass(self, metric, v):
        if numeric(v):
            self.res["metrics_passes"].setdefault(metric, []).append(round(v, 4))

    def add_prompt(self, pid, **fields):
        d = self.res["per_prompt"].setdefault(pid, {})
        for k, v in fields.items():
            d.setdefault(k, []).append(v)

    def stop_server(self):
        if self.cfg.get("stop"):
            subprocess.run(self.cfg["stop"], capture_output=True, env=self.client.env)
        elif self.cfg.get("pidfile"):
            pid = read_pid(self.cfg["pidfile"])
            if pid:
                kill_pid(pid, self.cfg.get("stop_timeout_s", 60))
            try:
                os.remove(self.cfg["pidfile"])
            except OSError:
                pass
        self.event("stop")

    def check_level(self, name):
        return ((self.rig.get("checks") or {}).get(name) or {}).get("level", "block")

    def on_floor(self, *_):
        if self.floor_hit.is_set():
            return
        if self.check_level("host_ram_floor") != "block":
            log("HOST RAM FLOOR: under the floor (rig.json level is not block: server left running)")
            self.event("watchdog", what="host RAM under the floor", action="none")
            return
        self.floor_hit.set()
        log("HOST RAM FLOOR: stopping the server")
        self.flag("HOST_FLOOR", "host RAM under the floor")
        self.stop_server()

    def on_memcap(self):
        self.event("watchdog", what="memory cap")
        self.stop_server()

    def flush_cache(self):
        fc = (self.rig.get("cache_bypass") or {}).get("flush_cmd")
        fc = shlex.split(fc) if isinstance(fc, str) else fc
        r = self.run_cmd_check(fc) if fc else {"status": "fail", "detail": "flush_cmd not set"}
        if r["status"] != "pass":
            raise RuntimeError(f"cache flush_cmd failed: {r['detail'][:200]}")

    def req(self, kind, pid, text, max_tokens, p, prefix=True, **kw):
        if self.floor_hit.is_set() or (self.watch and self.watch.tripped):
            raise Abort("watchdog stopped the run")
        if self.bypass and kind != "warmup" and kw.get("cache") != "bypass":
            kw["cache"] = "bypass"
            if self.bypass == "request_field":
                kw["extra"] = _merge(kw.get("extra") or {}, (self.rig.get("cache_bypass") or {}).get("request_field") or {})
            else:
                self.flush_cache()
        msgs = [{"role": "user", "content": (self.prefix(p, pid) if prefix else "") + text}]
        row = self.client.chat(msgs, max_tokens, kind=kind, prompt_id=pid, pass_=p, **kw)
        text_out, toks, mono = row.pop("text"), row.pop("tokens", None), row.pop("_mono")
        append_jsonl(self.path("requests.jsonl"), row)
        if toks:
            self.tok_any = True
            head = {"run_id": self.run_id, "pass": p, "kind": kind, "prompt_id": pid}
            lines = "".join(json.dumps(dict(head, pos=i, token=t[0], logprob=t[1], top=t[2]) if isinstance(t, list)
                                       and len(t) == 3 else dict(head, pos=i, raw=t)) + "\n" for i, t in enumerate(toks))
            with _LOCK, open(self.path("tokens.jsonl"), "a") as f:
                f.write(lines)
        if row["loop"]:
            self.flag("LOOP", pid)
        row["text"], row["_mono"] = text_out, mono
        return row

    def hook_env(self, p, test_name):
        off = self.client.log_offset()
        return dict(self.client.env, BENCH_BASE_URL=self.client.base, BENCH_MODEL=str(self.cfg.get("model", "")),
                    BENCH_RUN=self.name, BENCH_RUN_ID=self.run_id, BENCH_RUN_DIR=os.path.abspath(self.dir),
                    BENCH_CONFIG=self.cfg_path, BENCH_PASS=str(p),
                    BENCH_ENGINE_LOG=os.path.abspath(self.cfg["engine_log"]) if self.cfg.get("engine_log") else "",
                    BENCH_LOG_OFFSET="" if off is None else str(off), BENCH_TEST_NAME=test_name)

    def state(self):
        if not self.rigmod:
            return None
        try:
            return self.rigmod.state(self.rig)
        except Exception as e:
            if not any(x.startswith("rig.state") for x in self.na):
                self.na.append(f"rig.state ({e!r})")
            return None

    def preflight(self, own_server_up):
        cfg, results, blocked = self.cfg, [], []
        if self.rigmod:
            try:
                try:
                    results = self.rigmod.preflight(self.rig, cards=cfg.get("cards"), allow_pids=self.allow_pids or None)
                except TypeError:
                    results = self.rigmod.preflight(self.rig, cards=cfg.get("cards"))
                if own_server_up and not self.allow_pids:
                    for r in results:
                        if r.get("check") == "cards_idle" and r.get("status") == "fail":
                            r.update(status="na", detail="own server running, PIDs unknown: " + str(r.get("detail")))
                blocked = list(self.rigmod.blocking(results))
            except Exception as e:
                self.na.append(f"rig.preflight ({e!r})")
            for r in results:
                if r.get("status") == "na":
                    self.na.append(f"check:{r.get('check')}")
        for cmd in cfg.get("preflight") or []:
            r = self.run_cmd_check(cmd)
            results.append(r)
            if r["status"] == "fail":
                blocked.append(r)
        self.res["preflight"] = results
        if blocked:
            why = "; ".join(f"{r.get('check')}: {r.get('detail')}" for r in blocked)
            log("RIG_BLOCK:", why)
            self.flag("RIG_BLOCK", why)
            self.res["error"] = "preflight blocked: " + why
            return False
        return True

    def run_cmd_check(self, cmd):
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=self.client.env)
            ok, detail = p.returncode == 0, f"rc={p.returncode} {(p.stdout + p.stderr).strip()[-200:]}"
        except (OSError, subprocess.TimeoutExpired) as e:
            ok, detail = False, repr(e)
        return {"check": "preflight:" + " ".join(map(str, cmd))[:60], "status": "pass" if ok else "fail",
                "level": "block", "detail": detail}

    def write_identity(self, models=None):
        ic = self.cfg.get("identity") or {}
        ident = self.res["identity"] or {
            "run_id": self.run_id, "name": self.name, "config_hash": self.res["config_hash"], "time": self.res["time"],
            "host": platform.node(), "platform": platform.platform(), "python": platform.python_version(),
            "bench_sha12": (file_identity(os.path.abspath(__file__)).get("sha256") or "")[:12],
            "rig_source": self.rig.get("_source", "rig.json") if self.rig else None,
            "rig_sha12": sha12(json.dumps(self.rig, sort_keys=True, default=str)) if self.rig else None}
        if ic.get("binary") and "binary" not in ident:
            ident["binary"] = file_identity(ic["binary"])
        if ic.get("repo") and "repo" not in ident:
            ident["repo"] = repo_identity(ic["repo"])
        if models is not None:
            ident["server_models"] = models
        self.res["identity"] = ident
        with open(self.path("identity.json"), "w") as f:
            json.dump(ident, f, indent=1)

    def start_watchers(self):
        if not self.samplers:
            self.na += ["samplers (--no-samplers)", "host_floor_watchdog (--no-samplers)"]
        elif not self.rigmod:
            self.na += ["samplers", "host_floor_watchdog"]
        else:
            try:
                self.sampler = self.rigmod.Sampler(self.rig, self.path("samples.jsonl"), interval_s=1.0,
                                                   on_floor=self.on_floor)
                self.sampler.start()
            except Exception as e:
                self.sampler = None
                self.na += [f"samplers ({e!r})", "host_floor_watchdog"]
        if (self.cfg.get("memory") or {}).get("probe"):
            self.watch = MemWatch(self.cfg["memory"], self.cfg.get("pidfile"), self.client.env, self.on_memcap)
            self.watch.start()

    def run(self, passes, long_ctx, skip_cn, reps, reuse, determinism):
        cfg, res = self.cfg, self.res
        log("run", self.run_id, "->", self.dir)
        self.event("start", passes=passes, config_hash=res["config_hash"])
        if not self.rigmod and self.check_level("on_ac") == "block" and not on_ac():
            self.flag("ON_BATTERY")
            self.flag("RIG_BLOCK", "on battery (rig.json checks.on_ac level block)")
            res["error"] = "refusing to run on battery (rig.json checks.on_ac level block)"
            return self.finish()
        state = {"launch": cfg.get("launch"), "base_url": self.client.base, "env": cfg.get("env")}
        prev = read_json(SERVER_STATE, {}) or {}
        same_server = {k: prev.get(k) for k in state} == state
        reusing = bool(cfg.get("launch") and reuse and same_server and self.client.healthy())
        launching = bool(cfg.get("launch")) and not reusing
        if launching:
            if os.path.exists(SERVER_STATE):
                os.remove(SERVER_STATE)
            self.stop_server()
        else:
            mode = (self.rig.get("cache_bypass") or {}).get("mode")
            if mode in ("request_field", "flush_cmd"):
                self.bypass = mode
            else:
                self.pass_offset = prev.get("passes_used", 0) if same_server else 0
            res["cache_bypass"] = self.bypass
            res["prefix_pass_offset"] = self.pass_offset
            self.allow_pids = [int(x) for x in prev.get("pids") or []] if same_server else []
            self.allow_pids = self.allow_pids or server_pids(cfg, self.client.env)
            res["reused_server"] = reusing
        if not self.preflight(own_server_up=not launching):
            return self.finish()
        self.write_identity()
        self.start_watchers()
        try:
            if launching:
                self.phase("startup")
                t0 = time.monotonic()
                self.event("launch", argv=cfg["launch"])
                subprocess.run(cfg["launch"], check=True, capture_output=True, env=self.client.env)
                deadline = t0 + cfg.get("health_timeout_s", 900)
                while not self.client.healthy():
                    if time.monotonic() > deadline or self.floor_hit.is_set() or (self.watch and self.watch.tripped):
                        res["error"] = "server did not become healthy"
                        raise Abort(res["error"])
                    time.sleep(1)
                res["startup_s"] = round(time.monotonic() - t0, 1)
                log("healthy after", res["startup_s"], "s")
                self.event("healthy", startup_s=res["startup_s"])
            elif not self.client.healthy():
                res["error"] = "server not reachable" + ("" if cfg.get("launch") else " and no launch command given")
                raise Abort(res["error"])
            else:
                log("reusing running server" if reusing else "attached to running server")
            self.allow_pids = server_pids(cfg, self.client.env) or self.allow_pids
            self.save_server_state(state, self.pass_offset)
            if self.watch:
                self.watch.server_up = True
            self.write_identity(self.client.models())
            res["state_start"] = self.state()
            self.timed(passes, long_ctx, skip_cn, reps, determinism)
            self.save_server_state(state, self.pass_offset + passes)
            res["ok"] = True
        except Abort as e:
            res.setdefault("error", str(e))
        except NoProgress as e:
            log("NO PROGRESS:", e)
            self.flag("NO_PROGRESS", str(e))
            res["error"] = repr(e)
            self.stop_server()
        except Exception as e:
            res["error"] = repr(e)
            if not self.floor_hit.is_set() and not (self.watch and self.watch.tripped):
                self.flag("REQ_FAIL", repr(e)[:200])
        res["state_end"] = self.state()
        for cmd in cfg.get("preflight") or []:
            r = self.run_cmd_check(cmd)
            if r["status"] == "fail":
                res["ok"] = False
                res["error"] = (res.get("error", "") + f"; preflight command failed at the end: {r['detail']}").lstrip("; ")
                self.event("preflight_end_fail", **r)
        return self.finish()

    def save_server_state(self, state, used):
        with open(SERVER_STATE, "w") as f:
            json.dump({**state, "passes_used": used, "pids": self.allow_pids}, f)

    def timed(self, passes, long_ctx, skip_cn, reps, determinism):
        cfg = self.cfg
        self.phase("warmup")
        self.req("warmup", "warmup", "Say hello.", 16, 0, prefix=False)
        self.calibrate()
        n = int(cfg.get("concurrency", 4))
        for p in range(passes):
            log(f"pass {p + 1}/{passes}")
            self.phase("ttft")
            r = self.req("ttft", "ttft", "Reply with the single word: ready", 8, p)
            self.add_pass("ttft_short_ms", r["ttft_ms"])
            self.add_prompt("ttft", ttft_ms=r["ttft_ms"], prompt_sha=r["prompt_sha"])

            self.phase("c1")
            dec, steps, acc = [], [], []
            for i in range(reps):
                pid = f"c1-{i}"
                r = self.req("c1", pid, PROMPTS[i % len(PROMPTS)], 512, p)
                ct, da = r["completion_tokens"], r["draft_accepted"]
                al = ct / (ct - da) if numeric(ct) and numeric(da) and ct > da >= 0 else None
                self.add_prompt(pid, decode_tps=r["decode_tps"], step_ms=r["step_ms"], accept_len=al,
                                completion_tokens=ct, decode_ms=r["decode_ms"], ttft_ms=r["ttft_ms"],
                                prompt_sha=r["prompt_sha"])
                for lst, v in ((dec, r["decode_tps"]), (steps, r["step_ms"]), (acc, al)):
                    if numeric(v):
                        lst.append(v)
            for m, lst in (("c1_decode", dec), ("step_ms", steps), ("accept_len", acc)):
                if lst:
                    self.add_pass(m, statistics.median(lst))
            log("c1 decode", [round(x, 2) for x in dec])

            if n > 1 and not skip_cn:
                self.phase("cN")
                with ThreadPoolExecutor(n) as ex:
                    rs = list(ex.map(lambda j: self.req("cN", f"cN-{j}", PROMPTS[j % len(PROMPTS)], 512, p, batch=n),
                                     range(n)))
                toks = sum(x["completion_tokens"] or 0 for x in rs)
                wall = max(x["_mono"][1] for x in rs) - min(x["_mono"][0] for x in rs)
                self.add_pass(f"c{n}_aggregate", toks / wall if wall > 0 else None)
                log(f"c{n} aggregate", round(toks / wall, 2) if wall > 0 else None)

            self.phase("prefill")
            for L in cfg.get("prefill_lengths", [4096, 32768]):
                pid = f"prefill-{L}"
                prompt, _ = self.document(L, p, pid)
                r = self.req("prefill", pid, prompt, 1, p, prefix=False, temperature=0.0)
                pt, tt = r["prompt_tokens"], r["ttft_ms"]
                v = pt / (tt / 1000) if numeric(pt) and numeric(tt) and tt > 0 else None
                self.add_pass(f"prefill_{L}", v)
                self.add_prompt(pid, prefill_tps=v, prompt_tokens=pt, ttft_ms=tt, prompt_sha=r["prompt_sha"])
                self.res.setdefault("prefill_tokens", {})[str(L)] = pt
                log(f"prefill ~{L}", v and round(v, 1), "tok/s over", pt, "tokens")

            self.tests(p)
            self.res["passes"] = p + 1

        if long_ctx:
            self.phase("long")
        for L in long_ctx:
            pid = f"long-{L}"
            prompt, codes = self.document(L, 0, pid)
            r = self.req("long", pid, prompt, 256, 0, prefix=False, temperature=0.0)
            hits = sum(c in r["text"] for c in codes)
            pt, tt = r["prompt_tokens"], r["ttft_ms"]
            self.res.setdefault("long", {})[str(L)] = {
                "prompt_tokens": pt, "ttft_s": tt and round(tt / 1000, 1),
                "prefill": round(pt / (tt / 1000), 1) if numeric(pt) and tt else None,
                "decode": r["decode_tps"], "retrieval": f"{hits}/{len(codes)}"}
            if hits < len(codes):
                self.flag("NEEDLE_MISS", pid)
            log(f"long ~{L}", self.res["long"][str(L)])

        if determinism:
            self.phase("determinism")
            self.determinism(passes)
        self.proof(passes)

    def calibrate(self):
        pts = []
        for k, nw in ((1, 400), (2, 2400)):
            pid = f"calib-{k}"
            rng = random.Random(f"{self.seed}-{self.pass_offset}-{pid}")
            r = self.req("warmup", pid, filler(nw, rng), 1, 0, temperature=0.0)
            pts.append(r["prompt_tokens"])
        if all(numeric(x) for x in pts) and pts[1] > pts[0]:
            self.tpw = (pts[1] - pts[0]) / 2000
        else:
            self.na.append("tokens_per_word (no prompt_tokens in usage; using 1.6)")
        self.res["tokens_per_word"] = round(self.tpw, 4)
        log("tokens per word", self.res["tokens_per_word"])

    def document(self, tokens, p, pid, needles=3):
        rng = random.Random(f"{self.seed}-{p + self.pass_offset}-{pid}")
        n_words = int(tokens / self.tpw)
        words = [rng.choice(WORDS) for _ in range(n_words)]
        codes = ["".join(rng.choices(string.ascii_uppercase + string.digits, k=8)) for _ in range(needles)]
        for i, c in enumerate(codes):
            words.insert(int(n_words * (i + 1) / (needles + 1)), f". The secret code number {i + 1} is {c}. ")
        q = ("\n\nList every secret code number and its value that appears in the document above. "
             "Answer only with the codes.")
        return self.prefix(p, pid) + " ".join(words) + q, codes

    def tests(self, p):
        tests = [t for t in self.cfg.get("tests") or [] if not (t.get("once") and p > 0)]
        if tests:
            self.phase("tests")
        for t in tests:
            name = t["name"]
            tdir = self.path("tests", name)
            os.makedirs(tdir, exist_ok=True)
            env = self.hook_env(p, name)
            self.event("test_start", name=name, pass_=p, log_offset=env["BENCH_LOG_OFFSET"])
            try:
                pr = subprocess.run(t["cmd"], capture_output=True, text=True, env=env, timeout=t.get("timeout_s", 1800))
                rc, out = pr.returncode, pr.stdout + pr.stderr
            except (OSError, subprocess.TimeoutExpired) as e:
                rc, out = None, repr(e)
            with open(os.path.join(tdir, f"log.pass{p}.txt"), "w") as f:
                f.write(out)
            d = self.res["tests"].setdefault(name, {"rcs": []})
            d["rcs"].append(rc)
            d["rc"] = next((x for x in d["rcs"] if x != 0), 0)
            d["out"] = out[-600:]
            if rc != 0:
                self.flag("TEST_FAIL", name)
            mpath = os.path.join(tdir, "metrics.json")
            m = read_json(mpath)
            if isinstance(m, dict):
                for k, v in m.items():
                    self.add_pass(f"{name}.{k}", v)
                os.replace(mpath, os.path.join(tdir, f"metrics.pass{p}.json"))
            log(f"test {name} pass {p} rc", rc)

    def determinism(self, passes):
        cb = self.rig.get("cache_bypass") or {}
        mode = cb.get("mode", "none")
        info = {"mode": mode}
        self.res["determinism"] = info
        if mode == "reload":
            log("cache_bypass mode is reload: run the control config twice in separate loads, then compare the "
                "greedy answers with `python3 scripts/quality.py l0 runs/A runs/B`; deterministic stays null")
            return
        if mode not in ("request_field", "flush_cmd"):
            self.na.append("determinism (rig.json cache_bypass mode none)")
            return
        same = 0
        for i, text in enumerate(PROMPTS):
            pid, shas = f"det-{i}", []
            for _ in range(2):
                extra = None
                if mode == "request_field":
                    extra = dict(cb.get("request_field") or {})
                else:
                    fc = cb.get("flush_cmd")
                    fc = shlex.split(fc) if isinstance(fc, str) else fc
                    r = self.run_cmd_check(fc) if fc else {"status": "fail", "detail": "flush_cmd not set"}
                    if r["status"] != "pass":
                        self.na.append(f"determinism (flush_cmd failed: {r['detail'][:120]})")
                        return
                r = self.req("determinism", pid, text, 256, passes, temperature=0.0, seed=self.seed, extra=extra,
                             cache="bypass")
                shas.append(r["output_sha12"])
            same += shas[0] == shas[1]
        total = len(PROMPTS)
        self.res["deterministic"] = same == total
        info.update(same=same, total=total)
        if same != total:
            info["why"] = (f"{total - same}/{total} panel prompts gave different greedy answers twice with cache "
                           f"bypass ({mode}): answer identity is not available on this rig+engine; use quality.py "
                           "teacher-forced logit checks for bit claims")
        log("deterministic", self.res["deterministic"], f"{same}/{total}")

    def proof(self, passes):
        if not self.cfg.get("proof"):
            return
        self.phase("proof")
        try:
            p = subprocess.run(self.cfg["proof"], capture_output=True, text=True, env=self.hook_env(passes - 1, "proof"),
                               timeout=self.cfg.get("proof_timeout_s", 300))
            rc, out = p.returncode, p.stdout + p.stderr
        except (OSError, subprocess.TimeoutExpired) as e:
            rc, out = None, repr(e)
        with open(self.path("proof.txt"), "w") as f:
            f.write(out)
        self.res["proof"] = {"rc": rc, "out": out[-600:]}
        if rc != 0:
            self.flag("NO_PROOF")
        log("proof rc", rc)

    def finish(self):
        res, n = self.res, self.noise
        if self.watch:
            self.watch.stop.set()
            res["mem_peak_gib"] = round(self.watch.peak / 2**30, 2)
            if self.watch.tripped:
                self.flag("MEM_CAP")
            if self.watch.probe_failed:
                self.flag("MEM_PROBE_FAIL")
        if self.sampler:
            try:
                s = self.sampler.stop() or {}
                res["phases"] = s.get("phases") or {}
                res["host_ram_min_gib"] = s.get("host_ram_min_gib")
                if s.get("host_busy"):
                    self.flag("HOST_BUSY")
            except Exception as e:
                self.na.append(f"samplers.stop ({e!r})")
        changes = state_changes(res["state_start"], res["state_end"])
        if changes:
            self.flag("STATE_CHANGED", "; ".join(changes))
            res["state_changes"] = changes
        if not on_ac():
            if self.check_level("on_ac") == "block":
                self.flag("ON_BATTERY")
            else:
                self.event("watchdog", what="on battery", action="none")
        metrics = {k: round(statistics.median(v), 3) for k, v in res["metrics_passes"].items() if v}
        c1 = [v for pid, d in res["per_prompt"].items() if pid.startswith("c1-") for v in d.get("decode_tps", [])
              if numeric(v)]
        if c1:
            metrics["c1_decode"] = round(statistics.median(c1), 2)
            cts = [v for pid, d in res["per_prompt"].items() if pid.startswith("c1-")
                   for v in d.get("completion_tokens", []) if numeric(v)]
            if len(c1) < n["min_samples"] or (cts and statistics.median(cts) < n["min_tokens"]):
                self.flag("LOW_N", f"{len(c1)} c1 samples, median {cts and statistics.median(cts)} tokens")
        res["metrics"] = metrics
        if self.cfg.get("token_log") and not self.tok_any and res["passes"]:
            self.na.append("token_log (server returned no logprobs)")
        if VOID_FLAGS & set(self.flags):
            res["ok"] = False
        res["flags"] = sorted(set(self.flags))
        res["not_available"] = sorted(set(self.na))
        res["dur_s"] = round(time.monotonic() - self.t0, 1)
        self.event("end", ok=res["ok"], flags=res["flags"])
        append_jsonl("ledger.jsonl", res)
        print(json.dumps({k: res.get(k) for k in ("name", "run_id", "run_dir", "ok", "error", "flags", "not_available",
                                                   "passes", "metrics", "deterministic", "tokens_per_word",
                                                   "startup_s", "mem_peak_gib", "host_ram_min_gib", "long", "tests",
                                                   "proof") if res.get(k) is not None}, indent=1))
        return res


def run(cfg_path, passes=None, long_ctx=(), skip_cn=False, reps=6, reuse=False, determinism=False, samplers=True,
        rig_path="rig.json"):
    cfg = load_config(cfg_path)
    passes = max(1, int(passes or cfg.get("passes", 1)))
    return Bench(cfg, rig_path, samplers).run(passes, long_ctx, skip_cn, reps, reuse, determinism)


def normalize(d):
    if d.get("schema", 1) >= 2:
        m = dict(d.get("metrics") or {})
        for k in ("mem_peak_gib", "startup_s"):
            if numeric(d.get(k)):
                m[k] = d[k]
        return {**d, "metrics": m, "metrics_passes": dict(d.get("metrics_passes") or {}),
                "per_prompt": d.get("per_prompt") or {}, "flags": d.get("flags") or []}
    m = {k: v for k, v in d.items() if numeric(v) and not k.endswith("_tokens")}
    return {**d, "schema": 1, "metrics": m, "metrics_passes": {"c1_decode": d["c1_all"]} if d.get("c1_all") else {},
            "per_prompt": {}, "config_hash": None, "passes": 1, "deterministic": None, "not_available": [],
            "flags": d.get("flags") or [], "run_dir": None}


def hard_flags(r):
    return set(r.get("flags") or []) - WATCH_FLAGS - REPEAT_FLAGS


def good(r):
    return bool(r.get("ok")) and not hard_flags(r)


def bare(m):
    return m.split(".")[-1]


def lower_better(m):
    b = bare(m)
    return m in LOWER_IS_BETTER or b in LOWER_IS_BETTER or b.endswith(("_ms", "_s", "_gib")) or "_ms_" in b


def row_time(r):
    try:
        return parse_time(r.get("time"))
    except (TypeError, ValueError):
        return None


def show(path="ledger.jsonl"):
    rows = [normalize(r) for r in read_jsonl(path)]
    if not rows:
        sys.exit(f"no rows in {path}")
    allm = {k for d in rows for k in d["metrics"]}
    agg = sorted(k for k in allm if re.match(r"c\d+_aggregate$", k))
    pre = sorted((k for k in allm if re.match(r"prefill_\d+$", k)), key=lambda k: int(k[8:]))
    keys = ["c1_decode", *agg, *pre, "step_ms", "accept_len", "ttft_short_ms", "startup_s", "mem_peak_gib"]
    keys = [k for k in keys if k in allm]
    print("name".ljust(24) + "pass".rjust(5) + "det".rjust(4) + "".join(k[:13].rjust(14) for k in keys) + "  flags")
    for d in rows:
        det = {True: "y", False: "n"}.get(d.get("deterministic"), "-")
        print(str(d.get("name"))[:24].ljust(24) + str(d.get("passes", "-")).rjust(5) + det.rjust(4)
              + "".join(str(d["metrics"].get(k, "-"))[:13].rjust(14) for k in keys)
              + "  " + ("" if d.get("ok") else "NOT-OK ") + ",".join(d["flags"]))


def noise_stats(rows, window):
    groups = {}
    for r in rows:
        if r.get("schema", 1) >= 2 and r.get("config_hash") and good(r):
            groups.setdefault(r["config_hash"], []).append(r)
    out = {}
    for h, rs in groups.items():
        rs = rs[-int(window):]
        mets = {}
        for m in sorted({k for r in rs for k in r["metrics_passes"]}):
            loads = [[v for v in r["metrics_passes"].get(m) or [] if numeric(v)] for r in rs]
            loads = [l for l in loads if l]
            if not loads:
                continue
            grand = statistics.fmean(v for l in loads for v in l)
            if not grand:
                continue
            multi = [l for l in loads if len(l) > 1]
            ss = sum(sum((v - statistics.fmean(l)) ** 2 for v in l) for l in multi)
            df = sum(len(l) - 1 for l in multi)
            means = [statistics.fmean(l) for l in loads]
            mets[m] = {"mean": grand, "sd_within_pct": 100 * math.sqrt(ss / df) / abs(grand) if df else None,
                       "df_within": df,
                       "sd_between_pct": 100 * statistics.stdev(means) / abs(grand) if len(means) > 1 else None,
                       "loads": len(loads), "passes_per_load": statistics.median(len(l) for l in loads)}
        out[h] = {"names": sorted({r["name"] for r in rs}), "rows": len(rs), "last": rs[-1].get("time"), "metrics": mets}
    return out


def bars(ns, l_ctl, l_cand, noise):
    k, floor = noise["k"], noise["floor_pct"]
    calibrated = bool(ns) and ns["loads"] >= noise["min_loads"] and (ns["df_within"] or 0) >= noise["min_df"] \
        and ns["sd_between_pct"] is not None
    if not calibrated:
        return {"calibrated": False, "bar_pct": FALLBACK["bar"], "trend_pct": FALLBACK["drift"], "sd_load_pct": None,
                "sd_within_pct": ns["sd_within_pct"] if ns else None, "t_scale": 1.0}
    sd_load, sdw = ns["sd_between_pct"], ns["sd_within_pct"]
    ts = t_scale(ns["loads"] - 1)
    return {"calibrated": True, "bar_pct": max(k * ts * sd_load * math.sqrt(1 / l_ctl + 1 / l_cand), floor),
            "sd_load_pct": sd_load, "sd_within_pct": sdw, "trend_pct": max(k * math.sqrt(2) * sdw, floor),
            "t_scale": ts}


PROMPT_SPEC = {"c1_decode": (r"c1-\d+$", "decode_tps"), "step_ms": (r"c1-\d+$", "step_ms"),
               "accept_len": (r"c1-\d+$", "accept_len"), "ttft_short_ms": (r"ttft$", "ttft_ms")}


def prompt_spec(metric):
    if metric in PROMPT_SPEC:
        return PROMPT_SPEC[metric]
    m = re.match(r"prefill_(\d+)$", metric)
    return (rf"prefill-{m.group(1)}$", "prefill_tps") if m else None


def pooled_prompts(rows, spec):
    pat, field = spec
    acc = {}
    for r in rows:
        for pid, d in r["per_prompt"].items():
            if re.match(pat, pid):
                acc.setdefault(pid, []).extend(v for v in d.get(field) or [] if numeric(v) and v > 0)
    return {p: statistics.fmean(v) for p, v in acc.items() if v}


def samples(rows, m):
    out = []
    for r in rows:
        vals = [v for v in r["metrics_passes"].get(m) or [] if numeric(v) and v > 0]
        if not vals and numeric(r["metrics"].get(m)) and r["metrics"][m] > 0:
            vals = [r["metrics"][m]]
        out += vals
    return out


def totals(metric, ctl, cand, common):
    if metric == "c1_decode":
        num, den, off = "completion_tokens", "decode_ms", -1
    elif re.match(r"prefill_\d+$", metric):
        num, den, off = "prompt_tokens", "ttft_ms", 0
    else:
        return None

    def side(rows):
        a = b = 0.0
        for r in rows:
            for pid in common:
                x = r["per_prompt"].get(pid) or {}
                for t, ms in zip(x.get(num) or [], x.get(den) or []):
                    if numeric(t) and numeric(ms) and ms > 0:
                        a, b = a + t + off, b + ms / 1000
        return a / b if b else None
    c, k = side(cand), side(ctl)
    return c / k - 1 if c and k else None


def prompt_shas(rows, pat):
    acc = {}
    for r in rows:
        for pid, d in r["per_prompt"].items():
            if re.match(pat, pid):
                acc.setdefault(pid, set()).update(s for s in d.get("prompt_sha") or [] if s)
    return acc


def compare(metric, ctl_rows, cand_rows, iters=2000):
    lower, rng, note = lower_better(metric), random.Random(0), None
    spec = prompt_spec(metric)
    if spec:
        pc, pk = pooled_prompts(cand_rows, spec), pooled_prompts(ctl_rows, spec)
        common = sorted(p for p in pc if p in pk)
        hc, hk = prompt_shas(cand_rows, spec[0]), prompt_shas(ctl_rows, spec[0])
        if any(hc.get(p) and hk.get(p) and not hc[p] & hk[p] for p in common):
            note = "unpaired: reused server without cache bypass (ctl and cand prompts differ)"
        elif len(common) >= 3:
            logs = [math.log(pc[p] / pk[p]) * (-1 if lower else 1) for p in common]
            boots = [math.exp(statistics.fmean(rng.choices(logs, k=len(logs)))) - 1 for _ in range(iters)]
            return {"gain": math.exp(statistics.fmean(logs)) - 1, "se": statistics.stdev(boots),
                    "totals": totals(metric, ctl_rows, cand_rows, common), "paired": True, "note": None,
                    "method": f"paired geomean over {len(common)} prompts"}
    sc, sk = samples(cand_rows, metric), samples(ctl_rows, metric)
    if not sc or not sk:
        return None

    def g(c, k):
        return (k / c if lower else c / k) - 1
    se = 0.0
    if len(sc) > 1 or len(sk) > 1:
        se = statistics.stdev(g(statistics.fmean(rng.choices(sc, k=len(sc))), statistics.fmean(rng.choices(sk, k=len(sk))))
                              for _ in range(iters))
    return {"gain": g(statistics.fmean(sc), statistics.fmean(sk)), "se": se, "totals": None, "paired": False,
            "note": note, "method": f"ratio of means, {len(sk)} ctl / {len(sc)} cand per-pass samples (unpaired)"}


def greedy_answers(rows, ledger_dir):
    out = {}
    for r in rows:
        if not r.get("run_dir"):
            continue
        for q in read_jsonl(os.path.join(ledger_dir, r["run_dir"], "requests.jsonl")):
            if q.get("kind") in ("determinism", "long", "prefill") and q.get("output_sha12"):
                key = (q.get("prompt_sha"), json.dumps(q.get("path"), sort_keys=True))
                out.setdefault(key, set()).add(q["output_sha12"])
    return out


def verdict(ctl_names, cand, mode, since=None, metric="c1_decode", watch=None, path="ledger.jsonl",
            rig_path="rig.json", predicted=None, surprise_ratio=2.0):
    rows = [dict(normalize(r), _i=i) for i, r in enumerate(read_jsonl(path))]
    if not rows:
        sys.exit(f"no rows in {path}")
    noise = rig_noise(read_json(rig_path, {}))
    k, floor, z = noise["k"], noise["floor_pct"], Z95
    t_since = parse_time(since) if since else None

    def sel(name):
        return [r for r in rows if r.get("name") == name and (not t_since or (row_time(r) and row_time(r) >= t_since))]
    reasons, repeat, notes, vflags = [], [], [], []
    if mode == "triple":
        if len(set(ctl_names)) < 2 or cand in ctl_names:
            sys.exit("the three runs need distinct names: copy the control config to a second name (e.g. ctl-a, ctl-b)")
        picked = {n: sel(n) for n in (*ctl_names, cand)}
        missing = [n for n, rs in picked.items() if not rs]
        if missing:
            sys.exit(f"not in {path}: {', '.join(missing)}")
        ctl_rows, cand_rows = [picked[n][-1] for n in ctl_names], [picked[cand][-1]]
        win_ctl = sorted(ctl_rows, key=lambda r: r["_i"])
        for r in ctl_rows + cand_rows:
            if not good(r):
                reasons.append(f"{r['name']}: ok={r.get('ok')} flags={','.join(r['flags']) or '-'}")
    else:
        if ctl_names[0] == cand:
            sys.exit("--ctl and --cand need different names")
        ca, cc = sel(ctl_names[0]), sel(cand)
        missing = [n for n, rs in ((ctl_names[0], ca), (cand, cc)) if not rs]
        if missing:
            sys.exit(f"not in {path}{' since ' + since if since else ''}: {', '.join(missing)}")
        if not good(cc[-1]):
            reasons.append(f"latest {cand} run {cc[-1].get('run_id', '')}: ok={cc[-1].get('ok')} "
                           f"flags={','.join(cc[-1]['flags']) or '-'}")
        ctl_rows, cand_rows = [r for r in ca if good(r)], [r for r in cc if good(r)]
        first_c = min(r["_i"] for r in cc)
        before = [r for r in ctl_rows if r["_i"] < first_c]
        start = before[-1]["_i"] if before else -1
        win_ctl = [r for r in ctl_rows if r["_i"] >= start]
        skipped = [r for r in ca + cc[:-1] if not good(r) and r["_i"] >= start]
        if skipped:
            notes.append(f"skipped {len(skipped)} runs not ok or flagged: "
                         + ", ".join(str(r.get("run_id") or r.get("time")) for r in skipped))
        if not ctl_rows:
            reasons.append(f"no usable {ctl_names[0]} run")
    window = win_ctl + cand_rows
    out = {"time": now_iso(), "mode": mode, "ctl": ctl_names, "cand": cand, "metric": metric,
           "ctl_runs": [r.get("run_id") or r.get("time") for r in ctl_rows],
           "cand_runs": [r.get("run_id") or r.get("time") for r in cand_rows],
           "window_runs": [r.get("run_id") or r.get("time") for r in window], "predicted_pct": predicted}
    if mode == "triple":
        out.update(ctl_a=ctl_names[0], ctl_b=ctl_names[1])
    if len({r.get("config_hash") for r in ctl_rows if r.get("config_hash")}) > 1:
        reasons.append("control config_hash differs across the selected loads: pick loads of one config with --since")
    group = noise_stats(rows, noise["window"]).get(ctl_rows[-1].get("config_hash") if ctl_rows else None) or {}
    ns_all = group.get("metrics", {})
    l_ctl, l_cand = max(len(ctl_rows), 1), max(len(cand_rows), 1)
    b = bars(ns_all.get(metric), l_ctl, l_cand, noise)
    sd_load = b["sd_load_pct"]
    z = Z95 * b["t_scale"]
    out.update(calibrated=b["calibrated"], bar_pct=round(b["bar_pct"], 3), sd_pct=sd_load and round(sd_load, 3),
               ci=None)
    below = False
    c = compare(metric, ctl_rows, cand_rows) if ctl_rows and cand_rows else None
    if not c:
        reasons.append(f"{metric} missing in the control or candidate runs")
    else:
        g, bar = 100 * c["gain"], b["bar_pct"]
        se_prompt = 100 * c["se"]
        se_load = sd_load * math.sqrt(1 / l_ctl + 1 / l_cand) if b["calibrated"] else 0.0
        se_total = math.sqrt(se_prompt ** 2 + se_load ** 2)
        lower, upper = g - z * se_total, g + z * se_total
        out.update(gain_pct=round(g, 3), ci=[round(lower, 3), round(upper, 3)], se_total_pct=round(se_total, 3),
                   se_prompt_pct=round(se_prompt, 3), se_load_pct=round(se_load, 3),
                   totals_pct=None if c["totals"] is None else round(100 * c["totals"], 3), method=c["method"])
        if c["note"]:
            notes.append(c["note"])
        if not b["calibrated"]:
            notes.append("CI is prompt-only (no load-to-load term before calibration)")
        if g <= 0:
            reasons.append(f"no gain on {metric}: {g:+.2f}% (95% CI {lower:+.2f}..{upper:+.2f}%)")
        elif g >= bar:
            if lower <= 0:
                repeat.append(f"gain {g:+.2f}% clears the {bar:.2f}% bar but the lower bound {lower:+.2f}% <= 0: "
                              "one more load in reverse order (BA)")
        elif lower > 0:
            below = True
        elif len(cand_rows) < 2 and b["calibrated"] and upper >= bar:
            repeat.append(f"inconclusive: gain {g:+.2f}% (CI {lower:+.2f}..{upper:+.2f}%) could still clear the "
                          f"{bar:.2f}% bar with one candidate load; run one more load of each config before rejecting")
        else:
            reasons.append(f"gain {g:+.2f}% is under the {bar:.2f}% bar and the lower bound {lower:+.2f}% <= 0")
        n_cand = len(cand_rows)
        if predicted is not None:
            if g > surprise_ratio * predicted and n_cand < 2:
                repeat.append(f"win of {g:+.2f}% is above {surprise_ratio:g} x the predicted {predicted:+.2f}%: "
                              "repeat the candidate load before accepting")
        elif g > FALLBACK["surprise"] and n_cand < 2:
            repeat.append(f"win of {g:+.2f}% is above {FALLBACK['surprise']:.0f}% with one candidate load: "
                          "repeat it before accepting (or pass --predicted)")
        if c["totals"] is not None and (c["totals"] > 0) != (c["gain"] > 0):
            notes.append(f"totals ratio {100 * c['totals']:+.2f}% disagrees in sign with the per-prompt geomean")
        if mode == "triple":
            for r in ctl_rows:
                ci = compare(metric, [r], cand_rows)
                if ci and ci["gain"] <= 0:
                    reasons.append(f"does not beat {r['name']} on {metric}: {100 * ci['gain']:+.2f}%")
        means = [statistics.fmean(s) for s in (samples([r], metric) for r in win_ctl) if s]
        if len(means) > 1:
            mu = statistics.fmean(means[:-1])
            dev = 100 * abs(means[-1] - mu) / mu
            thr = (max(k * sd_load * math.sqrt(1 + 1 / (len(means) - 1)), floor) if b["calibrated"]
                   else FALLBACK["drift"])
            out.update(drift_pct=round(dev, 3), drift_bar_pct=round(thr, 3))
            if dev > thr:
                repeat.append(f"newest control load differs from the other window loads by {dev:.2f}% "
                              f"(> drift bar {thr:.2f}%): one more load in reverse order (BA)")
        for r in window:
            s = [v for v in r["metrics_passes"].get(metric) or [] if numeric(v)]
            if len(s) > 1 and s[0]:
                t = 100 * abs(s[-1] - s[0]) / abs(s[0])
                if t > b["trend_pct"]:
                    repeat.append(f"{r.get('run_id') or r['name']}: first vs last pass differ by {t:.2f}% "
                                  f"(> {b['trend_pct']:.2f}%): drift inside the load")
        if b["calibrated"] and b["sd_within_pct"] and b["sd_within_pct"] > b["bar_pct"]:
            vflags.append("NOISY")
            notes.append(f"NOISY: per-pass SD {b['sd_within_pct']:.2f}% > bar {b['bar_pct']:.2f}% (watch only)")
    if not b["calibrated"]:
        notes.append(f"uncalibrated: fallback {FALLBACK['bar']:.0f}% bar / {FALLBACK['drift']:.0f}% drift / "
                     f"{FALLBACK['surprise']:.0f}% surprise; calibration needs >= {noise['min_loads']} ok control "
                     f"loads and >= {noise['min_df']} within-load degrees of freedom")
    if any("HOST_BUSY" in r["flags"] for r in window):
        repeat.append("HOST_BUSY in a compared run: host load above the idle baseline during timing")
    every = ctl_rows + cand_rows
    if any("LOW_N" in r["flags"] for r in every):
        vflags.append("LOW_N")
        notes.append("LOW_N: too few samples or tokens in a compared run (watch only)")
    shared = set.intersection(*(set(r["metrics"]) for r in every)) if every else set()
    core = {m for m in shared if m in ("c1_decode", "step_ms", "mem_peak_gib")
            or re.match(r"c\d+_aggregate$", m) or re.match(r"prefill_\d+$", m)}
    checked = sorted((set(watch) & shared if watch else core) - {metric})
    out["watched"] = checked
    for m in checked:
        cm = compare(m, ctl_rows, cand_rows)
        if not cm:
            continue
        bm = bars(ns_all.get(m), l_ctl, l_cand, noise)
        if 100 * cm["gain"] < -bm["bar_pct"]:
            reasons.append(f"{m} worse by {-100 * cm['gain']:.2f}% (> bar {bm['bar_pct']:.2f}%)")
    if cand_rows and cand_rows[-1].get("claims") == "l0":
        dets = [r.get("deterministic") for r in ctl_rows]
        if c and not c["paired"] and c["note"]:
            notes.append("ANSWER_DIFF not available: ctl and cand prompts differ (reused server without cache bypass)")
        elif any(d is False for d in dets):
            notes.append("answer identity not available: the control is not deterministic on this rig+engine; "
                         "check the l0 claim with quality.py teacher-forced logit fingerprints")
        elif not any(d is True for d in dets):
            notes.append("control determinism unknown: run the control with --determinism before judging an l0 claim")
        else:
            ldir = os.path.dirname(os.path.abspath(path))
            ga, gc = greedy_answers(ctl_rows, ldir), greedy_answers(cand_rows, ldir)
            keys = [key for key in gc if key in ga]
            diffs = [key for key in keys if gc[key] - ga[key]]
            out["answers_compared"] = len(keys)
            if not keys:
                notes.append("ANSWER_DIFF not available: no greedy answers on matching prompt and path "
                             "(run both with --determinism)")
            elif diffs:
                vflags.append("ANSWER_DIFF")
                reasons.append(f"ANSWER_DIFF: candidate claims l0 but {len(diffs)}/{len(keys)} greedy answers differ "
                               "from the control on the same prompt and compute path")
    if cand_rows and not cand_rows[-1].get("proof"):
        notes.append("candidate has no proof recorded: ask for evidence that the changed path ran")
    if mode == "pair" and not b["calibrated"] and not reasons:
        repeat.append(f"uncalibrated pair verdict: the CI leaves out load-to-load noise, so it cannot ACCEPT or call "
                      f"a gain real; run control loads until >= {noise['min_loads']} ok loads and >= "
                      f"{noise['min_df']} within-load df, or use the control-candidate-control triple")
    decision = "REJECT" if reasons else "REPEAT" if repeat else "BELOW_BAR" if below else "ACCEPT"
    out.update(decision=decision, flags=sorted(set(vflags)), reasons=reasons + repeat, notes=notes)
    append_jsonl(os.path.join(os.path.dirname(os.path.abspath(path)), "verdicts.jsonl"), out)
    head = (f"{decision}: {cand} vs {' / '.join(ctl_names)} on {metric} "
            f"({mode}, {len(ctl_rows)} ctl + {len(cand_rows)} cand loads)")
    if out.get("gain_pct") is not None:
        head += (f": {out['gain_pct']:+.2f}% (95% CI {out['ci'][0]:+.2f}..{out['ci'][1]:+.2f}%), "
                 f"bar {out['bar_pct']:.2f}% {'calibrated' if b['calibrated'] else 'uncalibrated'}")
        if out.get("totals_pct") is not None:
            head += f", totals {out['totals_pct']:+.2f}%"
    print(head)
    if out.get("se_total_pct") is not None:
        print(f"  se_total {out['se_total_pct']:.3f}% = sqrt(se_prompt {out['se_prompt_pct']:.3f}%^2 + "
              f"se_load {out['se_load_pct']:.3f}%^2); {out['method']}")
    for r in out["reasons"]:
        print("  -", r)
    for n in notes:
        print("  note:", n)
    return out


def noise_cmd(path="ledger.jsonl", rig_path="rig.json"):
    rows = [normalize(r) for r in read_jsonl(path)]
    noise = rig_noise(read_json(rig_path, {}))
    stats = noise_stats(rows, noise["window"])
    if not stats:
        sys.exit(f"no good schema-2 rows in {path}")
    print(f"window {noise['window']} rows per config hash; k={noise['k']}, floor {noise['floor_pct']}%")
    print("hash".ljust(10) + "names".ljust(26) + "metric".ljust(28) + "loads".rjust(6) + "passes".rjust(7)
          + "mean".rjust(12) + "sd_within%".rjust(11) + "df".rjust(5) + "sd_between%".rjust(12))

    def f(x):
        return "-" if x is None else f"{x:.3f}"
    for h, g in stats.items():
        for m, s in g["metrics"].items():
            print(h[:8].ljust(10) + ",".join(g["names"])[:25].ljust(26) + m[:27].ljust(28) + str(s["loads"]).rjust(6)
                  + str(s["passes_per_load"]).rjust(7) + f"{s['mean']:.3f}".rjust(12) + f(s["sd_within_pct"]).rjust(11)
                  + str(s["df_within"]).rjust(5) + f(s["sd_between_pct"]).rjust(12))


def board(baseline=None, ceilings=None, path="ledger.jsonl"):
    rows = [normalize(r) for r in read_jsonl(path)]
    if not rows:
        sys.exit(f"no rows in {path}")
    decisions = {}
    for v in read_jsonl(os.path.join(os.path.dirname(os.path.abspath(path)), "verdicts.jsonl")):
        decisions[v.get("cand")] = v.get("decision")
    if baseline:
        bs = [r for r in rows if r.get("name") == baseline]
        if not bs:
            sys.exit(f"baseline {baseline} not in {path}")
        base = bs[-1]
    else:
        base = next((r for r in rows if good(r)), rows[0])
    ceil = read_json(ceilings) if ceilings else None
    cm = (ceil or {}).get("metrics") or {}
    latest, loads = {}, {}
    for r in rows:
        latest[r["name"]] = r
        loads[r["name"]] = loads.get(r["name"], 0) + (1 if r.get("ok") else 0)
    allm = {k for r in latest.values() for k in r["metrics"]}
    agg = sorted(k for k in allm if re.match(r"c\d+_aggregate$", k))[:1]
    pre = sorted((k for k in allm if re.match(r"prefill_\d+$", k)), key=lambda k: int(k[8:]))[:2]
    cols = ["c1_decode", *agg, *pre]

    def vs(r, m):
        a, b = r["metrics"].get(m), base["metrics"].get(m)
        if not numeric(a) or not numeric(b) or not a or not b:
            return "-"
        return f"{100 * ((b / a if lower_better(m) else a / b) - 1):+.1f}%"

    def of_ceiling(v, m, kind):
        c = (cm.get(bare(m)) or {}).get(kind)
        if not numeric(v) or not numeric(c) or not c or not v:
            return "-"
        return f"{100 * (c / v if lower_better(m) else v / c):.0f}%"
    print(f"baseline: {base['name']} ({base.get('time')})"
          + (f"; ceilings {ceilings} config_hash {str(ceil.get('config_hash'))[:8]}" if ceil else ""))
    hdr = "name".ljust(24) + "loads".rjust(6) + "".join(c[:13].rjust(14) for c in cols) + "vs base".rjust(9)
    hdr += ("%hard".rjust(7) + "%pract".rjust(7) if cm else "") + "  decision    flags"
    print(hdr)
    for name, r in latest.items():
        line = str(name)[:24].ljust(24) + str(loads[name]).rjust(6)
        line += "".join(str(r["metrics"].get(c, "-"))[:13].rjust(14) for c in cols) + vs(r, "c1_decode").rjust(9)
        if cm:
            v = r["metrics"].get("c1_decode")
            line += of_ceiling(v, "c1_decode", "hard").rjust(7) + of_ceiling(v, "c1_decode", "practical").rjust(7)
        line += "  " + str(decisions.get(name, "-")).ljust(10) + "  " + ("" if r.get("ok") else "NOT-OK ")
        print(line + ",".join(r["flags"]))
    accepted = [n for n, d in decisions.items() if d == "ACCEPT" and n in latest]
    best = latest[accepted[-1]] if accepted else base
    if cm:
        print(f"\nceilings for {best['name']} (metric, value, % of hard, % of practical-at-current-graph):")
        for m, v in sorted(best["metrics"].items()):
            if bare(m) in cm:
                print(f"  {m:<36}{v:>12}{of_ceiling(v, m, 'hard'):>8}{of_ceiling(v, m, 'practical'):>8}")
    durs = [r["dur_s"] for r in rows if numeric(r.get("dur_s"))]
    if durs:
        print(f"\nruns: {len(rows)}; logged time {sum(durs) / 3600:.1f} h; mean run {statistics.fmean(durs) / 60:.1f} min "
              "(ETA = runs left x mean run)")
    noise = rig_noise(read_json(os.path.join(os.path.dirname(os.path.abspath(path)), "rig.json"), {}))
    ns = (noise_stats(rows, noise["window"]).get(base.get("config_hash")) or {}).get("metrics", {}).get("c1_decode")
    b = bars(ns, 1, 1, noise)
    print("noise (baseline config, c1_decode): "
          + (f"calibrated, between-load SD {b['sd_load_pct']:.2f}%, 1-vs-1 load bar {b['bar_pct']:.2f}%"
             if b["calibrated"] else f"uncalibrated (fallback {FALLBACK['bar']:.0f}% bar; needs >= "
                                     f"{noise['min_loads']} ok loads and >= {noise['min_df']} within-load df)"))


def main(a):
    if not a or a[0] not in ("run", "show", "verdict", "noise", "board", "resolve"):
        sys.exit(__doc__)

    def opt(k, d=None):
        if k not in a:
            return d
        i = a.index(k)
        if i + 1 >= len(a):
            sys.exit(__doc__)
        return a[i + 1]
    cmd = a[0]
    if cmd == "show":
        show(a[1] if len(a) > 1 and not a[1].startswith("--") else "ledger.jsonl")
    elif cmd == "resolve":
        if len(a) < 2:
            sys.exit(__doc__)
        cfg = load_config(a[1])
        print(json.dumps(cfg, indent=1, sort_keys=True))
        print("config_hash", config_hash(cfg), file=sys.stderr)
    elif cmd == "noise":
        noise_cmd(opt("--ledger", "ledger.jsonl"), opt("--rig", "rig.json"))
    elif cmd == "board":
        board(opt("--baseline"), opt("--ceilings"), opt("--ledger", "ledger.jsonl"))
    elif cmd == "verdict":
        kw = dict(metric=opt("--metric", "c1_decode"), watch=opt("--watch") and opt("--watch").split(","),
                  path=opt("--ledger", "ledger.jsonl"), rig_path=opt("--rig", "rig.json"),
                  predicted=float(opt("--predicted")) if opt("--predicted") else None,
                  surprise_ratio=float(opt("--surprise-ratio", 2)))
        if "--ctl" in a or "--cand" in a:
            if not opt("--ctl") or not opt("--cand"):
                sys.exit(__doc__)
            verdict([opt("--ctl")], opt("--cand"), "pair", since=opt("--since"), **kw)
        else:
            pos = a[1:4]
            if len(pos) < 3 or any(x.startswith("--") for x in pos):
                sys.exit(__doc__)
            verdict([pos[0], pos[2]], pos[1], "triple", **kw)
    else:
        if len(a) < 2 or a[1].startswith("--"):
            sys.exit(__doc__)
        res = run(a[1], passes=opt("--passes"),
                  long_ctx=[int(x) for x in opt("--long").split(",")] if opt("--long") else (),
                  skip_cn="--skip-cN" in a, reps=int(opt("--reps", 6)), reuse="--reuse" in a,
                  determinism="--determinism" in a, samplers="--no-samplers" not in a,
                  rig_path=opt("--rig", "rig.json"))
        sys.exit(0 if res["ok"] else 1)


if __name__ == "__main__":
    main(sys.argv[1:])
