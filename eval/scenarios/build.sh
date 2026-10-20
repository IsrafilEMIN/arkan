#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd "$(dirname "$0")" && pwd)
arkan_root=$(cd "$script_dir/../.." && pwd)
seed="$script_dir/sandbox/history.bundle"
build_name="arkan sandbox build"
build_email="sandbox@arkan.invalid"
build_date="2026-10-18T20:10:00Z"

usage() {
	printf 'usage: build.sh build <destination>\n       build.sh refresh <checkout> [base]\n' >&2
	exit 2
}
die() {
	printf 'build: %s\n' "$*" >&2
	exit 2
}

cleanup_root=""
cleanup() {
	[ -z "$cleanup_root" ] && return 0
	[ -d "$cleanup_root" ] || return 0
	find "$cleanup_root" -depth -mindepth 1 -delete
	rmdir "$cleanup_root"
}
trap cleanup EXIT

absolute_dir() {
	local dir="$1"
	[ -d "$dir" ] || die "not a directory: $dir"
	(cd "$dir" && pwd)
}

rm_tree() {
	local dir="$1"
	[ -n "$dir" ] || die "refusing to remove an empty path"
	[ -d "$dir" ] || return 0
	find "$dir" -depth -mindepth 1 -delete
	rmdir "$dir"
}

replace_board_mentions() {
	local dir="$1" file tmp
	for file in AGENTS.md docs/agents/issue-tracker.md; do
		[ -f "$dir/$file" ] || die "missing $file"
		tmp="$dir/$file.tmp"
		sed -e 's|scripts/build-board\.sh|scripts/board.sh build|g' \
			-e 's|scripts/check-board\.sh|scripts/board.sh check|g' \
			"$dir/$file" >"$tmp"
		mv "$tmp" "$dir/$file"
	done
}

copy_skills() {
	local dir="$1"
	rm_tree "$dir/.claude/skills"
	mkdir -p "$dir/.claude"
	cp -a "$arkan_root/skills/." "$dir/.claude/skills"
}

copy_ci() {
	local dir="$1" workflow
	mkdir -p "$dir/.github/workflows"
	cp -p "$script_dir/sandbox/check.yml" "$dir/.github/workflows/check.yml"
	cp -p "$script_dir/sandbox/auto-merge.yml" "$dir/.github/workflows/auto-merge.yml"
	workflow="$dir/.github/workflows/arkan-review.yml"
	sed -E 's/^(  REVIEW_MODEL: ).*$/\1claude-sonnet-5-5/' "$arkan_root/ci/github/arkan-review.yml" >"$workflow"
	grep -q '^  REVIEW_MODEL: claude-sonnet-5-5$' "$workflow" || die "arkan-review.yml has no sonnet model line"
}

commit_tree() {
	local dest="$1" branch="$2" stage="$3" index="$4" message="$5"
	local base tree commit
	base=$(git -C "$dest" rev-parse "refs/heads/$branch")
	tree=$(GIT_DIR="$dest/.git" GIT_WORK_TREE="$stage" GIT_INDEX_FILE="$index" git add -A && GIT_DIR="$dest/.git" GIT_INDEX_FILE="$index" git write-tree)
	commit=$(GIT_AUTHOR_NAME="$build_name" GIT_AUTHOR_EMAIL="$build_email" GIT_AUTHOR_DATE="$build_date" \
		GIT_COMMITTER_NAME="$build_name" GIT_COMMITTER_EMAIL="$build_email" GIT_COMMITTER_DATE="$build_date" \
		TZ=UTC git -C "$dest" -c commit.gpgsign=false commit-tree "$tree" -p "$base" -m "$message")
	git -C "$dest" update-ref "refs/heads/$branch" "$commit"
	printf '%s\n' "$commit"
}

build() {
	local dest="$1" parent stage_main stage_pre index_main index_pre todo
	local main_before pre_before main_tip pre_tip status
	[ -n "$dest" ] || usage
	if [ -e "$dest" ]; then
		[ -d "$dest" ] || die "destination is not a directory: $dest"
		[ -z "$(ls -A "$dest")" ] || die "destination is not empty: $dest"
	else
		parent=$(dirname "$dest")
		[ -d "$parent" ] || die "parent does not exist: $parent"
	fi
	parent=$(absolute_dir "$(dirname "$dest")")
	dest="$parent/$(basename "$dest")"
	case "$dest/" in
		"$arkan_root"/*) die "destination must be outside the arkan checkout: $dest" ;;
	esac
	[ -f "$seed" ] || die "missing seed bundle: $seed"
	mkdir -p "$dest"
	git -C "$dest" init -q
	git -C "$dest" fetch -q "$seed" '+refs/heads/*:refs/seed/*'
	git -C "$dest" update-ref refs/heads/main "$(git -C "$dest" rev-parse refs/seed/main)"
	git -C "$dest" update-ref refs/heads/pre-break "$(git -C "$dest" rev-parse refs/seed/pre-break)"
	git -C "$dest" update-ref -d refs/seed/main
	git -C "$dest" update-ref -d refs/seed/pre-break
	main_before=$(git -C "$dest" rev-parse --verify refs/heads/main)
	pre_before=$(git -C "$dest" rev-parse --verify refs/heads/pre-break)
	[ "$main_before" = "294acb1dc039ab87ddfab7d5c7c77c20404efdf3" ] || die "seed main is $main_before"
	[ "$pre_before" = "af4922bffa6fee961cac2df2a1d50de1324c8083" ] || die "seed pre-break is $pre_before"

	stage_main=$(mktemp -d "$parent/.arkan-build.XXXXXX")
	cleanup_root=$stage_main
	stage_main="$cleanup_root/main"
	stage_pre="$cleanup_root/pre-break"
	mkdir -p "$stage_main" "$stage_pre"
	index_main="$cleanup_root/index-main"
	index_pre="$cleanup_root/index-pre"

	git -C "$dest" archive main | tar -x -C "$stage_main"
	replace_board_mentions "$stage_main"
	copy_skills "$stage_main"
	find "$stage_main/scripts" -maxdepth 1 \( -name build-board.sh -o -name check-board.sh \) -delete
	cp -p "$arkan_root/scripts/board.sh" "$stage_main/scripts/board.sh"
	chmod +x "$stage_main/scripts/board.sh"
	copy_ci "$stage_main"
	todo=$(cd "$stage_main" && bash scripts/board.sh build "$stage_main")
	printf '%s\n' "$todo"
	(cd "$stage_main" && bash scripts/board.sh check "$stage_main")
	main_tip=$(commit_tree "$dest" main "$stage_main" "$index_main" \
		"rebuild: current arkan skills, one board entry point, sandbox ci")

	git -C "$dest" archive pre-break | tar -x -C "$stage_pre"
	replace_board_mentions "$stage_pre"
	copy_skills "$stage_pre"
	find "$stage_pre/scripts" -maxdepth 1 \( -name build-board.sh -o -name check-board.sh \) -delete
	cp -p "$arkan_root/scripts/board.sh" "$stage_pre/scripts/board.sh"
	chmod +x "$stage_pre/scripts/board.sh"
	copy_ci "$stage_pre"
	todo=$(cd "$stage_pre" && bash scripts/board.sh build "$stage_pre")
	printf '%s\n' "$todo"
	(cd "$stage_pre" && bash scripts/board.sh check "$stage_pre")
	pre_tip=$(commit_tree "$dest" pre-break "$stage_pre" "$index_pre" \
		"rebuild: current arkan skills, one board entry point, sandbox ci")

	if diff -r "$arkan_root/skills" "$stage_pre/.claude/skills" >/dev/null; then
		:
	else
		die "pre-break .claude/skills does not match arkan skills"
	fi
	if diff -r "$arkan_root/skills" "$stage_main/.claude/skills" >/dev/null; then
		:
	else
		die "main .claude/skills does not match arkan skills"
	fi
	for status in "$stage_main" "$stage_pre"; do
		grep -q 'scripts/board.sh build' "$status/AGENTS.md" || die "AGENTS.md does not name board.sh build"
		grep -q 'scripts/board.sh check' "$status/AGENTS.md" || die "AGENTS.md does not name board.sh check"
		[ ! -e "$status/scripts/build-board.sh" ] || die "build-board.sh survived"
		[ ! -e "$status/scripts/check-board.sh" ] || die "check-board.sh survived"
	done
	(cd "$stage_pre" && bash scripts/check.sh) || die "pre-break check failed"
	if (cd "$stage_main" && bash scripts/check.sh) >"$cleanup_root/main.log" 2>&1; then
		die "main check passed; the planted money regression is gone"
	fi
	grep -q 'test_parses_one_decimal_place_as_tens_of_cents' "$cleanup_root/main.log" ||
		die "main check failed for a reason other than the planted money regression"

	git -C "$dest" symbolic-ref HEAD refs/heads/main
	git -C "$dest" read-tree main
	git -C "$dest" archive main | tar -x -C "$dest"
	[ -z "$(git -C "$dest" status --porcelain)" ] || die "destination worktree is not clean"

	if git -C "$dest" log --all --format= --name-only | grep -qx 'ANSWERS.md'; then
		die "ANSWERS.md is in the exposed history"
	fi
	for status in main pre-break; do
		git -C "$dest" ls-tree -r --name-only "$status" | grep -qx 'ANSWERS.md' && die "ANSWERS.md is in $status"
		git -C "$dest" ls-tree -r --name-only "$status" | grep -Eq '^scripts/(build|check)-board\.sh$' && die "old board script is in $status"
		[ "$(git -C "$dest" ls-tree -r --name-only "$status" scripts | grep -c '^scripts/board\.sh$')" = 1 ] || die "board.sh is not the one board entry in $status"
	done
	[ ! -e "$dest/ANSWERS.md" ] || die "ANSWERS.md is in the checkout"
	grep -q '^  REVIEW_MODEL: claude-sonnet-5-5$' "$dest/.github/workflows/arkan-review.yml" || die "review model is not sonnet"

	printf 'build: wrote %s\n' "$dest"
	printf 'build: main %s\n' "$main_tip"
	printf 'build: pre-break %s\n' "$pre_tip"
	printf 'build: pre-break check ok, main fails test_parses_one_decimal_place_as_tens_of_cents\n'
}

refresh() {
	local target="$1" base="${2:-pre-break}" branch short source_sha source_version slug
	local base_sha worktree changed head title body
	target=$(absolute_dir "$target")
	git -C "$target" rev-parse --git-dir >/dev/null 2>&1 || die "not a git checkout: $target"
	[ -d "$target/.claude/skills" ] || die "checkout has no .claude/skills: $target"
	[ -z "$(git -C "$target" status --porcelain)" ] || die "checkout is not clean: $target"
	source_sha=$(git -C "$arkan_root" rev-parse HEAD) || die "cannot read arkan HEAD"
	short=$(printf '%s' "$source_sha" | cut -c1-12)
	source_version="$short"
	if [ -n "$(git -C "$arkan_root" status --porcelain -- skills)" ]; then
		source_version="$source_version-dirty"
	fi
	base_sha=$(git -C "$target" rev-parse --verify "refs/heads/$base" 2>/dev/null ||
		git -C "$target" rev-parse --verify "refs/remotes/origin/$base" 2>/dev/null) ||
		die "base branch not found: $base"
	slug=$(git -C "$target" remote get-url origin 2>/dev/null) || die "checkout has no origin"
	slug="${slug%/}"
	slug="${slug%.git}"
	slug="${slug#https://github.com/}"
	slug="${slug#git@github.com:}"
	slug="${slug#ssh://git@github.com/}"
	case "$slug" in
		*/*/*) die "cannot read owner/repo from origin: $slug" ;;
		*/*) : ;;
		*) die "cannot read owner/repo from origin: $slug" ;;
	esac
	branch="agent/refresh-skills-$source_version"
	[ -z "$(git -C "$target" rev-parse --verify "refs/heads/$branch" 2>/dev/null)" ] || die "local branch exists: $branch"
	command -v agent-gh >/dev/null || die "broker client missing on PATH"

	worktree=$(mktemp -d "${TMPDIR:-/tmp}/arkan-refresh.XXXXXX")
	git -C "$target" worktree add -q -b "$branch" "$worktree" "$base_sha"
	git -C "$worktree" rm -r -q .claude/skills
	mkdir -p "$worktree/.claude"
	cp -a "$arkan_root/skills/." "$worktree/.claude/skills"
	git -C "$worktree" add -A .claude/skills
	changed=$(git -C "$worktree" diff --cached --name-only)
	if [ -z "$changed" ]; then
		git -C "$target" worktree remove --force "$worktree"
		git -C "$target" branch -D "$branch" >/dev/null
		printf 'refresh: skills already current at arkan %s\n' "$source_version"
		return 0
	fi
	while IFS= read -r path; do
		case "$path" in
			.claude/skills/*) : ;;
			*) die "change outside .claude/skills: $path" ;;
		esac
	done <<<"$changed"
	if [ -n "$(git -C "$worktree" status --porcelain | grep -v '^[AMDRC]  \.claude/skills/' || true)" ]; then
		die "change outside .claude/skills after staging"
	fi
	git -C "$worktree" -c user.name="arkan refresh" -c user.email="$build_email" -c commit.gpgsign=false \
		commit -q -m "chore(skills): refresh from arkan $source_version"
	head=$(git -C "$worktree" rev-parse HEAD)
	title="chore(skills): refresh from arkan $source_version"
	body="## Why
Keep the sandbox's .claude/skills/ matched to arkan $source_sha.

## What changed
Replaced only .claude/skills/ with arkan's skill tree at $source_version.

## Scope
No files outside .claude/skills/ change.

## Blast Radius
Scenario runs use the refreshed skills; the stock code and tests are unchanged.

## Verification
git diff --name-only $base_sha..$head lists only .claude/skills/ paths."
	agent-gh push "$slug" "$worktree" "$branch" "$head"
	agent-gh pr-create "$slug" "$base" "$branch" "$title" "$body"
	git -C "$target" worktree remove "$worktree"
	printf 'refresh: branch %s at %s, %s files\n' "$branch" "$head" "$(printf '%s\n' "$changed" | wc -l | tr -d ' ')"
}

[ $# -ge 1 ] || usage
mode=$1
shift
case "$mode" in
	build)
		[ $# -eq 1 ] || usage
		export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null
		build "$1"
		;;
	refresh)
		[ $# -ge 1 ] && [ $# -le 2 ] || usage
		refresh "$@"
		;;
	*) usage ;;
esac
