#!/usr/bin/env bash
# finding-report.sh <owner/repo> [<since>]
# how arkan-review's findings ended, per tag, from the sticky comment of each pr
# (open and closed) created on or after <since> (YYYY-MM-DD; default: all).
# noise = (wrong + did-not-matter) / closed-out, where closed-out is every
# finding that is no longer open. needs `gh` (logged in) and `jq`; rest api only.
set -euo pipefail

repo=${1:?usage: finding-report.sh <owner/repo> [<since YYYY-MM-DD>]}
since=${2:-}
if [ -n "$since" ] && ! [[ $since =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  echo "since must be YYYY-MM-DD" >&2
  exit 2
fi

prs=$(gh api "repos/$repo/pulls?state=all&per_page=100" --paginate \
  --jq ".[] | select(.created_at >= \"$since\") | .number")

rows=$(mktemp)
trap 'rm -f "$rows"' EXIT
n_prs=0
for pr in $prs; do
  # the sticky comment: by github-actions[bot] only, first line the marker.
  body=$(gh api "repos/$repo/issues/$pr/comments" --paginate \
    --jq '.[] | select(.user.login == "github-actions[bot]" and (.body | startswith("<!-- arkan:review "))) | .body' \
    | jq -Rs '.')
  [ "$body" = '""' ] && continue
  n_prs=$((n_prs + 1))
  # one row per finding: pr, tag, state. an old marker (`<id>:<state>`) takes
  # the tag from the finding's line below the marker.
  jq -r --arg pr "$pr" '
    (split("\n")) as $lines
    | ($lines[0] | capture("(^| )findings=(?<f>[^ ]*)").f // "") as $f
    | ([$lines[] | capture("^- `(?<id>[0-9a-f]{8})` \\*\\*[a-z-]+\\*\\* `(?<tag>[a-z-]+)`")] | map({key: .id, value: .tag}) | from_entries) as $t
    | $f | split(",")[] | select(. != "") | split(":")
    | if length == 2 then [.[0], ($t[.[0]] // "unknown"), .[1]] else . end
    | "\($pr)\t\(.[1])\t\(.[2])"' <<< "$body" >> "$rows"
done

echo "arkan-review findings in $repo${since:+ (prs since $since)}: $n_prs prs with a review marker"
jq -Rrs '
  ["open", "fixed", "wrong", "intended", "did-not-matter"] as $states
  | [split("\n")[] | select(. != "") | split("\t") | {tag: .[1], state: .[2]}] as $all
  | (["important", "nit", "pre-existing"] + ([$all[].tag] | unique | map(select(IN("important", "nit", "pre-existing") | not)))) as $tags
  | def row($name; $fs):
      ([$states[] as $s | [$fs[] | select(.state == $s)] | length]) as $c
      | ([$fs[] | select(.state != "open")] | length) as $closed
      | ([$fs[] | select(.state == "wrong" or .state == "did-not-matter")] | length) as $noise
      | [$name] + ($c | map(tostring)) + [($closed | tostring),
          (if $closed == 0 then "-" else "\($noise * 100 / $closed | floor)%" end)];
    [(["tag"] + $states + ["closed-out", "noise"]),
     ($tags[] as $g | row($g; [$all[] | select(.tag == $g)])),
     row("all"; $all)] as $table
  # a plain table: the first column padded right, the counts padded left.
  | [range($table[0] | length) as $i | [$table[][$i] | length] | max] as $w
  | $table[] | [range(length) as $i | .[$i] as $v | (" " * ($w[$i] - ($v | length))) as $pad
      | if $i == 0 then $v + $pad else $pad + $v end] | join("  ")' "$rows"
