#!/usr/bin/env bash
set -eu

tab="$(printf '\t')"
sep="$(printf '\037')"
home="${HOME:-}"
pending=""
agents_root=""
fm_closed="" fm_name=""

say() { printf '%-16s %s%s\n' "$1" "$2" "${3:+  $3}"; }

usage() { printf 'usage: name-scan.sh [--pending <skills-dir>] <harness>...  (claude code, codex, omp)\n' >&2; exit 2; }

record() { printf '%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" "$5" >>"$records"; }
hint() { printf '%s\n' "$1" >>"$hints"; }

read_frontmatter() {
	local out
	out="$(awk -v sep="$sep" '
		function clean(v) {
			sub(/^[^:]*:[[:space:]]*/, "", v)
			if (v ~ /^"/) { sub(/^"/, "", v); sub(/".*$/, "", v); return v }
			if (v ~ /^'\''/) { sub(/^'\''/, "", v); sub(/'\''.*$/, "", v); return v }
			sub(/[[:space:]]#.*$/, "", v)
			sub(/[[:space:]]+$/, "", v)
			return v
		}
		NR == 1 { if ($0 !~ /^---[[:space:]]*$/) exit; next }
		/^---[[:space:]]*$/ { closed = 1; exit }
		/^name:/ && !seen_name { seen_name = 1; name = clean($0); next }
		END { if (closed) printf "yes%s%s\n", sep, name }
	' "$1" 2>/dev/null)" || out=""
	fm_closed="" fm_name=""
	[ -n "$out" ] || return 0
	IFS="$sep" read -r fm_closed fm_name <<EOF
$out
EOF
}

owned_change() {
	local name="$1" raw listed recorded
	[ -f "$home/.agents/skills/.arkan-links" ] || return 1
	[ -L "$home/.agents/skills/$name" ] || return 1
	raw="$(readlink "$home/.agents/skills/$name")" || return 1
	while IFS="$tab" read -r listed recorded || [ -n "$listed" ]; do
		[ "$listed" = "$name" ] || continue
		if [ -d "$pending/$name" ]; then
			case "${raw%/}" in
				*/skills/"$name") printf '%s' "$pending/$name"; return 0 ;;
			esac
		elif [ "${raw%/}" = "${recorded%/}" ]; then
			return 0
		fi
		return 1
	done <"$home/.agents/skills/.arkan-links"
	return 1
}

modeled_dir() {
	local p="$1" parent raw replacement hops=0
	if [ -n "$pending" ] && [ -n "$agents_root" ]; then
		while [ "$hops" -lt 40 ]; do
			parent="$(cd -P -- "${p%/*}" 2>/dev/null && pwd -P)" || break
			p="$parent/${p##*/}"
			if [ "$parent" = "$agents_root" ] && replacement="$(owned_change "${p##*/}")"; then
				printf '%s' "$replacement"
				return 0
			fi
			[ -L "$p" ] || break
			raw="$(readlink "$p")" || break
			case "$raw" in /*) p="${raw%/}" ;; *) p="$parent/${raw%/}" ;; esac
			hops=$((hops + 1))
		done
	fi
	printf '%s' "$1"
}

add_skill() {
	local harness="$1" root="$2" entry_name="$3" dir="$4" canonical name
	canonical="$(cd -P -- "$dir" 2>/dev/null && pwd -P)" || canonical=""
	if [ -z "$canonical" ]; then
		hint "skill source $dir unreadable; not grouped"
		return 0
	fi
	read_frontmatter "$dir/SKILL.md"
	case "$harness" in
		codex)
			if [ "$fm_closed" != yes ]; then
				hint "codex skips $dir: SKILL.md has no frontmatter"
				return 0
			fi
			name="$(printf '%s' "$fm_name" | tr -s '[:space:]' ' ')"
			name="${name# }"
			name="${name% }"
			[ -n "$name" ] || name="${canonical##*/}"
			;;
		*)
			name="$fm_name"
			[ -n "$name" ] || name="$entry_name"
			;;
	esac
	record "$harness" plain "$name" "$canonical" "$root"
}

scan_entry() {
	local harness="$1" root="$2" entry_name="$3" dir="$4" file
	[ -d "$dir" ] || return 0
	if [ "$harness" = codex ]; then
		while IFS= read -r -d '' file; do
			add_skill codex "$root" "$entry_name" "${file%/SKILL.md}"
		done < <(find -L "$dir" -maxdepth 5 -name '.*' -prune -o -type f -name SKILL.md -print0 2>/dev/null)
		return 0
	fi
	[ -f "$dir/SKILL.md" ] || return 0
	add_skill "$harness" "$root" "$entry_name" "$dir"
}

scan_root() {
	local harness="$1" root="$2" entry dir
	[ -d "$root" ] || return 0
	for entry in "$root"/*; do
		[ -e "$entry" ] || [ -L "$entry" ] || continue
		if [ -L "$entry" ] && [ ! -e "$entry" ]; then
			hint "dangling skill link $entry; not grouped"
			continue
		fi
		dir="$(modeled_dir "$entry")"
		scan_entry "$harness" "$root" "${entry##*/}" "$dir"
	done
}

scan_incoming() {
	local harness="$1" src
	[ -n "$pending" ] || return 0
	[ -d "$pending" ] || return 0
	for src in "$pending"/*; do
		scan_entry "$harness" "$home/.agents/skills" "${src##*/}" "$src"
	done
}

scan_harness() {
	case "$1" in
		"claude code") scan_root "claude code" "$home/.claude/skills" ;;
		codex)
			scan_root codex "$home/.agents/skills"
			scan_root codex "${CODEX_HOME:-$home/.codex}/skills"
			scan_incoming codex
			;;
		omp)
			scan_root omp "$home/.agents/skills"
			scan_root omp "$home/.claude/skills"
			scan_root omp "$home/.codex/skills"
			scan_incoming omp
			;;
	esac
}

report() {
	awk -F "$tab" -v builtins=" simplify code-review security-review " '
		function append(list, item) { return list == "" ? item : list "; " item }
		{
			h = $1; ns = $2; name = $3; canon = $4; root = $5
			key = h SUBSEP ns SUBSEP name
			if (!(key in seenkey)) {
				seenkey[key] = 1
				order[++nkeys] = key
				hfor[key] = h; nsfor[key] = ns; namefor[key] = name
			}
			ck = key SUBSEP canon
			if (!(ck in seencanon)) {
				seencanon[ck] = 1
				canonfor[key, ++ncanon[key]] = canon
			}
			rk = ck SUBSEP root
			if (!(rk in seenroot)) {
				seenroot[rk] = 1
				rootfor[ck] = append(rootfor[ck], root)
			}
			sk = h SUBSEP canon
			if (!(sk in scanned)) { scanned[sk] = 1; nskills++ }
			harnessseen[h] = 1
		}
		END {
			clashes = 0
			for (i = 1; i <= nkeys; i++) {
				key = order[i]; h = hfor[key]; ns = nsfor[key]; name = namefor[key]
				if (ncanon[key] >= 2) {
					detail = h ": " name " from "
					for (j = 1; j <= ncanon[key]; j++) {
						c = canonfor[key, j]
						detail = detail (j > 1 ? " and " : "") c " (via " rootfor[key SUBSEP c] ")"
					}
					finding[++clashes] = detail
				}
				if (h == "claude code" && ns == "plain" && index(builtins, " " name " ") > 0) {
					c = canonfor[key, 1]
					finding[++clashes] = h ": " name " shadows built-in /" name " from " c " (via " rootfor[key SUBSEP c] ")"
				}
			}
			if (clashes > 0) {
				printf "%-16s %s%s\n", "names", "out-of-date", "  " clashes " clash(es)"
				for (i = 1; i <= clashes; i++) printf "  %s\n", finding[i]
			} else {
				nh = 0
				for (h in harnessseen) nh++
				printf "%-16s %s%s\n", "names", "ok", "  " nskills " skill(s), " nh " harness(es); no same-name sources"
			}
		}
	' "$records"
}

case "${1:-}" in
	--pending)
		pending="${2:-}"
		[ -n "$pending" ] || usage
		shift 2
		;;
	--pending=*)
		pending="${1#--pending=}"
		[ -n "$pending" ] || usage
		shift
		;;
esac

if [ -z "$home" ]; then
	say names skip "HOME is not set"
	exit 0
fi
[ "$#" -gt 0 ] || usage
if [ -n "$pending" ]; then
	pending="${pending%/}"
	agents_root="$(cd -P -- "$home/.agents/skills" 2>/dev/null && pwd -P)" || agents_root=""
fi

tmp="$(mktemp -d "${TMPDIR:-/tmp}/arkan-names.XXXXXX")"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
records="$tmp/records"
hints="$tmp/hints"
: >"$records"
: >"$hints"

unverified=""
for h in "$@"; do
	case "$h" in
		"claude code"|codex|omp) scan_harness "$h" ;;
		*) unverified="$unverified${unverified:+, }$h" ;;
	esac
done
if [ -n "$unverified" ]; then
	hint "unverified: $unverified; not scanned (the scan covers claude code, codex and omp)"
fi

if [ -s "$records" ]; then
	report
else
	say names skip "no sourced harness skill roots"
fi

detail=""
while IFS= read -r line; do
	[ -n "$line" ] || continue
	detail="$detail${detail:+; }$line"
done <"$hints"
if [ -n "$detail" ]; then say names hint "$detail"; fi
