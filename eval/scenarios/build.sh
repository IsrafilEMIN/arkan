#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd "$(dirname "$0")" && pwd)
arkan_root=$(cd "$script_dir/../.." && pwd)
seed="$script_dir/sandbox/history.bundle"
board_link="../.claude/skills/pre-setup/scripts/board.sh"
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
refresh_target=""
refresh_worktree=""
refresh_branch=""
refresh_root=""
refresh_keep=0

rm_tree() {
	local dir="$1"
	[ -n "$dir" ] || die "refusing to remove an empty path"
	[ -d "$dir" ] || return 0
	find "$dir" -depth -mindepth 1 -delete
	rmdir "$dir"
}

cleanup_dir() {
	local dir="$1"
	[ -n "$dir" ] && [ -d "$dir" ] || return 0
	find "$dir" -depth -mindepth 1 -delete 2>/dev/null || true
	rmdir "$dir" 2>/dev/null || true
}

cleanup_all() {
	cleanup_dir "$cleanup_root"
	if [ "$refresh_keep" = 1 ]; then
		return 0
	fi
	if [ -n "$refresh_target" ] && [ -n "$refresh_worktree" ] && [ -d "$refresh_worktree" ]; then
		git -C "$refresh_target" worktree remove --force "$refresh_worktree" >/dev/null 2>&1 || true
		cleanup_dir "$refresh_worktree"
	fi
	if [ -n "$refresh_target" ] && [ -n "$refresh_branch" ] &&
		git -C "$refresh_target" rev-parse --verify "refs/heads/$refresh_branch" >/dev/null 2>&1; then
		git -C "$refresh_target" branch -D "$refresh_branch" >/dev/null 2>&1 || true
	fi
	cleanup_dir "$refresh_root"
}
trap cleanup_all EXIT

absolute_dir() {
	local dir="$1"
	[ -d "$dir" ] || die "not a directory: $dir"
	(cd "$dir" && pwd)
}

check_skills_clean() {
	[ -z "$(git -C "$arkan_root" status --porcelain -- skills)" ] ||
		die "skills/ has uncommitted changes; commit them first"
}

export_skills() {
	local dir="$1"
	mkdir -p "$dir"
	git -C "$arkan_root" archive HEAD skills | tar -x -C "$dir"
	[ -d "$dir/skills" ] || die "arkan HEAD has no skills/ tree"
}

install_skills() {
	local stage="$1" source="$2"
	rm_tree "$stage/.claude/skills"
	mkdir -p "$stage/.claude"
	cp -a "$source/skills/." "$stage/.claude/skills"
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
	local repo="$1" branch="$2" stage="$3" index="$4" message="$5"
	local base tree commit
	base=$(git -C "$repo" rev-parse "refs/heads/$branch")
	tree=$(GIT_DIR="$repo/.git" GIT_WORK_TREE="$stage" GIT_INDEX_FILE="$index" git add -A &&
		GIT_DIR="$repo/.git" GIT_INDEX_FILE="$index" git write-tree)
	commit=$(GIT_AUTHOR_NAME="$build_name" GIT_AUTHOR_EMAIL="$build_email" GIT_AUTHOR_DATE="$build_date" \
		GIT_COMMITTER_NAME="$build_name" GIT_COMMITTER_EMAIL="$build_email" GIT_COMMITTER_DATE="$build_date" \
		TZ=UTC git -C "$repo" -c commit.gpgsign=false commit-tree "$tree" -p "$base" -m "$message")
	git -C "$repo" update-ref "refs/heads/$branch" "$commit"
	printf '%s\n' "$commit"
}

stage_branch() {
	local repo="$1" branch="$2" skills="$3"
	local stage index
	stage="$cleanup_root/$branch"
	index="$cleanup_root/index-$branch"
	mkdir -p "$stage"
	git -C "$repo" archive "$branch" | tar -x -C "$stage"
	replace_board_mentions "$stage"
	install_skills "$stage" "$skills"
	find "$stage/scripts" -maxdepth 1 \( -name build-board.sh -o -name check-board.sh \) -delete
	ln -s "$board_link" "$stage/scripts/board.sh"
	copy_ci "$stage"
	(cd "$stage" && bash scripts/board.sh build "$stage")
	(cd "$stage" && bash scripts/board.sh check "$stage")
	staged_commit=$(commit_tree "$repo" "$branch" "$stage" "$index" \
		"rebuild: current arkan skills, one board entry point, sandbox ci")
}

build() {
	local dest="$1" parent repo main_before pre_before main_tip pre_tip
	local skills stage link count main_log
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
	check_skills_clean
	cleanup_root=$(mktemp -d "$parent/.arkan-build.XXXXXX")
	skills="$cleanup_root/skills"
	export_skills "$skills"
	repo="$cleanup_root/repo"
	mkdir -p "$repo"
	git -C "$repo" init -q
	git -C "$repo" fetch -q "$seed" '+refs/heads/*:refs/seed/*'
	git -C "$repo" update-ref refs/heads/main "$(git -C "$repo" rev-parse refs/seed/main)"
	git -C "$repo" update-ref refs/heads/pre-break "$(git -C "$repo" rev-parse refs/seed/pre-break)"
	git -C "$repo" update-ref -d refs/seed/main
	git -C "$repo" update-ref -d refs/seed/pre-break
	main_before=$(git -C "$repo" rev-parse --verify refs/heads/main)
	pre_before=$(git -C "$repo" rev-parse --verify refs/heads/pre-break)
	[ "$main_before" = "294acb1dc039ab87ddfab7d5c7c77c20404efdf3" ] || die "seed main is $main_before"
	[ "$pre_before" = "af4922bffa6fee961cac2df2a1d50de1324c8083" ] || die "seed pre-break is $pre_before"

	for stage in main pre-break; do
		stage_branch "$repo" "$stage" "$skills"
		case "$stage" in
			main) main_tip=$staged_commit ;;
			pre-break) pre_tip=$staged_commit ;;
		esac
	done

	for stage in main pre-break; do
		diff -r "$skills/skills" "$cleanup_root/$stage/.claude/skills" >/dev/null ||
			die "$stage .claude/skills does not match arkan HEAD"
		grep -q 'scripts/board.sh build' "$cleanup_root/$stage/AGENTS.md" ||
			die "$stage AGENTS.md does not name board.sh build"
		grep -q 'scripts/board.sh check' "$cleanup_root/$stage/AGENTS.md" ||
			die "$stage AGENTS.md does not name board.sh check"
		[ ! -e "$cleanup_root/$stage/scripts/build-board.sh" ] || die "$stage has build-board.sh"
		[ ! -e "$cleanup_root/$stage/scripts/check-board.sh" ] || die "$stage has check-board.sh"
		if git -C "$repo" cat-file -e "$stage:ANSWERS.md" 2>/dev/null; then
			die "$stage has ANSWERS.md"
		fi
		if git -C "$repo" cat-file -e "$stage:scripts/build-board.sh" 2>/dev/null; then
			die "$stage has build-board.sh in its tree"
		fi
		if git -C "$repo" cat-file -e "$stage:scripts/check-board.sh" 2>/dev/null; then
			die "$stage has check-board.sh in its tree"
		fi
		git -C "$repo" cat-file -e "$stage:scripts/board.sh" 2>/dev/null ||
			die "$stage has no scripts/board.sh"
		link=$(git -C "$repo" cat-file -p "$stage:scripts/board.sh")
		[ "$link" = "$board_link" ] || die "$stage board.sh is not the skills symlink"
		[ -f "$cleanup_root/$stage/scripts/board.sh" ] || die "$stage board.sh symlink is broken"
		[ -x "$cleanup_root/$stage/scripts/board.sh" ] || die "$stage board.sh is not executable"
		git -C "$repo" ls-tree -r --name-only "$stage" scripts >"$cleanup_root/scripts-$stage"
		count=$(wc -l <"$cleanup_root/scripts-$stage" | tr -d ' ')
		[ "$count" = 3 ] || die "$stage scripts/ has $count entries"
		grep -qx 'scripts/board.sh' "$cleanup_root/scripts-$stage" || die "$stage scripts/board.sh missing"
		grep -qx 'scripts/check.sh' "$cleanup_root/scripts-$stage" || die "$stage scripts/check.sh missing"
		grep -qx 'scripts/style.py' "$cleanup_root/scripts-$stage" || die "$stage scripts/style.py missing"
	done
	git -C "$repo" log --all --format= --name-only >"$cleanup_root/history-paths"
	if grep -qx 'ANSWERS.md' "$cleanup_root/history-paths"; then
		die "ANSWERS.md is in the exposed history"
	fi
	(cd "$cleanup_root/pre-break" && bash scripts/check.sh) || die "pre-break check failed"
	if (cd "$cleanup_root/main" && bash scripts/check.sh) >"$cleanup_root/main.log" 2>&1; then
		die "main check passed; the planted money regression is gone"
	fi
	grep -q 'test_parses_one_decimal_place_as_tens_of_cents' "$cleanup_root/main.log" ||
		die "main check failed for a reason other than the planted money regression"

	git -C "$repo" symbolic-ref HEAD refs/heads/main
	git -C "$repo" read-tree main
	git -C "$repo" archive main | tar -x -C "$repo"
	[ -z "$(git -C "$repo" status --porcelain)" ] || die "staged worktree is not clean"
	if [ -d "$dest" ]; then
		rmdir "$dest"
	fi
	mv "$repo" "$dest"
	[ -z "$(git -C "$dest" status --porcelain)" ] || die "destination worktree is not clean"
	[ -f "$dest/scripts/board.sh" ] || die "destination board.sh symlink is broken"

	printf 'build: wrote %s\n' "$dest"
	printf 'build: main %s\n' "$main_tip"
	printf 'build: pre-break %s\n' "$pre_tip"
	printf 'build: skills from arkan %s\n' "$(git -C "$arkan_root" rev-parse HEAD)"
	printf 'build: pre-break check ok, main fails test_parses_one_decimal_place_as_tens_of_cents\n'
}

refresh() {
	local target="$1" base="${2:-pre-break}" branch short source_sha slug
	local base_sha changed head title body path status count
	target=$(absolute_dir "$target")
	git -C "$target" rev-parse --git-dir >/dev/null 2>&1 || die "not a git checkout: $target"
	[ -d "$target/.claude/skills" ] || die "checkout has no .claude/skills: $target"
	[ -z "$(git -C "$target" status --porcelain)" ] || die "checkout is not clean: $target"
	check_skills_clean
	source_sha=$(git -C "$arkan_root" rev-parse HEAD) || die "cannot read arkan HEAD"
	short=$(printf '%s' "$source_sha" | cut -c1-12)
	git -C "$target" fetch -q origin "+refs/heads/$base:refs/remotes/origin/$base" ||
		die "cannot fetch origin/$base"
	base_sha=$(git -C "$target" rev-parse --verify "refs/remotes/origin/$base" 2>/dev/null) ||
		die "origin/$base is missing"
	slug=$(git -C "$target" config --get remote.origin.url 2>/dev/null) || die "checkout has no origin"
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
	branch="agent/refresh-skills-$short"
	[ -z "$(git -C "$target" rev-parse --verify "refs/heads/$branch" 2>/dev/null)" ] ||
		die "local branch exists: $branch"
	command -v agent-gh >/dev/null || die "broker client missing on PATH"

	refresh_target=$target
	refresh_branch=$branch
	refresh_root=$(mktemp -d "${TMPDIR:-/tmp}/arkan-refresh.XXXXXX")
	refresh_worktree="$refresh_root/worktree"
	export_skills "$refresh_root"
	git -C "$target" worktree add -q -b "$branch" "$refresh_worktree" "$base_sha"
	git -C "$refresh_worktree" rm -r -q .claude/skills
	mkdir -p "$refresh_worktree/.claude"
	cp -a "$refresh_root/skills/." "$refresh_worktree/.claude/skills"
	git -C "$refresh_worktree" add -A .claude/skills
	changed=$(git -C "$refresh_worktree" diff --cached --name-only)
	if [ -z "$changed" ]; then
		printf 'refresh: skills already current at arkan %s\n' "$source_sha"
		return 0
	fi
	while IFS= read -r path; do
		case "$path" in
			.claude/skills/*) : ;;
			*) die "change outside .claude/skills: $path" ;;
		esac
	done <<<"$changed"
	status=$(git -C "$refresh_worktree" status --porcelain)
	while IFS= read -r path; do
		case "$path" in
			"" | [AMDRC]"  ".claude/skills/*) : ;;
			*) die "change outside .claude/skills after staging: $path" ;;
		esac
	done <<<"$status"
	GIT_AUTHOR_DATE="$build_date" GIT_COMMITTER_DATE="$build_date" TZ=UTC \
		git -C "$refresh_worktree" -c user.name="arkan refresh" -c user.email="$build_email" \
			-c commit.gpgsign=false commit -q -m "chore(skills): refresh from arkan $short"
	head=$(git -C "$refresh_worktree" rev-parse HEAD)
	title="chore(skills): refresh from arkan $short"
	body="## Why
Keep the sandbox's .claude/skills/ matched to arkan $source_sha.

## What changed
Replaced only .claude/skills/ with arkan's tree at $source_sha.

## Scope
No files outside .claude/skills/ change.

## Blast Radius
Scenario runs use the refreshed skills; the stock code and tests are unchanged.

## Verification
git diff --name-only $base_sha..$head lists only .claude/skills/ paths."
	agent-gh push "$slug" "$refresh_worktree" "$branch" "$head"
	refresh_keep=1
	agent-gh pr-create "$slug" "$base" "$branch" "$title" "$body"
	git -C "$target" worktree remove "$refresh_worktree"
	rm_tree "$refresh_root"
	count=$(awk 'END {print NR}' <<<"$changed")
	printf 'refresh: branch %s at %s, %s files\n' "$branch" "$head" "$count"
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
