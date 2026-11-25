#!/usr/bin/env bash
# Serialized GPU queue: runs bench.py on each config in order, one GPU job at a time across all callers.
#   bash scripts/queue.sh ctl-a cand ctl-b            # interleave controls around each candidate
#   BENCH_FLAGS="--long 65536,131072" bash scripts/queue.sh cand   # both needle lengths in one load
#   BENCH_FLAGS="--reuse" bash scripts/queue.sh ctl-a cand ctl-b  # same launch (e.g. extra_body toggle): no reload
# Group configs by server state (all tests in one config per state): one load per state in run order, not one per test.
# Detach long queues so they survive agent/terminal restarts (on macOS, which has no setsid, python3 calls it):
#   setsid nohup bash scripts/queue.sh ctl-a cand ctl-b > queue.log 2>&1 < /dev/null & disown
#   python3 -c 'import os,sys; os.setsid(); os.execvp(sys.argv[1], sys.argv[1:])' bash scripts/queue.sh ctl-a cand ctl-b > queue.log 2>&1 < /dev/null & disown
# Run from your experiment directory (the one holding configs/ and ledger.jsonl).
LOCK=${QUEUE_LOCK:-/tmp/inference-hillclimb.lock}
if command -v flock >/dev/null; then
  exec 9>"$LOCK"; flock 9
else  # macOS has no flock(1): mkdir is atomic, so a lock directory serializes callers
  until mkdir "$LOCK.d" 2>/dev/null; do sleep 2; done
  trap 'rmdir "$LOCK.d"' EXIT
  trap 'exit 130' INT TERM HUP
fi
for n in "$@"; do
  python3 "${BENCH:-$(dirname "$0")/bench.py}" run "configs/$n.json" ${BENCH_FLAGS:-} > "runs-$n.log" 2>&1
  echo "done $n: $(tail -c 300 "runs-$n.log" | tr '\n' ' ' | cut -c1-200)"
done
echo QUEUE_DONE "$@"
