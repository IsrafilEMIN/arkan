#!/usr/bin/env bash
# setup.sh: the checks behind the pre-setup skill.
#   setup.sh check [repo-root]         one line per item: <item> <state> [detail]
#   setup.sh apply <item> [repo-root]  install one item that needs no choice
# states: ok, missing, out-of-date, hint (a pointer only), skip (does not apply here).
# check changes nothing. apply touches only local files; nothing here talks to a host.
# name clashes plug in here with ticket 17.
set -eu

skill="$(cd "$(dirname "$0")/.." && pwd -P)"
refs="$skill/references"
# the arkan checkout or plugin copy this skill came from, for the ci files.
arkan="$(cd "$skill/../.." && pwd -P)"
ci="$arkan/ci/github"
home_skills="${HOME:-}/.agents/skills"
tab="$(printf '\t')"

usage() { printf 'usage: setup.sh check [repo-root] | setup.sh apply <item> [repo-root]\n' >&2; exit 2; }

verb=${1:-}
case "$verb" in
	check) shift; item="" ;;
	apply) shift; item=${1:-}; [ -n "$item" ] || usage; shift ;;
	*) usage ;;
esac
root=${1:-$(pwd -P)}
[ -d "$root" ] || { printf 'setup: no directory %s\n' "$root" >&2; exit 2; }
root="$(cd "$root" && pwd -P)"

# the ci workflow files pre-setup copies in: <item> <arkan file> <repo file>
ci_items="ci-review:arkan-review.yml ci-check:check.yml ci-risk:arkan-risk.yml ci-post-merge:arkan-post-merge.yml ci-merge:arkan-merge.yml"

say() { printf '%-16s %s%s\n' "$1" "$2" "${3:+  $3}"; }
has() { [ -f "$root/$1" ]; }
in_git() { git -C "$root" rev-parse --show-toplevel >/dev/null 2>&1; }

check_file() { if has "$2"; then say "$1" ok "$2"; else say "$1" missing "$2"; fi; }

manifest_version() {
	[ -f "$1" ] || return 0
	sed -n 's/^[[:space:]]*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$1" | head -n1
}

json_arkan_version() {
	local block v
	block="$(sed -n '/"arkan@arkan"/,/^[[:space:]]*}[[:space:]]*,*[[:space:]]*$/p')"
	v="$(printf '%s\n' "$block" | sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | sed -n '1p')"
	printf '%s' "$v"
}

arkan_version() {
	local v="" top=""
	top="$(git -C "$arkan" rev-parse --show-toplevel 2>/dev/null)" || top=""
	if [ -n "$top" ] && [ "$(canon_dir "$top")" = "$arkan" ]; then
		v="$(git -C "$arkan" describe --tags --always --dirty 2>/dev/null)" || v=""
		if [ -n "$v" ]; then
			printf '%s' "$v"
			return
		fi
	fi
	v="$(manifest_version "$arkan/.claude-plugin/plugin.json")"
	if [ -n "$v" ]; then
		printf '%s (plugin)' "$v"
		return
	fi
	printf 'unknown'
}

check_arkan() {
	local src name dest raw expected marker marker_names=" " total=0 notlinked=0 missing="" stale="" kept="" clash="" owned=0 elsewhere=0 others=0 other_copy="" detail=""
	if [ -z "${HOME:-}" ]; then
		say arkan skip "HOME is not set"
		return
	fi
	if [ ! -d "$arkan/skills" ]; then
		say arkan skip "no skills/ in this checkout"
		return
	fi
	marker="$home_skills/.arkan-links"
	if [ -f "$marker" ]; then
		while IFS="$tab" read -r name raw || [ -n "$name" ]; do
			case "$name" in ""|.|..|*/*) continue ;; esac
			marker_names="$marker_names$name "
		done <"$marker"
	fi
	for src in "$arkan/skills"/*; do
		if [ ! -d "$src" ]; then continue; fi
		total=$((total + 1))
		name=${src##*/}
		dest="$home_skills/$name"
		expected="$arkan/skills/$name"
		owned=0
		case "$marker_names" in *" $name "*) owned=1 ;; esac
		if [ -L "$dest" ]; then
			raw="$(readlink "$dest")" || raw=""
			case "$raw" in */) raw="${raw%/}" ;; esac
			if [ "$raw" = "$expected" ]; then
				continue
			fi
			if [ "$owned" = 1 ]; then
				case "$raw" in
					*/skills/"$name")
						elsewhere=$((elsewhere + 1))
						if [ -z "$other_copy" ]; then other_copy="${raw%/skills/"$name"}"; fi
						;;
					*) others=$((others + 1)) ;;
				esac
			else
				clash="$clash${clash:+, }$name"
			fi
		elif [ -e "$dest" ]; then
			clash="$clash${clash:+, }$name"
		else
			missing="$missing${missing:+, }$name"
			notlinked=$((notlinked + 1))
		fi
	done
	if [ -f "$marker" ]; then
		while IFS="$tab" read -r name raw || [ -n "$name" ]; do
			case "$name" in ""|.|..|*/*) continue ;; esac
			if [ -d "$arkan/skills/$name" ]; then continue; fi
			stale="$stale${stale:+, }$name"
			dest="$home_skills/$name"
			if [ ! -L "$dest" ] && [ -e "$dest" ]; then
				kept="$kept${kept:+, }$name"
			fi
		done <"$marker"
	fi
	if [ -n "$clash" ]; then
		say arkan out-of-date "clash: $clash; left alone"
	elif [ "$notlinked" -gt 0 ]; then
		detail="$notlinked of $total skills not linked: $missing"
		if [ "$elsewhere" -gt 0 ]; then
			detail="$detail; $elsewhere link(s) point to another arkan copy${other_copy:+ ($other_copy)}"
		fi
		if [ "$others" -gt 0 ]; then detail="$detail; $others link(s) point elsewhere; left alone"; fi
		say arkan missing "$detail; run setup.sh apply arkan"
	elif [ -n "$stale" ] || [ "$elsewhere" -gt 0 ] || [ "$others" -gt 0 ]; then
		if [ "$elsewhere" -gt 0 ]; then
			detail="$elsewhere link(s) point to another arkan copy${other_copy:+ ($other_copy)}"
		fi
		if [ "$others" -gt 0 ]; then detail="$detail${detail:+; }$others link(s) point elsewhere; left alone"; fi
		if [ -n "$stale" ]; then detail="$detail${detail:+; }stale: $stale"; fi
		if [ -n "$kept" ]; then detail="$detail${detail:+; }not a link: $kept; left alone"; fi
		say arkan out-of-date "$detail; run setup.sh apply arkan"
	else
		say arkan ok "version $(arkan_version); $total skills linked"
	fi
}

check_claude_plugin() {
	local record out cache f v
	if [ -z "${HOME:-}" ]; then
		say claude-plugin skip "HOME is not set"
		return
	fi
	record="$HOME/.claude/plugins/installed_plugins.json"
	if command -v claude >/dev/null 2>&1; then
		if out="$(claude plugin list --json 2>/dev/null)" && [ -n "$out" ]; then
			case "$out" in
				*'"arkan@arkan"'*)
					v="$(printf '%s\n' "$out" | json_arkan_version)"
					if [ -n "$v" ]; then
						say claude-plugin ok "version $v"
					else
						say claude-plugin ok installed
					fi
					;;
				*) say claude-plugin missing "run setup.sh apply claude-plugin" ;;
			esac
			return
		fi
	fi
	if [ -f "$record" ]; then
		if grep -qF '"arkan@arkan"' "$record"; then
			v="$(json_arkan_version <"$record")"
			if [ -n "$v" ]; then
				say claude-plugin ok "version $v"
			else
				say claude-plugin ok installed
			fi
		elif command -v claude >/dev/null 2>&1; then
			say claude-plugin missing "run setup.sh apply claude-plugin"
		else
			say claude-plugin skip "claude is not installed"
		fi
		return
	fi
	cache="$HOME/.claude/plugins/cache/arkan/arkan"
	for f in "$cache"/*/; do
		if [ ! -f "$f/.claude-plugin/plugin.json" ]; then continue; fi
		v="$(manifest_version "$f/.claude-plugin/plugin.json")"
		if [ -z "$v" ]; then
			v="${f%/}"
			v="${v##*/}"
		fi
		say claude-plugin ok "version $v"
		return
	done
	if command -v claude >/dev/null 2>&1; then
		say claude-plugin missing "run setup.sh apply claude-plugin"
	else
		say claude-plugin skip "claude is not installed"
	fi
}

plugin_record_ok() {
	local record f
	record="$HOME/.claude/plugins/installed_plugins.json"
	if [ -f "$record" ]; then
		grep -qF '"arkan@arkan"' "$record"
		return
	fi
	for f in "$HOME/.claude/plugins/cache/arkan/arkan"/*/; do
		if [ -f "$f/.claude-plugin/plugin.json" ]; then return 0; fi
	done
	return 1
}

claude_detected() {
	[ -n "${HOME:-}" ] || return 1
	if command -v claude >/dev/null 2>&1; then return 0; fi
	plugin_record_ok
}

check_harnesses() {
	local detected="" claude=0 detail="" hint=""
	if [ -z "${HOME:-}" ]; then
		say harnesses skip "HOME is not set"
		return
	fi
	if claude_detected; then
		detected="claude code"
		claude=1
	fi
	if [ -d "${CODEX_HOME:-$HOME/.codex}" ]; then detected="$detected${detected:+, }codex"; fi
	if [ -d "${DSH_HOME:-$HOME/.dsh}" ]; then
		detected="$detected${detected:+, }dsh"
		case "${DSH_AGENTS_HOME:-$HOME/.agents}" in
			"$HOME/.agents"|"$HOME/.agents/") ;;
			*) hint="${hint:+$hint; }dsh reads ${DSH_AGENTS_HOME%/}/skills, not ~/.agents/skills; unset DSH_AGENTS_HOME or point it at ~/.agents" ;;
		esac
	fi
	if [ -d "$HOME/.pi" ]; then detected="$detected${detected:+, }pi"; fi
	if [ -d "$HOME/.cursor" ]; then detected="$detected${detected:+, }cursor"; fi
	if [ -d "$HOME/.config/opencode" ] || command -v opencode >/dev/null 2>&1; then detected="$detected${detected:+, }opencode"; fi
	if command -v omp >/dev/null 2>&1; then detected="$detected${detected:+, }omp"; fi
	if [ -d "$HOME/.hermes" ]; then
		detected="$detected${detected:+, }hermes"
		if ! grep -q 'external_dirs' "$HOME/.hermes/config.yaml" 2>/dev/null || ! grep -q 'agents/skills' "$HOME/.hermes/config.yaml" 2>/dev/null; then
			hint="${hint:+$hint; }hermes needs a nested skills.external_dirs in ~/.hermes/config.yaml; see harnesses.md"
		fi
	fi
	if [ -z "$detected" ]; then
		say harnesses skip "no harness detected"
		return
	fi
	if [ "$claude" = 1 ] && ! plugin_record_ok; then
		say harnesses missing "claude code needs the plugin; run setup.sh apply claude-plugin"
		return
	fi
	detail="detected $detected"
	if [ "$claude" = 1 ]; then
		if [ "$detected" = "claude code" ]; then
			detail="$detail; claude code uses the plugin"
		else
			detail="$detail; claude code uses the plugin; reads ~/.agents/skills"
		fi
	else
		detail="$detail; reads ~/.agents/skills"
	fi
	if [ -n "$hint" ]; then
		say harnesses hint "$detail; $hint"
	else
		say harnesses ok "$detail"
	fi
}

check_claude_md() {
	if ! claude_detected; then
		say claude-md skip "claude code is not detected"
		return
	fi
	if ! has AGENTS.md; then
		say claude-md skip "no AGENTS.md"
		return
	fi
	if [ -e "$root/CLAUDE.md" ] || [ -L "$root/CLAUDE.md" ]; then
		say claude-md ok CLAUDE.md
		return
	fi
	say claude-md missing "CLAUDE.md -> AGENTS.md"
}

apply_claude_plugin() {
	if ! command -v claude >/dev/null 2>&1; then
		say claude-plugin skip "claude is not installed"
		return
	fi
	if ! claude plugin marketplace add "$arkan"; then
		printf 'setup: claude plugin marketplace add failed\n' >&2
		exit 1
	fi
	if ! claude plugin install arkan@arkan; then
		printf 'setup: claude plugin install failed\n' >&2
		exit 1
	fi
	check_claude_plugin
}

marker_target() {
	local n raw
	while IFS="$tab" read -r n raw || [ -n "$n" ]; do
		if [ "$n" = "$2" ]; then printf '%s' "$raw"; return 0; fi
	done <"$1"
}

apply_arkan() {
	local src name dest raw live recorded expected marker marker_names=" " linked=0 removed=0 clashes=0 owned=0 keep=0 linked_names="" removed_names="" new="" summary="" tmp_marker="" marker_existed=0 marker_changed=0 line_target=""
	if [ -z "${HOME:-}" ]; then
		printf 'setup: HOME is not set\n' >&2
		exit 2
	fi
	if [ ! -d "$arkan/skills" ]; then
		say arkan skip "no skills/ in this checkout"
		return
	fi
	mkdir -p "$home_skills"
	marker="$home_skills/.arkan-links"
	if [ -f "$marker" ]; then
		marker_existed=1
		while IFS="$tab" read -r name raw || [ -n "$name" ]; do
			case "$name" in ""|.|..|*/*) continue ;; esac
			marker_names="$marker_names$name "
		done <"$marker"
	fi
	for src in "$arkan/skills"/*; do
		if [ ! -d "$src" ]; then continue; fi
		name=${src##*/}
		dest="$home_skills/$name"
		expected="$arkan/skills/$name"
		line_target="$expected"
		owned=0
		case "$marker_names" in *" $name "*) owned=1 ;; esac
		keep=0
		if [ -L "$dest" ]; then
			raw="$(readlink "$dest")" || raw=""
			case "$raw" in */) raw="${raw%/}" ;; esac
			if [ "$raw" = "$expected" ]; then
				keep=$owned
			elif [ "$owned" = 1 ]; then
				case "$raw" in
					*/skills/"$name")
						ln -sfn "$expected" "$dest"
						linked=$((linked + 1))
						linked_names="$linked_names${linked_names:+, }$name"
						keep=1
						;;
					*)
						printf 'setup: clash: %s is not a link to %s; left alone\n' "$dest" "$expected" >&2
						clashes=$((clashes + 1))
						recorded="$(marker_target "$marker" "$name")"
						line_target="${recorded:-$expected}"
						keep=1
						;;
				esac
			else
				printf 'setup: clash: %s is not a link to %s; left alone\n' "$dest" "$expected" >&2
				clashes=$((clashes + 1))
			fi
		elif [ -e "$dest" ]; then
			printf 'setup: clash: %s is not a link to %s; left alone\n' "$dest" "$expected" >&2
			clashes=$((clashes + 1))
			keep=$owned
		else
			ln -s "$expected" "$dest"
			linked=$((linked + 1))
			linked_names="$linked_names${linked_names:+, }$name"
			keep=1
		fi
		if [ "$keep" = 1 ]; then
			new="$new$name"$'\t'"$line_target"$'\n'
		fi
	done
	if [ -f "$marker" ]; then
		while IFS="$tab" read -r name raw || [ -n "$name" ]; do
			case "$name" in ""|.|..|*/*) continue ;; esac
			if [ -d "$arkan/skills/$name" ]; then continue; fi
			dest="$home_skills/$name"
			if [ -L "$dest" ]; then
				live="$(readlink "$dest")" || live=""
				case "$live" in */) live="${live%/}" ;; esac
				recorded="$raw"
				case "$recorded" in */) recorded="${recorded%/}" ;; esac
				if [ "$live" = "$recorded" ]; then
					rm -f "$dest"
					removed=$((removed + 1))
					removed_names="$removed_names${removed_names:+, }$name"
				else
					printf "setup: stale: %s (not arkan's link; left alone)\n" "$name" >&2
				fi
			elif [ -e "$dest" ]; then
				printf 'setup: stale: %s (not a link; left alone)\n' "$name" >&2
			else
				printf 'setup: stale: %s (no link; left alone)\n' "$name" >&2
			fi
		done <"$marker"
	fi
	if [ -n "$new" ]; then
		if [ "$marker_existed" = 0 ]; then
			marker_changed=1
		else
			tmp_marker="$(mktemp)"
			printf '%s' "$new" >"$tmp_marker"
			if ! cmp -s "$marker" "$tmp_marker"; then marker_changed=1; fi
			rm -f "$tmp_marker"
		fi
		printf '%s' "$new" >"$marker"
	else
		if [ "$marker_existed" = 1 ]; then marker_changed=1; fi
		rm -f "$marker"
	fi
	if [ "$linked" -gt 0 ]; then summary="linked $linked ($linked_names)"; fi
	if [ "$removed" -gt 0 ]; then summary="$summary${summary:+; }removed $removed ($removed_names)"; fi
	if [ "$marker_changed" = 1 ]; then summary="$summary${summary:+; }marker updated"; fi
	if [ "$clashes" -gt 0 ]; then
		if [ "$clashes" = 1 ]; then
			summary="$summary${summary:+; }1 clash"
		else
			summary="$summary${summary:+; }$clashes clashes"
		fi
	fi
	if [ -z "$summary" ]; then
		printf 'setup: nothing changed; version %s\n' "$(arkan_version)"
	else
		printf 'setup: %s; version %s\n' "$summary" "$(arkan_version)"
	fi
	[ "$clashes" = 0 ] || exit 1
}

file_hash() { # path
	if command -v sha256sum >/dev/null 2>&1; then
		sha256sum "$1" | cut -d' ' -f1
	elif command -v shasum >/dev/null 2>&1; then
		shasum -a 256 "$1" | cut -d' ' -f1
	elif command -v cksum >/dev/null 2>&1; then
		cksum "$1" | cut -d' ' -f1
	else
		printf 'setup: no sha256sum, shasum or cksum\n' >&2
		return 1
	fi
}

body_hash() { # path: the hash with every arkan-copy line removed
	local tmp
	tmp="$(mktemp)"
	grep -vE '^# arkan-copy: [0-9a-f]+$' "$1" >"$tmp" || true
	file_hash "$tmp"
	rm -f "$tmp"
}

stamp_of() { # path
	awk '/^# arkan-copy: [0-9a-f]+$/ { print substr($0, 15); exit }' "$1"
}

merge_path() {
	local f="$root/docs/agents/approvals.md" broker="" gate=""
	[ -f "$f" ] || return 0
	if grep -qxF '**Merge path:** broker' "$f"; then broker=1; fi
	if grep -qxF '**Merge path:** gate' "$f"; then gate=1; fi
	if [ -n "$broker" ] && [ -n "$gate" ]; then
		printf 'both'
	elif [ -n "$broker" ]; then
		printf 'broker'
	elif [ -n "$gate" ]; then
		printf 'gate'
	fi
}

tracker_kind() {
	local f="$root/docs/agents/issue-tracker.md" head
	[ -f "$f" ] || return 0
	head="$(grep -m1 '^# ' "$f" || true)"
	head="$(printf '%s' "$head" | tr '[:upper:]' '[:lower:]')"
	case "$head" in
		*"local markdown"*) printf local ;;
		*github*) printf github ;;
		*gitlab*) printf gitlab ;;
		*) printf other ;;
	esac
}

check_tracker() {
	local out line rel bad=0 total=0 problems=0 seen=" " shown=0 first="" detail=""
	if ! has docs/agents/issue-tracker.md; then
		say tracker missing docs/agents/issue-tracker.md
		return
	fi
	if [ "$(tracker_kind)" != local ]; then
		say tracker ok docs/agents/issue-tracker.md
		return
	fi
	if [ ! -d "$root/.scratch" ]; then
		say tracker out-of-date "no .scratch/; run setup.sh apply board"
		return
	fi
	if out="$("$skill/scripts/board.sh" fields "$root" 2>&1)"; then
		say tracker ok docs/agents/issue-tracker.md
		return
	fi
	total="$(find "$root/.scratch" -type f \( -path '*/issues/*.md' -o -name spec.md \) 2>/dev/null | wc -l | tr -d ' ')"
	while IFS= read -r line; do
		case "$line" in
			.scratch/*) ;;
			*) continue ;;
		esac
		problems=$((problems + 1))
		rel="${line%%: *}"
		case "$seen" in
			*" $rel "*) ;;
			*) seen="$seen$rel "; bad=$((bad + 1)) ;;
		esac
		if [ $shown -lt 3 ]; then
			first="$first$line"$'\n'
			shown=$((shown + 1))
		fi
	done <<<"$out"
	if [ $problems = 0 ]; then
		detail="$(printf '%s\n' "$out" | head -n1)"
		detail="${detail#fields: }"
		[ -n "$detail" ] || detail="board.sh fields failed"
		say tracker out-of-date "$detail; fix the tickets first"
		return
	fi
	say tracker out-of-date "$bad of $total files break the contract: $problems problem(s)"
	while IFS= read -r line; do
		if [ -n "$line" ]; then printf '  %s\n' "$line"; fi
	done <<<"$first"
}

check_board() {
	local out count detail
	if ! has TODO.md; then
		say board missing TODO.md
		return
	fi
	if in_git && git -C "$root" check-ignore -q --no-index TODO.md; then
		say board missing "TODO.md is git-ignored"
		return
	fi
	if [ "$(tracker_kind)" != local ]; then
		say board ok TODO.md
		return
	fi
	if [ ! -d "$root/.scratch" ]; then
		say board out-of-date "no .scratch/; run setup.sh apply board"
		return
	fi
	if out="$("$skill/scripts/board.sh" check "$root" 2>&1)"; then
		case "$out" in
			*"check-board: ok"*) say board ok TODO.md ;;
			*) say board out-of-date "board.sh check did not print ok" ;;
		esac
		return
	fi
	count="$(printf '%s\n' "$out" | sed -n 's/^check-board: \([0-9][0-9]*\) problem(s)$/\1/p' | head -n1)"
	if [ -n "$count" ]; then
		detail="$count problem(s)"
	else
		detail="$(printf '%s\n' "$out" | sed -n 's/^check-board: //p' | head -n1)"
		detail="${detail%:}"
		[ -n "$detail" ] || detail="board.sh check failed"
	fi
	if "$skill/scripts/board.sh" fields "$root" >/dev/null 2>&1; then
		say board out-of-date "$detail; run board.sh build"
	else
		say board out-of-date "$detail; fix the tickets first, then run board.sh build"
	fi
}

agents_board_line() {
	awk '
		/^## / { block = ($0 == "## Agent skills"); next }
		block && /board\.sh build/ && /board\.sh check/ { found = 1 }
		END { exit !found }
	' "$root/AGENTS.md"
}

# the repo's own workflow files: every .yml/.yaml in .github/workflows/ that is not arkan's.
own_ci() {
	local f out=""
	for f in "$root"/.github/workflows/*.yml "$root"/.github/workflows/*.yaml; do
		[ -f "$f" ] || continue
		case "${f##*/}" in arkan-*.yml | check.yml) continue ;; esac
		out="$out${out:+, }${f##*/}"
	done
	printf '%s' "$out"
}

check_ci() {
	local name=$1 src=$2 dst=".github/workflows/$2" repo="$root/.github/workflows/$2" want
	if [ ! -f "$ci/$src" ]; then
		say "$name" skip "arkan's ci/github/$src not found next to this skill"
	elif ! has "$dst"; then
		if [ "$name" = ci-check ] && [ -n "$(own_ci)" ]; then
			say "$name" hint "the repo runs its own ci ($(own_ci)); keep it, or copy $src"
		else
			say "$name" missing "$dst"
		fi
	else
		want="$(file_hash "$ci/$src")"
		if [ "$(body_hash "$repo")" = "$want" ]; then
			say "$name" ok "$dst"
		elif [ "$(stamp_of "$repo")" = "$want" ]; then
			say "$name" ok "$dst customized"
		else
			say "$name" out-of-date "$dst differs from $ci/$src; update it and merge the repo's settings"
		fi
	fi
}

check_merge() {
	local dst=".github/workflows/arkan-merge.yml" mode
	mode="$(merge_path)"
	case "$mode" in
		broker)
			if has "$dst"; then
				say ci-merge out-of-date "$dst is installed, but docs/agents/approvals.md records **Merge path:** broker; remove it, or record gate"
			else
				say ci-merge ok "broker (docs/agents/approvals.md)"
			fi
			;;
		gate) check_ci ci-merge arkan-merge.yml ;;
		both) say ci-merge out-of-date "docs/agents/approvals.md records both merge paths; keep one line" ;;
		*)
			if has "$dst"; then
				check_ci ci-merge arkan-merge.yml
			else
				say ci-merge missing "choose gate or broker; record **Merge path:** gate or **Merge path:** broker in docs/agents/approvals.md"
			fi
			;;
	esac
}

canon_dir() {
	if [ -d "$1" ]; then
		cd -- "$1" && pwd -P
		return
	fi
	local parent base
	parent=$(dirname "$1")
	base=$(basename "$1")
	if [ -d "$parent" ]; then
		printf '%s/%s\n' "$(cd -- "$parent" && pwd -P)" "$base"
	else
		printf '%s\n' "$1"
	fi
}

repo_hooks_dir() {
	local path top common
	top=$(git -C "$root" rev-parse --show-toplevel)
	top=$(canon_dir "$top")
	if path="$(git -C "$root" config --local --path --get core.hooksPath 2>/dev/null)" && [ -n "$path" ]; then
		case "$path" in
			/*) ;;
			*) path="$top/$path" ;;
		esac
	else
		common=$(git -C "$root" rev-parse --git-common-dir)
		case "$common" in
			/*) ;;
			*) common="$top/$common" ;;
		esac
		path="$common/hooks"
	fi
	canon_dir "$path"
}

common_hooks_dir() {
	local top common
	top=$(git -C "$root" rev-parse --show-toplevel)
	top=$(canon_dir "$top")
	common=$(git -C "$root" rev-parse --git-common-dir)
	case "$common" in
		/*) ;;
		*) common="$top/$common" ;;
	esac
	canon_dir "$common/hooks"
}

git_hooks_dir() {
	local path
	path="$(git -C "$root" rev-parse --git-path hooks)"
	case "$path" in
		/*) ;;
		*) path="$root/$path" ;;
	esac
	canon_dir "$path"
}

hook_covers() { # language hook-file: a non-comment line names that language's tool
	local lines
	lines="$(grep -v '^[[:space:]]*#' "$2" 2>/dev/null)" || true
	case "$1" in
		rust) printf '%s\n' "$lines" | grep -qE '(^|[[:space:];&|(/])(cargo[[:space:]]+(fmt|clippy)|rustfmt)([[:space:]]|$)' ;;
		python) printf '%s\n' "$lines" | grep -qE '(^|[[:space:];&|(/])ruff([[:space:]]|$)' ;;
		go) printf '%s\n' "$lines" | grep -qE '(^|[[:space:];&|(/])(gofmt|go[[:space:]]+vet)([[:space:]]|$)' ;;
		js/ts) printf '%s\n' "$lines" | grep -qE '(^|[[:space:];&|(/])lint-staged([[:space:]]|$)' ;;
		*) return 1 ;;
	esac
}

check() {
	check_arkan
	check_claude_plugin
	check_harnesses
	if in_git; then say git ok; else say git missing "not a git repo"; fi
	check_tracker
	check_file labels docs/agents/triage-labels.md
	check_file domain docs/agents/domain.md
	if has .gitattributes && grep -qx 'GLOSSARY.md merge=union' "$root/.gitattributes"; then
		say gitattributes ok
	else
		say gitattributes missing "GLOSSARY.md merge=union"
	fi
	if ! has AGENTS.md || ! grep -qx '## Agent skills' "$root/AGENTS.md"; then
		say agents-block missing "## Agent skills in AGENTS.md"
	elif [ "$(tracker_kind)" = local ] && ! agents_board_line; then
		say agents-block out-of-date "add this line under ### Board in ## Agent skills:"
		printf '  %s\n' "Do not edit \`TODO.md\` by hand: run the \`pre-setup\` skill's \`scripts/board.sh build\` from the repo root, then \`scripts/board.sh check\`; it must print \`ok\`."
	else
		say agents-block ok AGENTS.md
	fi
	check_claude_md
	check_board
	check_file sensitive-paths docs/agents/sensitive-paths.md
	check_file approvals docs/agents/approvals.md
	check_file review-md REVIEW.md
	local pair
	for pair in $ci_items; do
		if [ "${pair%%:*}" = ci-merge ]; then
			check_merge
		else
			check_ci "${pair%%:*}" "${pair#*:}"
		fi
	done
	check_file codeowners .github/CODEOWNERS
	if ls -d "$root"/.claude/skills/*verif* "$root"/.agents/skills/*verif* >/dev/null 2>&1; then
		say verify ok
	else
		say verify hint "no verify skill: run create-verification"
	fi
	local langs="" target="" common="" effective="" hook_file="" husky=0 missing="" lang covered=0 covered_any=0
	has Cargo.toml && langs="$langs rust"
	has pyproject.toml && langs="$langs python"
	has go.mod && langs="$langs go"
	has package.json && langs="$langs js/ts"
	if [ -z "$langs" ]; then
		say hooks skip "no Cargo.toml, pyproject.toml, go.mod or package.json"
	elif in_git; then
		target="$(repo_hooks_dir)"
		common="$(common_hooks_dir)"
		effective="$(git_hooks_dir)"
		if [ "$target" != "$effective" ] && ! { [ "$target" = "$common" ] && [ -x "$effective/pre-commit" ] && grep -q 'git-common-dir' "$effective/pre-commit" 2>/dev/null; }; then
			say hooks out-of-date "git uses $effective, so $target/pre-commit will not run; change the hooks path or add a delegating hook"
		else
			hook_file="$target/pre-commit"
			if [ ! -x "$hook_file" ]; then hook_file=""; fi
			if [ -f "$root/.husky/pre-commit" ]; then husky=1; fi
			for lang in $langs; do
				covered=0
				if [ -n "$hook_file" ] && hook_covers "$lang" "$hook_file"; then covered=1; fi
				if [ "$lang" = js/ts ] && [ "$husky" = 1 ]; then covered=1; fi
				if [ "$covered" = 1 ]; then covered_any=1; else missing="$missing $lang"; fi
			done
			if [ -z "$missing" ]; then
				say hooks ok
			elif [ "$covered_any" = 0 ] && [ -n "$hook_file" ]; then
				say hooks hint "hook exists but does not name ${langs# }: run setup-pre-commit or check its config"
			else
				say hooks hint "no commit hook for${missing}: run setup-pre-commit"
			fi
		fi
	else
		say hooks hint "no commit hook for${langs}: run setup-pre-commit"
	fi
}

append_line() { # file line: add the line once
	local f="$root/$1"
	if [ -f "$f" ] && grep -qxF "$2" "$f"; then return; fi
	if [ -s "$f" ] && [ -n "$(tail -c1 "$f")" ]; then printf '\n' >>"$f"; fi
	printf '%s\n' "$2" >>"$f"
}

seed() { # repo file, reference file: copy only when the repo file is missing
	if has "$1"; then return; fi
	mkdir -p "$(dirname "$root/$1")"
	cp "$refs/$2" "$root/$1"
}

apply() {
	case "$item" in
		git) in_git || git -C "$root" init -q ;;
		gitattributes) append_line .gitattributes 'GLOSSARY.md merge=union' ;;
		board)
			if [ "$(tracker_kind)" = local ]; then mkdir -p "$root/.scratch"; fi
			seed TODO.md todo.md
			if has .gitignore; then
				local tmp
				tmp="$(mktemp)"
				grep -vxE '/?TODO\.md' "$root/.gitignore" >"$tmp" || true
				cat "$tmp" >"$root/.gitignore"
				rm -f "$tmp"
			fi
			;;
		approvals) seed docs/agents/approvals.md approvals.md ;;
		review-md) seed REVIEW.md review.md ;;
		claude-md)
			if claude_detected && has AGENTS.md && [ ! -e "$root/CLAUDE.md" ] && [ ! -L "$root/CLAUDE.md" ]; then
				ln -s AGENTS.md "$root/CLAUDE.md"
			fi
			;;
		arkan) apply_arkan; return ;;
		claude-plugin) apply_claude_plugin; return ;;
		ci-review | ci-check | ci-risk | ci-post-merge | ci-merge)
			local pair src="" mode=""
			if [ "$item" = ci-merge ]; then
				mode="$(merge_path)"
				if [ "$mode" = broker ]; then
					check_merge
					return
				fi
				if [ "$mode" = both ]; then
					printf 'setup: docs/agents/approvals.md records both merge paths; keep one before installing a gate\n' >&2
					exit 2
				fi
				if [ "$mode" != gate ]; then
					printf 'setup: record **Merge path:** gate in docs/agents/approvals.md before installing the gate\n' >&2
					exit 2
				fi
			fi
			for pair in $ci_items; do [ "${pair%%:*}" = "$item" ] && src="${pair#*:}"; done
			[ -f "$ci/$src" ] || { printf 'setup: %s not found\n' "$ci/$src" >&2; exit 1; }
			mkdir -p "$root/.github/workflows"
			local want
			want="$(file_hash "$ci/$src")" || exit 1
			cp "$ci/$src" "$root/.github/workflows/$src"
			printf '# arkan-copy: %s\n' "$want" >>"$root/.github/workflows/$src"
			;;
		*)
			printf 'setup: %s needs a choice or is written by the skill; apply takes git, gitattributes, board, approvals, review-md, claude-md, arkan, claude-plugin, ci-review, ci-check, ci-risk, ci-post-merge, ci-merge\n' "$item" >&2
			exit 2
			;;
	esac
	# report the item's state after the write, so the caller sees it took effect.
	check | grep -E "^$item " || true
}

"$verb"
