#!/usr/bin/env bash
set -eu

tab="$(printf '\t')"
home="${HOME:-}"
arkan="$(cd "$(dirname "$0")/../../.." && pwd -P)"

say() { printf '%-16s %s%s\n' "$1" "$2" "${3:+  $3}"; }

usage() { printf 'usage: name-scan.sh <harness>...  (claude code, codex, dsh, pi, omp, cursor, opencode, hermes)\n' >&2; exit 2; }

trim() {
	local s="$1"
	s="${s#"${s%%[![:space:]]*}"}"
	printf '%s' "${s%"${s##*[![:space:]]}"}"
}

expand_home() {
	case "$1" in
		"~") printf '%s' "$home" ;;
		"~/"*) printf '%s/%s' "$home" "${1#\~/}" ;;
		'$HOME') printf '%s' "$home" ;;
		'$HOME/'*) printf '%s/%s' "$home" "${1#\$HOME/}" ;;
		'${HOME}') printf '%s' "$home" ;;
		'${HOME}/'*) printf '%s/%s' "$home" "${1#\$\{HOME\}/}" ;;
		/*) printf '%s' "$1" ;;
	esac
}

dsh_agents_root() {
	local r="${DSH_AGENTS_HOME:-$home/.agents}"
	case "$r" in *[![:space:]]*) ;; *) r="$home/.agents" ;; esac
	case "$r" in
		"~") r="$home" ;;
		"~/"*) r="$home/${r#\~/}" ;;
		'$HOME') r="$home" ;;
		'$HOME/'*) r="$home/${r#\$HOME/}" ;;
	esac
	printf '%s' "${r%/}"
}

declared_name() {
	local value
	value="$(awk '
		NR == 1 { if ($0 != "---") exit; next }
		/^---[[:space:]]*$/ { exit }
		/^name:[[:space:]]*/ {
			sub(/^name:[[:space:]]*/, "")
			sub(/[[:space:]]#.*$/, "")
			sub(/[[:space:]]+$/, "")
			print
			exit
		}
	' "$1")"
	case "$value" in
		\"*\") value="${value#\"}"; value="${value%\"}" ;;
		\'*\') value="${value#\'}"; value="${value%\'}" ;;
	esac
	printf '%s' "$value"
}

hermes_dirs() {
	awk '
		/^[[:space:]]*external_dirs:[[:space:]]*/ {
			found = 1
			line = $0
			sub(/^[^:]*:[[:space:]]*/, "", line)
			if (line != "") print line
			next
		}
		found == 1 {
			if ($0 ~ /^[[:space:]]*-[[:space:]]*/) {
				line = $0
				sub(/^[[:space:]]*-[[:space:]]*/, "", line)
				print line
				next
			}
			if ($0 ~ /^[[:space:]]*(#|$)/) next
			exit
		}
	' "$1" 2>/dev/null || true
}

record() { printf '%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" "$5" >>"$records"; }
hint() { printf '%s\n' "$1" >>"$hints"; }

claude_plugin_installed() {
	local record="$home/.claude/plugins/installed_plugins.json" out f
	if command -v claude >/dev/null 2>&1; then
		out="$(claude plugin list --json 2>/dev/null)" || out=""
		if [ -n "$out" ]; then
			case "$out" in
				*'"arkan@arkan"'*) return 0 ;;
				*) return 1 ;;
			esac
		fi
	fi
	if [ -f "$record" ]; then
		grep -qF '"arkan@arkan"' "$record"
		return
	fi
	for f in "$home"/.claude/plugins/cache/arkan/arkan/*/; do
		if [ -f "$f/.claude-plugin/plugin.json" ]; then return 0; fi
	done
	return 1
}

scan_plugin() {
	local entry canonical name
	for entry in "$arkan"/skills/*; do
		[ -d "$entry" ] || continue
		[ -f "$entry/SKILL.md" ] || continue
		canonical="$(cd -P -- "$entry" 2>/dev/null && pwd -P)" || canonical=""
		[ -n "$canonical" ] || continue
		name="$(declared_name "$entry/SKILL.md")"
		[ -n "$name" ] || continue
		record "claude code" "plugin:arkan" "$name" "$canonical" "$arkan/skills"
	done
}

scan_root() {
	local harness="$1" root="$2" skip_system="$3" entry canonical name
	[ -n "$root" ] || return 0
	[ -d "$root" ] || return 0
	for entry in "$root"/*; do
		[ -e "$entry" ] || [ -L "$entry" ] || continue
		if [ "$skip_system" = 1 ] && [ "${entry##*/}" = .system ]; then continue; fi
		if [ -L "$entry" ] && [ ! -e "$entry" ]; then
			hint "dangling skill link $entry; not grouped"
			continue
		fi
		[ -d "$entry" ] || continue
		[ -f "$entry/SKILL.md" ] || continue
		canonical="$(cd -P -- "$entry" 2>/dev/null && pwd -P)" || canonical=""
		if [ -z "$canonical" ]; then
			hint "skill source $entry unreadable; not grouped"
			continue
		fi
		name="$(declared_name "$entry/SKILL.md")"
		if [ -z "$name" ]; then
			hint "skill without frontmatter name: $entry; not grouped"
			continue
		fi
		record "$harness" plain "$name" "$canonical" "$root"
	done
}

scan_hermes_dir() {
	local d path
	d="$(trim "$1")"
	d="${d#\[}"; d="${d%\]}"
	d="${d#\"}"; d="${d%\"}"
	d="${d#\'}"; d="${d%\'}"
	d="${d%/}"
	case "$d" in ""|"[]") return 0 ;; esac
	path="$(expand_home "$d")"
	if [ -z "$path" ]; then
		hint "hermes external dir $d unverified; not scanned"
		return 0
	fi
	scan_root hermes "$path" 0
}

scan_hermes() {
	local line part
	hint "hermes local skill root unverified; scanned skills.external_dirs only"
	if [ ! -f "$home/.hermes/config.yaml" ]; then return 0; fi
	while IFS= read -r line; do
		[ -n "$line" ] || continue
		case "$line" in
			*,*)
				while IFS= read -r part; do
					scan_hermes_dir "$part"
				done <<EOF
$(printf '%s\n' "$line" | tr ',' '\n')
EOF
				;;
			*) scan_hermes_dir "$line" ;;
		esac
	done <<EOF
$(hermes_dirs "$home/.hermes/config.yaml")
EOF
}

scan_harness() {
	case "$1" in
		"claude code")
			scan_root "claude code" "$home/.claude/skills" 0
			if claude_plugin_installed; then scan_plugin; fi
			;;
		codex)
			scan_root codex "$home/.agents/skills" 0
			scan_root codex "${CODEX_HOME:-$home/.codex}/skills" 1
			;;
		dsh) scan_root dsh "$(dsh_agents_root)/skills" 0 ;;
		pi) scan_root pi "$home/.agents/skills" 0 ;;
		omp)
			scan_root omp "$home/.agents/skills" 0
			scan_root omp "$home/.claude/skills" 0
			scan_root omp "$home/.codex/skills" 1
			;;
		cursor)
			scan_root cursor "$home/.agents/skills" 0
			scan_root cursor "$home/.claude/skills" 0
			scan_root cursor "$home/.codex/skills" 1
			;;
		opencode)
			scan_root opencode "$home/.agents/skills" 0
			scan_root opencode "$home/.claude/skills" 0
			;;
		hermes) scan_hermes ;;
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

if [ -z "$home" ]; then
	say names skip "HOME is not set"
	exit 0
fi
[ "$#" -gt 0 ] || usage
for h in "$@"; do
	case "$h" in
		"claude code"|codex|dsh|pi|omp|cursor|opencode|hermes) ;;
		*) say names skip "unknown harness $h; no sourced skill root"; exit 0 ;;
	esac
done

tmp="$(mktemp -d "${TMPDIR:-/tmp}/arkan-names.XXXXXX")"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
records="$tmp/records"
hints="$tmp/hints"
: >"$records"
: >"$hints"

for h in "$@"; do scan_harness "$h"; done

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
