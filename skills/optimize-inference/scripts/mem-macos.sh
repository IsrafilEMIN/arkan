#!/usr/bin/env bash
# Print the real memory footprint (bytes) of a native macOS model server, for bench.py's memory watchdog.
#   bash scripts/mem-macos.sh PORT
# Sums phys_footprint (from `footprint`) over the processes listening on PORT and their descendants, so
# runner subprocesses (Ollama, LM Studio) count too. phys_footprint includes Metal buffers on unified
# memory, also GPU-only ones; `ps` RSS misses buffers the CPU never touched. Another user's server
# needs root. On any failure: reason on stderr, nothing on stdout, non-zero exit.
set -euo pipefail
port=${1:?port}
fail() { echo "mem-macos.sh: $*" >&2; exit 1; }
listeners=$(lsof -nP -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null | sort -u) || true
[ -n "$listeners" ] || fail "no process listening on TCP port $port"
pids=$(ps -axo pid=,ppid= | awk -v roots="$listeners" '
  BEGIN { n = split(roots, r); for (i = 1; i <= n; i++) keep[r[i]] = 1 }
  { parent[$1] = $2 }
  END {
    do { grew = 0; for (p in parent) if (!(p in keep) && (parent[p] in keep)) { keep[p] = 1; grew = 1 } } while (grew)
    for (p in keep) print p
  }')
args=()
for p in $pids; do args+=(-p "$p"); done
out=$(footprint -f bytes --noCategories "${args[@]}" 2>&1) || fail "footprint failed: $out"
total=$(awk -v want="$(echo "$pids" | wc -w)" '
  /^[[:space:]]*phys_footprint:[[:space:]]+[0-9]+ B$/ { s += $2; n++ }
  END { if (n == want) print s }' <<<"$out")
[ -n "$total" ] || fail "could not parse footprint output for pids $(echo $pids): $out"
echo "$total"
