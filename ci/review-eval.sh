#!/usr/bin/env bash
set -eu
cd "$(git rev-parse --show-toplevel)"
export LC_ALL=C

cases=docs/agents/review-evals
prompt=
reviewer=${REVIEW_CMD:-omp -p --no-session --tools=read,grep,glob}
default_reviewer=1
[ -n "${REVIEW_CMD:-}" ] && default_reviewer=0
baseline=
compare=0
update=0
check=0
show=0
script_dir=$(cd "$(dirname "$0")" && pwd)

usage() {
	cat <<'EOF'
usage: ci/review-eval.sh [options]

runs the ci reviewer on each case's bad.diff and prints `<case> caught` or
`<case> missed`.

  --cases DIR         case folders (default: docs/agents/review-evals)
  --prompt FILE       reviewer prompt, replacing ci/review-prompt.md
  --reviewer CMD      reviewer command, reading the prompt on stdin
                      (default: REVIEW_CMD, else
                      `omp -p --no-session --tools=read,grep,glob`)
  --baseline FILE     caught-case baseline (default: <cases>/baseline.txt)
  --compare           exit 1 when a case in the baseline is now missed
  --update-baseline   write the caught cases to the baseline
  --check             check the cases and baseline without a model
  --show              print the reviewer's output to stderr
EOF
}

die() { printf 'review-eval: %s\n' "$*" >&2; exit 2; }

while [ $# -gt 0 ]; do
	case "$1" in
		--cases) cases=${2:?}; shift 2 ;;
		--prompt) prompt=${2:?}; shift 2 ;;
		--reviewer) reviewer=${2:?}; default_reviewer=0; shift 2 ;;
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
if [ "$check" = 1 ]; then
	case_prompt=
else
	case_prompt=${prompt:-$script_dir/review-prompt.md}
	[ -f "$case_prompt" ] || die "no prompt file: $case_prompt"
	[ -n "$reviewer" ] || die "empty reviewer command"
fi

trim() { local s=$1; s=${s#"${s%%[![:space:]]*}"}; printf '%s' "${s%"${s##*[![:space:]]}"}"; }

case_path=
case_range=
case_first=
case_last=
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
	case_path=$(sed -n 's/^\*\*Path:\*\*[[:space:]]*`\([^`]*\)`.*$/\1/p' "$file" | head -n1)
	case_range=$(sed -n 's/^\*\*Lines:\*\*[[:space:]]*\([0-9][0-9]*\(-[0-9][0-9]*\)\{0,1\}\)[[:space:]]*$/\1/p' "$file" | head -n1)
	[ -n "$case_path" ] || die "$file: **Path:** needs one path in backticks"
	[ -n "$case_range" ] || die "$file: **Lines:** needs a number or a range"
	case_first=${case_range%%-*}
	case_last=${case_range#*-}
	[ "$case_last" = "$case_range" ] && case_last=$case_first
	[ "$case_first" -le "$case_last" ] || die "$file: **Lines:** starts after it ends: $case_range"
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

baseline_names() {
	[ -f "$baseline" ] || return 0
	grep -vE '^[[:space:]]*(#|$)' "$baseline" || true
}

while IFS= read -r name; do
	name=$(trim "$name")
	[ -n "$name" ] || continue
	[ -f "$cases/$name/case.md" ] || die "baseline names a missing case: $name"
done < <(baseline_names)

if [ "$check" = 1 ]; then
	printf 'review-eval: ok (%s case(s))\n' "$n_cases"
	exit 0
fi

n_cases=0
for dir in "$cases"/*/; do
	[ -d "$dir" ] || continue
	[ -f "$dir/case.md" ] || continue
	n_cases=$((n_cases + 1))
done
[ "$n_cases" -gt 0 ] || die "no cases in $cases"

if [ "$default_reviewer" = 1 ]; then
	command -v omp >/dev/null || die "omp is not on PATH; set REVIEW_CMD to a headless reviewer"
fi

read -r -a reviewer_cmd <<<"$reviewer"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
: >"$tmp/caught"
n_caught=0
n_missed=0
n_error=0

grade() {
	awk -v path="$case_path" -v first="$case_first" -v last="$case_last" '
		{
			s = $0
			while ((i = index(s, path)) > 0) {
				s = substr(s, i + length(path))
				if (match(s, /^[^0-9]{0,12}[0-9]+(-[0-9]+)?/)) {
					seg = substr(s, RSTART, RLENGTH)
					gsub(/[^0-9-]/, "", seg)
					split(seg, part, "-")
					a = part[1] + 0
					b = part[2] + 0
					if (part[2] == "") b = a
					if (a <= last + 0 && b >= first + 0) { found = 1; exit }
				}
			}
		}
		END { exit(found ? 0 : 1) }' "$1"
}

for dir in "$cases"/*/; do
	[ -d "$dir" ] || continue
	[ -f "$dir/case.md" ] || die "$dir has no case.md"
	read_case "$dir"
	name=$(basename "$dir")
	{
		cat "$case_prompt"
		printf '\n\nThe diff:\n\n```diff\n'
		cat "$dir/bad.diff"
		printf '\n```\n\nWrite each finding on one line, as `<file>:<line>: <one sentence>`, where `<file>` is the path in the diff and `<line>` is a line number in the new version of the file (the `+` side). If you find nothing, write `none`.\n'
	} >"$tmp/prompt"
	set +e
	"${reviewer_cmd[@]}" <"$tmp/prompt" >"$tmp/out" 2>"$tmp/err"
	code=$?
	set -e
	if [ "$show" = 1 ] && [ -s "$tmp/out" ]; then
		printf '%s output:\n' "$name" >&2
		cat "$tmp/out" >&2
	fi
	if [ "$code" -ne 0 ]; then
		printf 'review-eval: %s: reviewer exited %s\n' "$name" "$code" >&2
		[ -s "$tmp/err" ] && tail -n 5 "$tmp/err" >&2
		printf '%s missed\n' "$name"
		n_missed=$((n_missed + 1))
		n_error=$((n_error + 1))
		continue
	fi
	if grade "$tmp/out"; then
		printf '%s caught\n' "$name"
		printf '%s\n' "$name" >>"$tmp/caught"
		n_caught=$((n_caught + 1))
	else
		printf '%s missed\n' "$name"
		n_missed=$((n_missed + 1))
	fi
done

printf 'review-eval: %s caught, %s missed\n' "$n_caught" "$n_missed"

[ "$n_error" -gt 0 ] && exit 2

if [ "$update" = 1 ]; then
	sort "$tmp/caught" >"$baseline"
	printf 'review-eval: baseline written to %s\n' "$baseline"
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
