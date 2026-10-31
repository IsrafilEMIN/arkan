#!/usr/bin/env bash
# setup.sh: the checks behind the pre-setup skill.
#   setup.sh check [repo-root]         one line per item: <item> <state> [detail]
#   setup.sh apply <item> [repo-root]  install one item that needs no choice
# states: ok, missing, out-of-date, hint (a pointer only), skip (does not apply here).
# check changes nothing. apply touches only local files; nothing here talks to a host.
set -eu

skill="$(cd "$(dirname "$0")/.." && pwd -P)"
refs="$skill/references"
# the arkan checkout this skill came from.
arkan="$(cd "$skill/../.." && pwd -P)"

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

say() { printf '%-16s %s%s\n' "$1" "$2" "${3:+  $3}"; }
has() { [ -f "$root/$1" ]; }
in_git() { git -C "$root" rev-parse --show-toplevel >/dev/null 2>&1; }

check_file() { if has "$2"; then say "$1" ok "$2"; else say "$1" missing "$2"; fi; }

omp_dir() {
	local dir=""
	if command -v omp >/dev/null 2>&1; then dir="$(omp config path 2>/dev/null)" || dir=""; fi
	printf '%s/skills' "${dir:-$HOME/.omp/agent}"
}

link_state() {
	local raw
	if [ -L "$1" ]; then
		raw="$(readlink "$1")"
		if [ "${raw%/}" = "$2" ]; then printf ok; else printf clash; fi
	elif [ -e "$1" ]; then
		printf clash
	else
		printf missing
	fi
}

stale_links() {
	local l
	for l in "$1"/*; do
		if [ -L "$l" ] && [ ! -e "$l" ]; then
			case "$(readlink "$l")" in "$arkan/skills/"*) printf '%s\n' "$l" ;; esac
		fi
	done
}

check_omp() {
	local dir src name l total=0 missing="" clash="" stale="" detail=""
	if [ -z "${HOME:-}" ]; then
		say omp skip "HOME is not set"
		return
	fi
	if [ ! -d "$arkan/skills" ]; then
		say omp skip "no skills/ in this checkout"
		return
	fi
	dir="$(omp_dir)"
	for src in "$arkan/skills"/*/; do
		name="${src%/}"
		name="${name##*/}"
		total=$((total + 1))
		case "$(link_state "$dir/$name" "$arkan/skills/$name")" in
			missing) missing="$missing${missing:+, }$name" ;;
			clash) clash="$clash${clash:+, }$name" ;;
		esac
	done
	while IFS= read -r l; do
		if [ -n "$l" ]; then stale="$stale${stale:+, }${l##*/}"; fi
	done <<EOF
$(stale_links "$dir")
EOF
	if [ -n "$missing" ]; then detail="not linked: $missing"; fi
	if [ -n "$stale" ]; then detail="$detail${detail:+; }stale: $stale"; fi
	if [ -n "$clash" ]; then
		say omp out-of-date "$dir; clash: $clash; left alone${detail:+; $detail}"
	elif [ -n "$missing" ]; then
		say omp missing "$dir; $detail; run setup.sh apply omp"
	elif [ -n "$stale" ]; then
		say omp out-of-date "$dir; $detail; run setup.sh apply omp"
	else
		say omp ok "$dir; $total skills linked"
	fi
}

apply_omp() {
	local dir src name l out
	if [ -z "${HOME:-}" ]; then
		printf 'setup: HOME is not set\n' >&2
		exit 2
	fi
	if [ ! -d "$arkan/skills" ]; then
		say omp skip "no skills/ in this checkout"
		return
	fi
	dir="$(omp_dir)"
	mkdir -p "$dir"
	while IFS= read -r l; do
		if [ -n "$l" ]; then
			rm -f "$l"
			printf 'setup: removed %s\n' "${l##*/}"
		fi
	done <<EOF
$(stale_links "$dir")
EOF
	for src in "$arkan/skills"/*/; do
		name="${src%/}"
		name="${name##*/}"
		if [ "$(link_state "$dir/$name" "$arkan/skills/$name")" = missing ]; then
			ln -s "$arkan/skills/$name" "$dir/$name"
			printf 'setup: linked %s\n' "$name"
		fi
	done
	out="$(check_omp)"
	printf '%s\n' "$out"
	case "$out" in *"clash: "*) exit 1 ;; esac
}

claude_detected() {
	[ -n "${HOME:-}" ] || return 1
	command -v claude >/dev/null 2>&1 || [ -d "$HOME/.claude" ]
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

tracker_kind() {
	local f="$root/docs/agents/issue-tracker.md" head
	[ -f "$f" ] || return 0
	head="$(grep -m1 '^# ' "$f" || true)"
	head="$(printf '%s' "$head" | tr '[:upper:]' '[:lower:]')"
	case "$head" in
		*"local markdown"*) printf local ;;
		*github*) printf github ;;
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
	check_omp
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
	if ls -d "$root"/.claude/skills/verify-* "$root"/.agents/skills/verify-* >/dev/null 2>&1; then
		say verify ok
	else
		say verify hint "no verify skill: run verification"
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
		claude-md)
			if claude_detected && has AGENTS.md && [ ! -e "$root/CLAUDE.md" ] && [ ! -L "$root/CLAUDE.md" ]; then
				ln -s AGENTS.md "$root/CLAUDE.md"
			fi
			;;
		omp) apply_omp; return ;;
		*)
			printf 'setup: %s needs a choice or is written by the skill; apply takes git, gitattributes, board, claude-md, omp\n' "$item" >&2
			exit 2
			;;
	esac
	# report the item's state after the write, so the caller sees it took effect.
	check | grep -E "^$item " || true
}

"$verb"
