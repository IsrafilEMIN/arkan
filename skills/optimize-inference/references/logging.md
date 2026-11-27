# Logging

Logging is the base layer. It is always on, on any machine. Every `bench.py run` writes one run directory and one
ledger row, also when the run fails or is blocked. Later analysis reads these files; it never needs a new run to see
what an old run did.

## Working directory

```
rig.json  PLAN.md  THEORY.md  ledger.jsonl  verdicts.jsonl  queue.jsonl  best-config.json
configs/<name>.json   hypotheses/<run>.md   scripts/ (copy of skill scripts)
runs/<run_id>/        run_id = <name>-<UTC %Y%m%dT%H%M%S>
  config.resolved.json   identity.json   requests.jsonl   samples.jsonl   events.jsonl
  tokens.jsonl (opt-in)  logits/ (opt-in, engine hook)   tests/<test-name>/   proof.txt
```

| top-level item | content |
|---|---|
| `rig.json` | the rig inventory and check levels (`references/rig.md`) |
| `PLAN.md` | a timestamped log of every experiment, with numbers, verdict and reason; the go/no-go threshold and report format |
| `THEORY.md` | the ceilings, the quality contract, the time budget and the current diagnosis |
| `configs/` | one JSON per run |
| `hypotheses/` | one card per experiment, from `templates/hypothesis.md`, written before the run |
| `scripts/` | a copy of the skill's `scripts/`. Run the harness from the working directory, so configs reach the memory probe as `scripts/mem.sh` |
| `best-config.json` | the current best config |

| file | content |
|---|---|
| `config.resolved.json` | the config after `base` + deltas, as the run used it |
| `identity.json` | binary, repo commit and other identity fields from the config's `identity` |
| `requests.jsonl` | one row per request (schema below) |
| `samples.jsonl` | one line per sampler tick: `{"t", "phase", ...flattened machine state}` from `rig.py`'s `Sampler` |
| `events.jsonl` | harness events during the run (launch, ready, tests, watchdog actions, stop) |
| `tokens.jsonl` | opt-in token log (config `"token_log": {"top_logprobs": 5}`, when the server supports logprobs) |
| `logits/` | opt-in full-vocab logits from an engine hook (format in `references/quality.md`) |
| `tests/<test-name>/` | output of each `tests` entry; `metrics.json` (flat JSON of numbers) is merged into the ledger |
| `proof.txt` | output of the config's `proof` command |

## Ledger row (schema 2)

```
{"schema": 2, "run_id", "run_dir", "name", "config_hash", "time", "ok", "flags", "not_available", "passes",
 "metrics": {metric: value}, "metrics_passes": {metric: [per-pass values]},
 "per_prompt": {prompt_id: {metric: [per-pass values]}}, "deterministic": true|false|null,
 "identity": {...}, "state_start", "state_end", "phases": {...sampler medians...}, "tests": {...}, "proof": {...},
 "startup_s", "mem_peak_gib", "host_ram_min_gib", "reused_server"}
```

- `config_hash`: sha256 of the resolved config minus `"name"`. Noise is pooled per config hash.
- Metric names: `c1_decode`, `c<N>_aggregate`, `prefill_<L>`, `ttft_short_ms`, plus `step_ms`/`accept_len` when the
  engine reports them, plus test metrics as `<test-name>.<metric>`.
- `flags`: LOOP, REQ_FAIL, ON_BATTERY, MEM_CAP, MEM_PROBE_FAIL, NEEDLE_MISS, TEST_FAIL, NO_PROOF, RIG_BLOCK (preflight
  blocked, run not started, `ok=false`), HOST_FLOOR (host-RAM watchdog stopped the run), NO_PROGRESS (no token for
  `no_progress_s`: abort, stop), STATE_CHANGED (power limit or persistence changed: run void), HOST_BUSY (CPU or disk
  above the idle baseline in the timed window), LOW_N (too few c1 samples or tokens per sample). How `verdict` treats
  them: `references/methodology.md`, The verdict statistics.
- Verdict flags, in `verdicts.jsonl` only: NOISY (`references/methodology.md`, The verdict statistics) and ANSWER_DIFF
  (`references/quality.md`).
- `not_available`: checks, collectors or tests that a platform lacks. They never block; state them in the report.
- Old schema-1 rows (no `"schema"`) stay readable: their top-level numeric keys are treated as metrics.

## Request row

```
{"run_id","pass","kind":"warmup|ttft|c1|cN|prefill|long|determinism|test","prompt_id","prompt_sha","seed",
 "prompt_tokens","completion_tokens","cached_tokens","ttft_ms","decode_ms","decode_tps","step_ms","draft_n",
 "draft_accepted","finish_reason","output_sha12","loop":bool,"t_start","t_end",
 "path":{"batch":int,"chunk":int|null,"cache":"cold|warm|bypass"},"engine":{...raw adapter fields...}}
```

Prompt prefixes and cache bypass on reused servers: `references/methodology.md`, Counting.

## Other files

- `verdicts.jsonl`: one row per `bench.py verdict`, with `"mode": "pair|triple"`, `"calibrated"`, `"bar_pct"`,
  `"ci"`, `"se_total"`, `"se_prompt"`, `"se_load"` and the decision (ACCEPT, REJECT, REPEAT, BELOW_BAR).
- `queue.jsonl`: `{"t": iso, "event": "start|end|fail|skip", "name", "rc", "dur_s", "queue", "pid", "step", "total",
  "names"}` from `scripts/queue.sh`.

## Collectors

The machine-state collectors are detected the same way as the rig checks (`references/rig.md`) and stored in
`rig.json` `collectors`; override them there. A collector that is missing is recorded as "not available" and never
blocks a run.

## Heavy items (opt-in)

- Full-vocab logits: an engine hook, turned on only when a quality class needs them (`references/quality.md`).
- Profiler traces: their own load, never during a timed run. Store the trace with a summary (`scripts/budget.py`).

## Logger cost

Once per rig, A/B the same config with the samplers off and on (`bench.py run --no-samplers`). Logging must cost less
than the noise bar. If it does not, set the costly collector to `none` in `rig.json` `collectors` and record that.

## What the ledger gives without new runs

- Noise SD per config hash and metric, within and between loads: `python3 scripts/bench.py noise`
  (`references/methodology.md`).
- Progress board: `python3 scripts/bench.py board [--baseline NAME] [--ceilings ceilings.json]`.
- ETAs from logged durations: `bash scripts/queue.sh status`.
- The quality floor from repeated control token logs (`references/quality.md`).

## Test hooks

A config's `tests` entries run on the running server and get this environment: `BENCH_BASE_URL`, `BENCH_MODEL`,
`BENCH_RUN`, `BENCH_RUN_ID`, `BENCH_RUN_DIR`, `BENCH_CONFIG` (path of the resolved config), `BENCH_PASS`,
`BENCH_ENGINE_LOG`, `BENCH_LOG_OFFSET` (byte offset of the engine log at test start; read only lines after it).
A test writes flat metrics to `$BENCH_RUN_DIR/tests/<name>/metrics.json`.

## Harness scripts

- `bench.py`: `run`, `show`, `verdict`, `noise`, `board`, `resolve`. Drivers (`http`, `cli`), timing adapters, config
  `base` + deltas, test hooks.
- `rig.py`: `detect`, `check`, `state`, `noise`. `queue.sh`: serialized queue and `status`. `mem.sh`, `mem-macos.sh`:
  memory probes.
- `ceiling.py`: ceilings. `workloads.py`: depth sweep, clients, multi-turn, invariance. `budget.py`: trace to
  attributed time per part.
- `quality.py`: l0/l1/l2 checks. `isa_diff.py`: per-function ISA diff of two builds.

## Your own tools

Extend `scripts/` through drivers, timing adapters and test hooks. If you must write your own tool, it appends ledger
rows in the schema above, so `verdict`, `noise` and `board` still work.
