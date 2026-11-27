#!/usr/bin/env bash
USAGE='Serialized GPU queue: runs bench.py on each config in order, one GPU job at a time across all callers.
  bash scripts/queue.sh [--keep-going] NAME...       run configs/NAME.json in order under the lock
  bash scripts/queue.sh status                       current step, done/total and ETA of the latest queue
Before each run: python3 scripts/rig.py check (cards idle, host-RAM floor, safety hooks ...); a blocking check
skips the run. The queue stops at the first skip, non-zero exit, missing ledger row, ledger row with ok=false, or a
ledger row carrying a stop flag; --keep-going continues with the next name instead. Events go to queue.jsonl:
  {"t", "event": "start|end|fail|skip", "name", "rc", "dur_s", "queue", "pid", "step", "total", "names"}
Env: BENCH_FLAGS (passed to bench.py run), QUEUE_CARDS (rig.py check --cards), QUEUE_ALLOW_PIDS (extra PIDs the
cards check ignores; the "pids" of .bench-server.json, the server the last run left up, are always ignored),
QUEUE_STOP_FLAGS (default: RIG_BLOCK HOST_FLOOR NO_PROGRESS STATE_CHANGED MEM_CAP MEM_PROBE_FAIL REQ_FAIL
ON_BATTERY TEST_FAIL NO_PROOF), QUEUE_LOCK, RIG_JSON (rig.json), LEDGER (ledger.jsonl), QUEUE_LOG (queue.jsonl).
Examples:
  BENCH_FLAGS="--passes 3" bash scripts/queue.sh ctl cand        # one load per config, passes inside each load
  BENCH_FLAGS="--long 65536,131072 --soak 4" bash scripts/queue.sh cand   # stability gate, candidate only
  BENCH_FLAGS="--reuse" bash scripts/queue.sh ctl cand ctl cand  # same launch (e.g. extra_body toggle): alternate in one load
  bash scripts/queue.sh ctl-a cand ctl-b                         # triple mode, when between-load noise is large
Detach long queues so they survive agent/terminal restarts. Linux:
  setsid nohup bash scripts/queue.sh ctl cand > queue.log 2>&1 < /dev/null & disown
macOS has no setsid; python3 forks first, then starts a new session (a bare os.setsid() fails with EPERM in a
job-control shell, because the background job leads its own process group):
  python3 -c '"'"'import subprocess,sys; subprocess.Popen(sys.argv[1:], start_new_session=True)'"'"' bash scripts/queue.sh ctl cand > queue.log 2>&1 < /dev/null
Run from your experiment directory (the one holding configs/, rig.json and ledger.jsonl).'
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
BENCH=${BENCH:-$HERE/bench.py}
RIG=${RIG:-$HERE/rig.py}
RIG_JSON=${RIG_JSON:-rig.json}
LEDGER=${LEDGER:-ledger.jsonl}
QLOG=${QUEUE_LOG:-queue.jsonl}
STOP_FLAGS=${QUEUE_STOP_FLAGS:-RIG_BLOCK HOST_FLOOR NO_PROGRESS STATE_CHANGED MEM_CAP MEM_PROBE_FAIL REQ_FAIL ON_BATTERY TEST_FAIL NO_PROOF}

status() {
  python3 - "$QLOG" <<'PY'
import json, os, statistics, sys, time
from datetime import datetime

path = sys.argv[1]
rows = []
if os.path.exists(path):
    with open(path) as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except ValueError:
                pass
if not rows:
    sys.exit(f"no queue events in {path}")
last = rows[-1]
q = [r for r in rows if r.get("queue") == last.get("queue")]
names, total = last.get("names") or [], last.get("total") or len(last.get("names") or [])
closed = {r["step"]: r for r in q if r.get("event") in ("end", "fail", "skip")}
open_ = [r for r in q if r.get("event") == "start" and r.get("step") not in closed]
try:
    os.kill(int(last.get("pid")), 0)
    alive = True
except (OSError, TypeError, ValueError):
    alive = False
if alive:
    st = "running"
elif len(closed) == total and all(r["event"] == "end" for r in closed.values()):
    st = "finished"
elif open_:
    st = "died (no end event for the running step)"
else:
    st = "stopped"
print(f"queue {last.get('queue')}: {st}, pid {last.get('pid')}, done {len(closed)}/{total}")
for s in sorted(closed):
    r = closed[s]
    dur = f"{r['dur_s']:.0f} s" if r.get("dur_s") is not None else "-"
    print(f"  {s}/{total} {r['event']:5} {r['name']} rc={r.get('rc')} {dur}")
ends = [r for r in rows if r.get("event") == "end" and r.get("dur_s")]
def est(n):
    ds = [r["dur_s"] for r in ends if r.get("name") == n] or [r["dur_s"] for r in ends]
    return statistics.fmean(ds) if ds else None
now = time.time()
remaining, unknown = 0.0, False
if open_:
    r = open_[-1]
    el = now - datetime.fromisoformat(r["t"]).timestamp()
    e = est(r["name"])
    print(f"  {r['step']}/{total} now   {r['name']} started {r['t']} ({el / 60:.0f} min ago"
          + (f", typical {e / 60:.0f} min)" if e else ")"))
    if e is None:
        unknown = True
    else:
        remaining += max(0.0, e - el)
if not alive:
    sys.exit(0)
seen = max([r.get("step", 0) for r in q] or [0])
for n in names[seen:]:
    e = est(n)
    if e is None:
        unknown = True
    else:
        remaining += e
if unknown and not ends:
    print("ETA: unknown (no finished runs in the log yet)")
else:
    finish = datetime.fromtimestamp(now + remaining).astimezone().isoformat(timespec="minutes")
    print(f"ETA: {remaining / 60:.0f} min left, done about {finish}" + (" (some steps not estimated)" if unknown else ""))
PY
}

ev() {
  python3 - "$QLOG" "$QID" "$$" "$1" "$2" "$3" "$4" "$5" "$TOTAL" "${NAMES[@]}" <<'PY'
import json, sys
from datetime import datetime
path, qid, pid, event, name, rc, dur, step, total, *names = sys.argv[1:]
row = {"t": datetime.now().astimezone().isoformat(timespec="seconds"), "event": event, "name": name,
       "rc": int(rc) if rc else None, "dur_s": float(dur) if dur else None, "queue": qid, "pid": int(pid),
       "step": int(step), "total": int(total), "names": names}
with open(path, "a") as f:
    f.write(json.dumps(row) + "\n")
PY
}

ledger_verdict() {
  python3 - "$LEDGER" "$1" "$STOP_FLAGS" <<'PY'
import json, sys
path, before, stop = sys.argv[1], int(sys.argv[2]), set(sys.argv[3].split())
try:
    with open(path) as f:
        lines = f.read().splitlines()[before:]
except OSError:
    lines = []
row = None
for line in reversed(lines):
    try:
        row = json.loads(line)
        break
    except ValueError:
        pass
if row is None:
    print("no new ledger row")
elif not row.get("ok", True):
    print(f"ok=false flags={','.join(row.get('flags') or []) or '-'}")
elif stop & set(row.get("flags") or []):
    print(f"stop flags {','.join(sorted(stop & set(row['flags'])))}")
else:
    print("ok")
PY
}

allow_pids() {
  local a
  a=$(python3 -c 'import json
try:
    print(",".join(str(int(p)) for p in json.load(open(".bench-server.json")).get("pids") or []))
except Exception:
    pass' 2>/dev/null)
  echo "${a}${QUEUE_ALLOW_PIDS:+${a:+,}$QUEUE_ALLOW_PIDS}"
}

case "${1:-}" in
  status) status; exit $? ;;
  -h|--help|"") echo "$USAGE" >&2; exit 2 ;;
esac
keep=0
if [ "$1" = --keep-going ]; then keep=1; shift; fi
[ $# -eq 0 ] && { echo "$USAGE" >&2; exit 2; }
for n in "$@"; do
  [ -f "configs/$n.json" ] || { echo "configs/$n.json not found" >&2; exit 2; }
done
NAMES=("$@"); TOTAL=$#

LOCK=${QUEUE_LOCK:-/tmp/inference-hillclimb.lock}
if command -v flock >/dev/null; then
  exec 9>"$LOCK"; flock 9
else
  until mkdir "$LOCK.d" 2>/dev/null; do sleep 2; done
  trap 'rmdir "$LOCK.d"' EXIT
  trap 'exit 130' INT TERM HUP
fi

QID=$(date +%Y%m%dT%H%M%S)-$$
rc_all=0; step=0
for n in "$@"; do
  step=$((step + 1))
  allow=$(allow_pids)
  if ! python3 "$RIG" check --rig "$RIG_JSON" ${QUEUE_CARDS:+--cards "$QUEUE_CARDS"} ${allow:+--allow-pids "$allow"} \
      > "runs-$n.check.log" 2>&1; then
    echo "skip $n: rig check blocked:"; grep -E ' fail block |Traceback|Error' "runs-$n.check.log"
    ev skip "$n" 1 "" "$step"; rc_all=1
    if [ $keep = 1 ]; then continue; else break; fi
  fi
  before=0; [ -f "$LEDGER" ] && before=$(wc -l < "$LEDGER")
  ev start "$n" "" "" "$step"
  t0=$(date +%s)
  python3 "$BENCH" run "configs/$n.json" ${BENCH_FLAGS:-} > "runs-$n.log" 2>&1
  rc=$?
  dur=$(( $(date +%s) - t0 ))
  why=$(ledger_verdict "$before")
  if [ $rc -eq 0 ] && [ "$why" = ok ]; then
    ev end "$n" "$rc" "$dur" "$step"
    echo "done $n (${dur}s): $(tail -c 300 "runs-$n.log" | tr '\n' ' ' | cut -c1-200)"
  else
    ev fail "$n" "$rc" "$dur" "$step"; rc_all=1
    echo "FAIL $n (rc=$rc, ${dur}s): $why; see runs-$n.log"
    if [ $keep = 0 ]; then break; fi
  fi
done
echo QUEUE_DONE "$@"
exit $rc_all
