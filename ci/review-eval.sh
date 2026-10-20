#!/usr/bin/env bash
set -eu
cd "$(git rev-parse --show-toplevel)"
export LC_ALL=C

cases=docs/agents/review-evals
workflow=
prompt=
reviewer=${REVIEW_CMD:-}
baseline=
compare=0
update=0
check=0
show=0

usage() {
	cat <<'EOF'
usage: ci/review-eval.sh [options]

runs the arkan-review reviewer on each case's bad.diff and prints
`<case> caught` or `<case> missed`.

  --cases DIR         case folders (default: docs/agents/review-evals)
  --workflow FILE     the arkan-review workflow that holds the prompt, the
                      model and the allowed tools (default:
                      ci/github/arkan-review.yml, else
                      .github/workflows/arkan-review.yml)
  --prompt FILE       reviewer prompt, replacing the workflow's prompt
  --reviewer CMD      reviewer command, reading the prompt on stdin
                      (default: REVIEW_CMD, else `claude -p` with the
                      workflow's model and allowed tools)
  --baseline FILE     caught-case baseline (default: <cases>/baseline.txt)
  --compare           exit 1 when a case in the baseline is now missed
  --update-baseline   add the caught cases to the baseline, never drop one
  --check             check the cases, the prompt and the baseline without a model
  --show              print the reviewer's output to stderr
EOF
}

die() { printf 'review-eval: %s\n' "$*" >&2; exit 2; }

while [ $# -gt 0 ]; do
	case "$1" in
		--cases) cases=${2:?}; shift 2 ;;
		--workflow) workflow=${2:?}; shift 2 ;;
		--prompt) prompt=${2:?}; shift 2 ;;
		--reviewer) reviewer=${2:?}; shift 2 ;;
		--baseline) baseline=${2:?}; shift 2 ;;
		--compare) compare=1; shift ;;
		--update-baseline) update=1; shift ;;
		--check) check=1; shift ;;
		--show) show=1; shift ;;
		-h|--help) usage; exit 0 ;;
		*) usage >&2; die "unknown option: $1" ;;
	esac
done

[ -d "$cases" ] || die "no cases folder: $cases"
[ -z "$baseline" ] && baseline=$cases/baseline.txt
[ "$compare" = 1 ] && [ "$update" = 1 ] && die "--compare and --update-baseline cannot be combined"
[ "$compare" = 1 ] && [ ! -f "$baseline" ] && die "no baseline: $baseline"

if [ -z "$workflow" ]; then
	for f in ci/github/arkan-review.yml .github/workflows/arkan-review.yml; do
		if [ -f "$f" ]; then workflow=$f; break; fi
	done
fi
[ -n "$workflow" ] || die "no workflow: ci/github/arkan-review.yml or .github/workflows/arkan-review.yml"
[ -f "$workflow" ] || die "no workflow: $workflow"

workflow_prompt() {
	awk '
		!started {
			if ($0 ~ /^[[:space:]]*prompt:[[:space:]]*\|[[:space:]]*$/) started = 1
			next
		}
		!content {
			if ($0 ~ /^[[:space:]]*$/) { print ""; next }
			match($0, /^[[:space:]]*/)
			content = RLENGTH
		}
		{
			if ($0 ~ /^[[:space:]]*$/) { print ""; next }
			match($0, /^[[:space:]]*/)
			if (RLENGTH < content) exit
			print substr($0, content + 1)
		}
	' "$1"
}

workflow_model() {
	sed -n 's/^[[:space:]]*REVIEW_MODEL:[[:space:]]*//p' "$1" | head -n1 | sed 's/[[:space:]]*$//'
}

workflow_tools() {
	sed -n 's/^[[:space:]]*--allowedTools[[:space:]]*"\(.*\)"[[:space:]]*$/\1/p' "$1" | head -n1
}

workflow_turns() {
	sed -n 's/^[[:space:]]*MAX_TURNS:[[:space:]]*//p' "$1" | head -n1 | sed 's/[[:space:]]*$//' | tr -d '"'
}

prompt_text=$(workflow_prompt "$workflow")
[ -n "$prompt_text" ] || die "$workflow has no prompt block"
model=$(workflow_model "$workflow")
[ -n "$model" ] || die "$workflow has no REVIEW_MODEL"
tools=$(workflow_tools "$workflow")
[ -n "$tools" ] || die "$workflow has no --allowedTools line"
turns=$(workflow_turns "$workflow")
[ -n "$turns" ] || die "$workflow has no MAX_TURNS"

read_envs="REVIEW_MODEL MAX_TURNS"
for name in $(grep -oE '\$\{\{[[:space:]]*env\.[A-Za-z_][A-Za-z0-9_]*' "$workflow" | sed 's/.*env\.//' | sort -u || true); do
	case " $read_envs " in
		*" $name "*) ;;
		*) die "$workflow uses \${{ env.$name }}, which the eval does not read" ;;
	esac
done
if [ -n "$prompt" ]; then
	[ -f "$prompt" ] || die "no prompt file: $prompt"
	prompt_text=$(cat "$prompt")
fi

origin=$(git remote get-url origin 2>/dev/null || true)
repo_slug=
case "$origin" in
	https://github.com/*) repo_slug=${origin#https://github.com/} ;;
	git@github.com:*) repo_slug=${origin#git@github.com:} ;;
	ssh://git@github.com/*) repo_slug=${origin#ssh://git@github.com/} ;;
esac
repo_slug=${repo_slug%.git}
printf '%s' "$repo_slug" | grep -Eq '^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$' || repo_slug=owner/repo

trim() { local s=$1; s=${s#"${s%%[![:space:]]*}"}; printf '%s' "${s%"${s##*[![:space:]]}"}"; }

case_path=
case_range=
case_first=
case_last=
case_commit=
case_pr=
n_cases=0

read_case() {
	local dir=$1 file
	file=$dir/case.md
	[ -f "$file" ] || die "$dir has no case.md"
	for field in Bug Path Lines; do
		grep -q "^\*\*$field:\*\*" "$file" || die "$file has no **$field:** line"
	done
	grep -q '^\*\*Fix PR:\*\*' "$file" || die "$file has no **Fix PR:** line"
	grep -q '^\*\*Broke main:\*\*' "$file" || die "$file has no **Broke main:** line"
	grep -q '^\*\*Bad PR:\*\*' "$file" || die "$file has no **Bad PR:** line"
	case_path=$(sed -n 's/^\*\*Path:\*\*[[:space:]]*`\([^`]*\)`.*$/\1/p' "$file" | head -n1)
	case_range=$(sed -n 's/^\*\*Lines:\*\*[[:space:]]*\([0-9][0-9]*\(-[0-9][0-9]*\)\{0,1\}\)[[:space:]]*$/\1/p' "$file" | head -n1)
	[ -n "$case_path" ] || die "$file: **Path:** needs one path in backticks"
	[ -n "$case_range" ] || die "$file: **Lines:** needs a number or a range"
	case_first=${case_range%%-*}
	case_last=${case_range#*-}
	[ "$case_last" = "$case_range" ] && case_last=$case_first
	[ "$case_first" -le "$case_last" ] || die "$file: **Lines:** starts after it ends: $case_range"
	case_commit=$(sed -n 's/^\*\*Broke main:\*\*//p' "$file" | grep -oE '[0-9a-f]{7,40}' | head -n1)
	[ -n "$case_commit" ] || die "$file: **Broke main:** needs a commit"
	case_pr=$(sed -n 's/^\*\*Bad PR:\*\*//p' "$file" | grep -oE '#[0-9]+|/pull/[0-9]+' | head -n1 | tr -dc '0-9')
	if [ -z "$case_pr" ]; then
		case_pr=$(sed -n 's/^\*\*Broke main:\*\*//p' "$file" | grep -oE '#[0-9]+|/pull/[0-9]+' | head -n1 | tr -dc '0-9')
	fi
	[ -n "$case_pr" ] || case_pr=0
	[ -s "$dir/bad.diff" ] || die "$dir has no bad.diff"
	grep -q '^diff --git ' "$dir/bad.diff" || die "$dir/bad.diff is not a git diff"
	grep -q '^+++ b/' "$dir/bad.diff" || die "$dir/bad.diff has no new file side"
	grep -qF "+++ b/$case_path" "$dir/bad.diff" || die "$file: **Path:** $case_path is not in bad.diff"
}

for dir in "$cases"/*/; do
	[ -d "$dir" ] || continue
	[ -f "$dir/case.md" ] || die "$dir has no case.md"
	read_case "$dir"
	n_cases=$((n_cases + 1))
done
[ "$n_cases" -gt 0 ] || die "no cases in $cases"

baseline_names() {
	[ -f "$baseline" ] || return 0
	grep -vE '^[[:space:]]*(#|$)' "$baseline" || true
}

while IFS= read -r name; do
	name=$(trim "$name")
	[ -n "$name" ] || continue
	[ -f "$cases/$name/case.md" ] || die "baseline names a missing case: $name"
done < <(baseline_names)

fill_prompt() {
	printf '%s' "$prompt_text" | sed \
		-e 's|${{ github.event.pull_request.number }}|'"$case_pr"'|g' \
		-e 's|${{ github.repository }}|'"$repo_slug"'|g' \
		-e 's|${{ steps.round.outputs.round }}|1|g' \
		-e 's|${{ github.event.pull_request.head.sha }}|'"$run_head"'|g' \
		-e 's|${{ github.event.pull_request.base.sha }}|'"$run_base"'|g' \
		-e 's|${{ steps.round.outputs.diff }}|'"$run_diff"'|g' \
		-e 's|${{ steps.round.outputs.scope }}|the full pr diff|g' \
		-e 's|${{ steps.round.outputs.prior }}|none (this is round 1)|g' \
		-e 's|${{ steps.round.outputs.from }}|'"$run_from"'|g'
}

run_head=0000000
run_base=0000000
run_diff=0000000...0000000
run_from=0000000
left=$(fill_prompt | grep -oE '\$\{\{[^}]*\}\}' | head -n1 || true)
[ -z "$left" ] || die "$workflow has an input the eval does not fill: $left"
unset left

if [ "$check" = 1 ]; then
	printf 'review-eval: ok (%s case(s))\n' "$n_cases"
	exit 0
fi

if [ -n "$reviewer" ]; then
	read -r -a reviewer_cmd <<<"$reviewer"
else
	command -v claude >/dev/null || die "claude is not on PATH; set REVIEW_CMD to a headless reviewer"
	reviewer_cmd=(claude -p --model "$model" --allowedTools "$tools" --max-turns "$turns")
fi

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
: >"$tmp/caught"
n_caught=0
n_missed=0
n_error=0

grade() {
	awk -v path="$case_path" -v first="$case_first" -v last="$case_last" '
		function pathchar(c) { return c ~ /[A-Za-z0-9._\/-]/ }
		{
			s = $0
			while ((i = index(s, path)) > 0) {
				before = (i > 1) ? substr(s, i - 1, 1) : ""
				after = substr(s, i + length(path), 1)
				if ((i == 1 || !pathchar(before)) && after == ":") {
					rest = substr(s, i + length(path) + 1)
					if (match(rest, /^[0-9]+(-[0-9]+)?/)) {
						seg = substr(rest, RSTART, RLENGTH)
						split(seg, part, "-")
						a = part[1] + 0
						b = (part[2] == "") ? a : part[2] + 0
						if (a >= first + 0 && b <= last + 0 && b - a <= last - first) { found = 1; exit }
					}
				}
				s = substr(s, i + length(path))
			}
		}
		END { exit(found ? 0 : 1) }' "$1"
}

make_work() {
	local dir=$1 zero=$2 message name src
	mkdir -p "$zero"
	git -C "$zero" init -q
	git -C "$zero" config user.email review-eval@localhost
	git -C "$zero" config user.name review-eval
	git archive "$case_commit^" | tar -x -C "$zero"
	rm -rf "$zero/docs/agents/review-evals"
	for name in code-review security-review; do
		src=
		if [ -d "skills/$name" ]; then
			src=skills/$name
		elif [ -d ".claude/skills/$name" ]; then
			src=.claude/skills/$name
		fi
		[ -n "$src" ] || continue
		mkdir -p "$zero/.claude/skills"
		rm -rf "$zero/.claude/skills/$name"
		cp -RL "$src" "$zero/.claude/skills/$name"
	done
	message=$(git log -1 --format=%B "$case_commit^")
	git -C "$zero" add -A -f
	git -C "$zero" commit -qm "$message"
	if ! git -C "$zero" apply --binary "$dir/bad.diff"; then
		die "$dir: bad.diff does not apply at $case_commit^"
	fi
	message=$(git log -1 --format=%B "$case_commit")
	git -C "$zero" add -A -f
	git -C "$zero" commit -qm "$message"
	run_base=$(git -C "$zero" rev-parse HEAD^)
	run_head=$(git -C "$zero" rev-parse HEAD)
	run_diff=$run_base...$run_head
	run_from=$run_base
}

run_once() {
	local zero=$1
	fill_prompt >"$tmp/prompt"
	printf '\nFor this eval, return text instead of the structured output: write each finding on one line as `<file>:<line>: <one sentence>`, where `<file>` is the path in the diff and `<line>` is a line number in the new version of the file. Write `none` when you find nothing.\n' >>"$tmp/prompt"
	( cd "$zero" && "${reviewer_cmd[@]}" ) <"$tmp/prompt" >"$tmp/out" 2>"$tmp/err"
}

for dir in "$cases"/*/; do
	[ -d "$dir" ] || continue
	[ -f "$dir/case.md" ] || die "$dir has no case.md"
	read_case "$dir"
	case_dir=$(cd "$dir" && pwd)
	name=$(basename "$dir")
	git rev-parse --verify "$case_commit^{commit}" >/dev/null 2>&1 || die "$dir: **Broke main:** $case_commit is not in this repo"
	case_commit=$(git rev-parse "$case_commit")
	case_tmp=$tmp/work
	make_work "$case_dir" "$case_tmp"
	result=
	first=1
	while :; do
		set +e
		run_once "$case_tmp"
		code=$?
		set -e
		if [ "$show" = 1 ] && [ -s "$tmp/out" ]; then
			printf '%s output:\n' "$name" >&2
			cat "$tmp/out" >&2
		fi
		if [ "$code" -ne 0 ]; then
			printf 'review-eval: %s: reviewer exited %s\n' "$name" "$code" >&2
			[ -s "$tmp/err" ] && tail -n 5 "$tmp/err" >&2
			if [ "$first" = 1 ]; then
				printf 'review-eval: %s: one fresh run\n' "$name" >&2
				first=0
				continue
			fi
			result=error
			break
		fi
		if grade "$tmp/out"; then
			result=caught
			break
		fi
		if [ "$first" = 1 ]; then
			printf 'review-eval: %s: first run missed; one fresh run\n' "$name" >&2
			first=0
			continue
		fi
		result=missed
		break
	done
	case "$result" in
		caught)
			printf '%s caught\n' "$name"
			printf '%s\n' "$name" >>"$tmp/caught"
			n_caught=$((n_caught + 1))
			;;
		missed)
			printf '%s missed\n' "$name"
			n_missed=$((n_missed + 1))
			;;
		*)
			printf '%s missed\n' "$name"
			n_missed=$((n_missed + 1))
			n_error=$((n_error + 1))
			;;
	esac
	rm -rf "$case_tmp"
done

printf 'review-eval: %s caught, %s missed\n' "$n_caught" "$n_missed"

[ "$n_error" -gt 0 ] && exit 2

if [ "$update" = 1 ]; then
	if [ -f "$baseline" ]; then
		sort -u "$baseline" "$tmp/caught" >"$tmp/baseline"
	else
		sort -u "$tmp/caught" >"$tmp/baseline"
	fi
	cp "$tmp/baseline" "$baseline"
	printf 'review-eval: baseline updated at %s\n' "$baseline"
fi

if [ "$compare" = 1 ]; then
	n_regressed=0
	while IFS= read -r name; do
		name=$(trim "$name")
		[ -n "$name" ] || continue
		if ! grep -qxF "$name" "$tmp/caught"; then
			printf 'review-eval: %s was caught in the baseline and is now missed\n' "$name" >&2
			n_regressed=$((n_regressed + 1))
		fi
	done < <(baseline_names)
	[ "$n_regressed" -eq 0 ] || exit 1
fi
