#!/usr/bin/env bash
usage() {
	printf '%s\n' \
		'usage: worktree-audit.sh [-b|--base <ref>] [repo-path]' \
		'read-only: lists every worktree with size, age, merge state, uncommitted work, remote and pr state, last omp chat and a suggested bucket. it deletes nothing.' \
		'repo-path defaults to the current repo.' \
		'-b sets the ref the MERGED column checks against. default: origin/HEAD, then origin/main, then origin/master.' \
		'MERGED is YES only when a merged pr has this exact head; in-base means the head is in the base but no merged pr proves the work landed (a new worktree looks like this).' \
		'BUCKET is safe only for a clean worktree with MERGED YES; a missing folder is prune.' \
		'LAST_CHAT reads omp sessions only; it is "-" for chats from other harnesses.'
}
set -u

base=""
while [ $# -gt 0 ]; do
	case "$1" in
	-b|--base) [ $# -ge 2 ] || { echo "error: $1 needs a ref" >&2; exit 2; }; base="$2"; shift 2 ;;
	-h|--help) usage; exit 0 ;;
	-*) echo "error: unknown option: $1" >&2; exit 2 ;;
	*) break ;;
	esac
done

repo="${1:-$(git rev-parse --show-toplevel 2>/dev/null)}"
[ -z "$repo" ] && { echo "not in a git repo; pass a repo path" >&2; exit 1; }
cd "$repo" || exit 1
git rev-parse --git-dir >/dev/null 2>&1 || { echo "error: not a git repo: $repo" >&2; exit 1; }

wt_paths() { git worktree list --porcelain | awk '/^worktree /{ sub(/^worktree /, ""); print }'; }
main_wt=$(wt_paths | head -1)
prunable=$(git worktree list --porcelain | awk '/^worktree /{ sub(/^worktree /, ""); p = $0 } /^prunable/{ print p }')

if [ -z "$base" ]; then
	for cand in "$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null)" origin/main origin/master; do
		[ -n "$cand" ] && git rev-parse --verify --quiet "$cand^{commit}" >/dev/null && { base="$cand"; break; }
	done
	[ -z "$base" ] && { echo "error: no base ref (origin/HEAD, origin/main, origin/master all missing); pass -b <ref>" >&2; exit 1; }
	echo "warn: no -b given; MERGED checks against $base" >&2
fi

case "$base" in
origin/*) git fetch origin "+refs/heads/${base#origin/}:refs/remotes/$base" --quiet 2>/dev/null \
	|| echo "warn: could not fetch $base; merged column may be stale" >&2 ;;
esac
git rev-parse --verify --quiet "$base^{commit}" >/dev/null 2>&1 || { echo "error: base ref not found: $base" >&2; exit 1; }

if stat -c %Y / >/dev/null 2>&1; then
	stat_fmt=(-c '%Y %n'); fmt_day() { date -d "@$1" '+%Y-%m-%d'; }
else
	stat_fmt=(-f '%m %N'); fmt_day() { date -r "$1" '+%Y-%m-%d'; }
fi

for tool in gh jq rg; do
	command -v "$tool" >/dev/null 2>&1 || echo "warn: $tool not found; the PR or LAST_CHAT column reads '-'" >&2
done
prs=$(mktemp "${TMPDIR:-/tmp}/worktree-audit.XXXXXX") || { echo "error: cannot create a temp file" >&2; exit 1; }
if raw=$(gh pr list --author "@me" --state all --limit 1000 \
	--json number,state,headRefName,headRefOid 2>/dev/null); then
	printf '%s' "$raw" | jq '[.[] | {number, state: (.state | ascii_downcase), head: .headRefName, oid: .headRefOid}]' > "$prs" 2>/dev/null
elif command -v gh >/dev/null 2>&1; then
	echo "warn: gh pr list failed; the PR column reads '-'" >&2
fi
[ -s "$prs" ] || echo "[]" > "$prs"

sessions="$HOME/.omp/agent/sessions"
omp_slug() {
	case "$1" in
	"$HOME") printf '%s' '-' ;;
	"$HOME"/*) printf '%s' "${1#"$HOME"}" | tr '/' '-' ;;
	*) printf -- '--%s--' "$(printf '%s' "${1#/}" | tr '/' '-')" ;;
	esac
}
main_sessions="$sessions/$(omp_slug "$main_wt")"
now=$(date +%s)

echo "# base: $base"
printf "SIZE\tAGE\tMERGED\tDIRTY\tREMOTE\tPR\tLAST_CHAT\tBUCKET\tWORKTREE\n"

wt_paths | while IFS= read -r wt; do
	[ "$wt" = "$main_wt" ] && continue

	if printf '%s\n' "$prunable" | grep -qxF -- "$wt"; then
		printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" - - - missing - - - prune "$wt"
		continue
	fi

	size=$(du -sh "$wt" 2>/dev/null | awk '{print $1}')
	head=$(git -C "$wt" rev-parse HEAD 2>/dev/null)
	head_ts=$(git -C "$wt" log -1 --format='%ct' HEAD 2>/dev/null || echo 0)
	age=$([ "$head_ts" -gt 0 ] 2>/dev/null && echo "$(( (now - head_ts) / 86400 ))d" || echo "?")

	git merge-base --is-ancestor "$head" "$base" 2>/dev/null && merged=in-base || merged=no

	if ! porcelain=$(git -C "$wt" status --porcelain 2>/dev/null); then dirty=unknown
	elif [ -z "$porcelain" ]; then dirty=clean
	elif printf '%s\n' "$porcelain" | grep -qv '^??'; then
		dirty="wip:$(printf '%s\n' "$porcelain" | grep -cv '^??')"
	else dirty="scratch:$(printf '%s\n' "$porcelain" | grep -c '^??')"; fi

	branch=$(git -C "$wt" symbolic-ref --quiet --short HEAD 2>/dev/null || echo "")
	if [ -z "$branch" ]; then remote=detached
	elif git -C "$wt" show-ref --verify --quiet "refs/remotes/origin/$branch"; then
		counts=$(git -C "$wt" rev-list --left-right --count "HEAD...origin/$branch" 2>/dev/null)
		ahead=${counts%%[[:space:]]*}; behind=${counts##*[[:space:]]}
		if [ "$ahead" = 0 ] && [ "$behind" = 0 ]; then remote=pushed
		else remote="ahead$ahead/behind$behind"; fi
	else remote=no-remote; fi

	pr=$([ -n "$branch" ] && jq -r --arg b "$branch" \
		'.[] | select(.head==$b) | "#\(.number)/\(.state)"' "$prs" 2>/dev/null | head -1)
	[ -z "$pr" ] && pr="-"
	merged_pr=$([ -n "$branch" ] && jq -r --arg b "$branch" --arg h "$head" \
		'.[] | select(.head==$b and .state=="merged" and .oid==$h) | .number' "$prs" 2>/dev/null | head -1)
	[ -n "$merged_pr" ] && merged=YES

	last="-"; last_ts=0
	wt_sessions="$sessions/$(omp_slug "$wt")"
	f=$( {
		[ -d "$main_sessions" ] && rg -l -F -g '*.jsonl' -e "${wt}/" -e "${wt}\"" "$main_sessions" 2>/dev/null
		[ -d "$wt_sessions" ] && rg --files -g '*.jsonl' "$wt_sessions" 2>/dev/null
	} | tr '\n' '\0' | xargs -0 stat "${stat_fmt[@]}" 2>/dev/null | sort -rn | head -1)
	if [ -n "$f" ]; then last_ts=$(echo "$f" | awk '{print $1}')
		last=$(fmt_day "$last_ts" 2>/dev/null); fi
	recent=$([ "$last_ts" -gt 0 ] 2>/dev/null && [ $(( (now - last_ts) / 86400 )) -le 4 ] && echo yes || echo no)

	case "$dirty" in wip:*) bucket=hold-wip ;; scratch:*) bucket=hold-scratch ;; unknown) bucket=hold-unknown ;; *)
		case "$pr" in */open) bucket=hold-open-pr ;; *)
			if [ "$recent" = yes ]; then bucket=verify-recent-chat
			elif [ "$merged" = YES ]; then bucket=safe
			else bucket=review; fi ;;
		esac ;;
	esac

	printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
		"$size" "$age" "$merged" "$dirty" "$remote" "$pr" "$last" "$bucket" "$wt"
done | sort -t$'\t' -k1,1 -rh

rm -f "$prs"
