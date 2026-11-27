# Rig safety

The rig is often a machine someone depends on. A run must not take it down, and a result must not come from a machine
that changed under it. This file defines six invariants, how `rig.json` and `scripts/rig.py` check them, and how to
leave the rig at the end.

## Six invariants

1. **The cards are yours.** No other compute process runs on the cards the run uses.
2. **The host keeps headroom and stays reachable.**
   - Host-RAM floor: default max(6 GiB, 10% of RAM). Also watch swap-in.
   - Builds and loads run in a capped scope (below).
3. **Safety daemons stay alive.** Rig hooks are commands that must exit 0, e.g. a fan or thermal guard.
4. **Machine state is recorded and does not change:** clocks, power limit, temperature, throttle reasons, AC power.
   A run is void (`STATE_CHANGED`) if the power limit or persistence mode changed during it.
5. **A failure stops the queue.** `--keep-going` is opt-in. Wait only on a PID, the lock, or log lines written after a
   recorded offset. Never use `pgrep -f`, and never grep over old log lines.
6. **Leave the rig as found.** See "Session end".

## Check results and levels

Each check gives pass, fail or not available.

- Default: a probe that ran and FAILED blocks the run (`RIG_BLOCK`, ledger row `ok=false`, the run does not start).
- Out of the box, cards idle, the host-RAM floor and the safety hooks block.
- A rig may lower any check to `warn` or `off` in `rig.json`.
- "Not available" never blocks. It goes into the ledger row's `not_available` and into the report.

## rig.json (schema 1)

Written during the section-0 inventory by `python3 scripts/rig.py detect`, then edited by you and the user.

```json
{
  "schema": 1,
  "platform": {"os": "linux|darwin", "gpu_vendor": "nvidia|amd|intel|apple|none", "gpus": [{"index": 0, "name": "...", "memory_gib": 32}],
               "ram_gib": 60, "cpus": 12},
  "collectors": {"gpu": "nvidia-smi|amd-smi|rocm-smi|xpu-smi|macos|none", "host": "linux-proc|macos|none"},
  "checks": {
    "cards_idle":     {"level": "block"},
    "host_ram_floor": {"level": "block", "floor_gib": null},
    "no_build":       {"level": "warn", "names": ["nvcc", "cicc", "ptxas", "ninja", "make", "cargo", "cc1plus"]},
    "on_ac":          {"level": "block"},
    "host_busy":      {"level": "warn", "load_per_cpu": 0.5}
  },
  "hooks": [{"name": "fan-guard", "cmd": ["systemctl", "is-active", "fan-guard"], "level": "block"}],
  "scope": {"build": ["systemd-run", "--user", "--scope", "-q", "-p", "MemoryHigh=30G", "-p", "CPUWeight=10", "nice", "-n", "19"], "load": []},
  "watchdog": {"no_progress_s": 600},
  "cache_bypass": {"mode": "request_field|flush_cmd|reload|none", "request_field": {"cache_prompt": false}, "flush_cmd": null},
  "noise": {"k": 2.5, "floor_pct": 0.3, "window": 20, "min_samples": 6, "min_tokens": 64, "min_loads": 3, "min_df": 4},
  "settings": {"protected": [], "accepted": []},
  "microbench": {"bw_gbs_by_read_mib": {}, "chain_node_us": null, "link_gbs": null, "peak_tflops_at_cap": null}
}
```

- A check level is `block`, `warn` or `off`. `floor_gib: null` means the default max(6, 10% of `ram_gib`).
- `hooks`: ask the user which daemons must stay alive; add one entry per daemon (optional `"timeout_s"`, default 30).
  A hook whose command is missing fails; it is never "not available", because the user asked for that daemon.
- `checks.host_busy` also takes `"disk_busy_pct"` (default 50) for the sampler's disk-busy flag.
- `settings.protected`: settings the user said you must not touch. `settings.accepted`: changed settings the user
  accepted into the best config.
- `cache_bypass`: how the determinism check bypasses the prompt cache (`references/quality.md`).
- `noise`: the bar parameters (`references/methodology.md`). A verdict is "calibrated" only with at least `min_loads`
  ok control loads and at least `min_df` within-load degrees of freedom. They are defaults; the rig or user can change
  them.
- `microbench`: inputs to the ceilings (`references/ceilings.md`), measured once per rig with short microbenchmarks:
  bandwidth at the real read sizes, cost of one dependent kernel node, link bandwidth under real concurrent traffic,
  peak FLOPs at the served power cap and clocks.

## scripts/rig.py

```
python3 scripts/rig.py detect [--out rig.json] [--force]                   # detect platform and collectors, write defaults
python3 scripts/rig.py check  [--rig rig.json] [--cards 0,1] [--allow-pids PID,PID]
python3 scripts/rig.py state  [--rig rig.json]                             # JSON machine-state snapshot
python3 scripts/rig.py noise  [--ledger ledger.jsonl] [--rig rig.json] [--json]   # pooled SD per config hash and metric
```

- `detect` never overwrites an existing file without `--force`. With an existing file it prints the difference between
  detected and stored values.
- `check` prints one line per check, `name status level detail` (status `pass`, `fail` or `na`), and exits 1 if a
  blocking check failed, else 0.
- `--allow-pids` (import API: `preflight(rig, cards=None, allow_pids=None)`): `cards_idle` ignores these PIDs and
  their descendants, e.g. the server the harness left running. The PIDs of that server are the `"pids"` in
  `.bench-server.json`.
- `noise --json` prints the result as JSON. `noise` reads ok schema-2 ledger rows over the last
  `noise.window` loads of each config; schema-1 rows are skipped and counted.
- `bench.py run` and `queue.sh` call the same checks before each run.
- Fields a platform lacks are null in `state`.

## scripts/queue.sh

```
bash scripts/queue.sh [--keep-going] NAME...    # run configs/NAME.json in order under the lock
bash scripts/queue.sh status                    # current step, done/total and ETA of the latest queue
```

- Before each run it calls `rig.py check`; a blocking check skips the run.
- The queue stops at the first skip, non-zero exit, missing ledger row, ledger row with `ok=false`, or ledger row with a
  stop flag. `--keep-going` continues with the next name instead.
- `QUEUE_STOP_FLAGS` sets the stop flags. Default: `RIG_BLOCK HOST_FLOOR NO_PROGRESS STATE_CHANGED MEM_CAP
  MEM_PROBE_FAIL REQ_FAIL ON_BATTERY TEST_FAIL NO_PROOF`.
- `QUEUE_ALLOW_PIDS`: extra PIDs the cards check ignores. The `"pids"` of `.bench-server.json` are always ignored.
- Other env: `BENCH_FLAGS` (passed to `bench.py run`), `QUEUE_CARDS` (`--cards`), `QUEUE_LOCK`, `RIG_JSON`, `LEDGER`,
  `QUEUE_LOG`. Events go to `queue.jsonl` (`references/logging.md`).

## Capped scopes

Builds and loads run in a capped scope, taken from `rig.json` `scope`, so they cannot starve the host.

- Linux: `systemd-run --user --scope -p MemoryHigh=.. -p CPUWeight=..` plus `nice`.
- macOS: `taskpolicy -b` or `nice`.
- `ionice` does nothing with the `none` I/O scheduler. Check that it has an effect before you rely on it.
- Never build during a timed run (`no_build` check).
- Root-level host changes (e.g. `MemoryMin` for ssh or VPN, swappiness) are proposals to the user. Never script them.

## Watchdog during a run

- The memory cap watchdog (`scripts/mem.sh`, `scripts/mem-macos.sh`) kills the run at the cap (`MEM_CAP`).
- Host-RAM floor: kill when host RAM falls below the floor (`HOST_FLOOR`).
- No progress: no tokens for `watchdog.no_progress_s` seconds -> abort, drain, stop (`NO_PROGRESS`).
- `HOST_BUSY`: a ledger flag set when CPU load or disk I/O in the timed window rose above the idle baseline. It does
  not stop the run; a verdict that compares a run carrying it gives REPEAT. (The `host_busy` preflight check before the
  run is separate and warns by default.)

## Session end

- List your own background processes (queues, servers, watchers) by PID and stop the ones the user does not want kept.
- Restore every setting you changed, except the ones in `settings.accepted`.
- Report what you restored, what you left changed and why, and what was not available on this rig.
