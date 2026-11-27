#!/usr/bin/env bash
# Print the real memory footprint (bytes) of a model server, for bench.py's memory watchdog.
#   mem.sh CONTAINER [unified]       containerised server: the container's processes + container anon memory
#   mem.sh --pid PID [unified]       native server: PID and all its descendants (pgrep -P) + their anon RSS
# Discrete NVIDIA GPU: sums nvidia-smi used memory of those processes + anon memory.
# Unified memory (Intel/AMD iGPU, Linux DRM drivers): sums drm-resident-* (deduplicated by drm-client-id)
# over those processes + anon memory. Reading other users' fdinfo needs root: run the watchdog
# with passwordless sudo for this script, or as root. Never embed a password here.
# A server that is not running prints 0.
set -euo pipefail
tree() { local k; echo "$1"; for k in $(pgrep -P "$1" 2>/dev/null || true); do tree "$k"; done; }
if [ "${1:-}" = --pid ]; then
  root=${2:?PID}; mode=${3:-auto}
  kill -0 "$root" 2>/dev/null || ps -p "$root" >/dev/null 2>&1 || { echo 0; exit 0; }
  pids=$(tree "$root" | tr '\n' ' ')
  anon=0
  for p in $pids; do
    if [ -r /proc/"$p"/status ]; then
      kb=$(awk '/^RssAnon:/{print $2}' /proc/"$p"/status 2>/dev/null || true)
    else
      kb=$(ps -o rss= -p "$p" 2>/dev/null | tr -d ' ' || true)
    fi
    anon=$((anon + ${kb:-0} * 1024))
  done
else
  c=${1:?container name or --pid PID}; mode=${2:-auto}
  pids=$(docker top "$c" -eo pid 2>/dev/null | tail -n +2 | tr '\n' ' ')
  [ -z "$pids" ] && { echo 0; exit 0; }
  cid=$(docker inspect -f '{{.Id}}' "$c")
  cg=$(ls -d /sys/fs/cgroup/system.slice/docker-"$cid".scope /sys/fs/cgroup/docker/"$cid" 2>/dev/null | head -1 || true)
  anon=$(awk '/^anon /{print $2}' "$cg/memory.stat" 2>/dev/null || echo 0)
fi
gpu=0
if [ "$mode" != unified ] && command -v nvidia-smi >/dev/null; then
  apps=$(nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader,nounits)
  for p in $pids; do
    m=$(echo "$apps" | awk -F', ' -v p="$p" '$1==p{s+=$2} END{print s+0}')
    gpu=$((gpu + m * 1048576))
  done
elif [ -d /proc/self/fdinfo ]; then
  declare -A seen
  for p in $pids; do
    for f in /proc/"$p"/fdinfo/*; do
      id=$(awk '/drm-client-id/{print $2}' "$f" 2>/dev/null) || continue
      [ -z "$id" ] && continue; [ -n "${seen[$id]:-}" ] && continue; seen[$id]=1
      kb=$(awk '/drm-resident-/{s+=$2} END{print s+0}' "$f"); gpu=$((gpu + kb * 1024))
    done
  done
fi
echo $((gpu + ${anon:-0}))
