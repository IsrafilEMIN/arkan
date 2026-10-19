#!/usr/bin/env bash
# setup.sh: the checks behind the pre-setup skill.
#   setup.sh check [repo-root]         one line per item: <item> <state> [detail]
#   setup.sh apply <item> [repo-root]  install one item that needs no choice
# states: ok, missing, out-of-date, hint (a pointer only), skip (does not apply here).
# check changes nothing. apply touches only local files; nothing here talks to a host.
# machine items (arkan installed, harnesses, name clashes) plug in here with tickets 04, 06 and 17.
set -eu

skill="$(cd "$(dirname "$0")/.." && pwd -P)"
refs="$skill/references"
# the arkan checkout or plugin copy this skill came from, for the ci files.
arkan="$(cd "$skill/../.." && pwd -P)"
ci="$arkan/ci/github"

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
	local name=$1 src=$2 dst=".github/workflows/$2"
	if [ ! -f "$ci/$src" ]; then
		say "$name" skip "arkan's ci/github/$src not found next to this skill"
	elif ! has "$dst"; then
		if [ "$name" = ci-check ] && [ -n "$(own_ci)" ]; then
			say "$name" hint "the repo runs its own ci ($(own_ci)); keep it, or copy $src"
		else
			say "$name" missing "$dst"
		fi
	elif cmp -s "$ci/$src" "$root/$dst"; then
		say "$name" ok "$dst"
	else
		say "$name" out-of-date "$dst differs from $ci/$src"
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

check() {
	if in_git; then say git ok; else say git missing "not a git repo"; fi
	check_file tracker docs/agents/issue-tracker.md
	check_file labels docs/agents/triage-labels.md
	check_file domain docs/agents/domain.md
	if has .gitattributes && grep -qx 'GLOSSARY.md merge=union' "$root/.gitattributes"; then
		say gitattributes ok
	else
		say gitattributes missing "GLOSSARY.md merge=union"
	fi
	if has AGENTS.md && grep -qx '## Agent skills' "$root/AGENTS.md"; then
		say agents-block ok AGENTS.md
	else
		say agents-block missing "## Agent skills in AGENTS.md"
	fi
	if ! has TODO.md; then
		say board missing TODO.md
	elif in_git && git -C "$root" check-ignore -q --no-index TODO.md; then
		say board missing "TODO.md is git-ignored"
	else
		say board ok TODO.md
	fi
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
	if ! has package.json; then
		say hooks skip "not a js/ts repo"
	elif [ -d "$root/.husky" ] || { in_git && git -C "$root" config core.hooksPath >/dev/null; }; then
		say hooks ok
	else
		say hooks hint "js/ts repo with no commit hooks: run setup-pre-commit"
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
			cp "$ci/$src" "$root/.github/workflows/$src"
			;;
		*)
			printf 'setup: %s needs a choice or is written by the skill; apply takes git, gitattributes, board, approvals, review-md, ci-review, ci-check, ci-risk, ci-post-merge, ci-merge\n' "$item" >&2
			exit 2
			;;
	esac
	# report the item's state after the write, so the caller sees it took effect.
	check | grep -E "^$item " || true
}

"$verb"
