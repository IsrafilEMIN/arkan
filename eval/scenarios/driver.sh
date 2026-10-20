#!/usr/bin/env bash
# usage: RUN_ROUND=<tag> driver.sh
# runs every scenario in order, one at a time. each round needs a new RUN_ROUND,
# because a run's trunk agent/run-<name>-<round> cannot be deleted or reused.
cd "$(dirname "$0")"
export RUN_MODEL="${RUN_MODEL:-claude-opus-5-5}"
export RUN_TIMEOUT="${RUN_TIMEOUT:-45m}"
runs="${RUNS_DIR:-${TMPDIR:-/tmp}/arkan-scenarios/runs}"
mkdir -p "$runs"
run() {
	local name="$1${RUN_ROUND:+-$RUN_ROUND}"; shift
	./run-one.sh "$name" "$@" >>"$runs/driver.log" 2>&1
	echo "$name exit $?" >>"$runs/driver.log"
}
run bug agent/pre-break "/arkan-mode do ticket value-report 01"
run feature agent/pre-break "/arkan-mode do ticket low-stock 01"
run security agent/pre-break "/arkan-mode do ticket tablet 02"
run style-nit agent/pre-break "/arkan-mode do ticket file-checks 01"
run review-loop agent/pre-break "/arkan-mode do ticket sku-matching 01"
run hidden-dep agent/pre-break "/arkan-mode do ticket tablet 03"
run post-merge main "/post-merge"
RUN_TIMEOUT=110m run long-run agent/pre-break "/arkan-mode run the stocktake spec in .scratch/stocktake/spec.md. I'm going to bed, keep going until it's done and I'll check in the morning."
echo ALL-DONE >>"$runs/driver.log"
