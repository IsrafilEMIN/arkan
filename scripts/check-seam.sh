#!/usr/bin/env bash
# check-seam: fail when arkan drifts from docs/seam.md (underground adr 0002).
# it reads only arkan's own files.
set -eu
cd "$(git rev-parse --show-toplevel)"
seam=docs/seam.md
fail=0
bad() { printf 'check-seam: %s\n' "$1" >&2; fail=1; }

# this script is skipped too: its patterns name what they look for.
files=$(git ls-files | grep -v '^\.scratch/' | grep -vxF -e "$seam" -e scripts/check-seam.sh || true)

# 1. every agent-gh verb a file names is in row 2's list.
verbs=$(grep "^Row 2's verbs" "$seam" | grep -oE '`[a-z-]+`' | tr -d '`')
[ -n "$verbs" ] || bad "$seam has no \"Row 2's verbs\" line"
while IFS=: read -r f n verb; do
	[ -n "$verb" ] || continue
	verb=${verb#agent-gh }
	printf '%s\n' "$verbs" | grep -qx "$verb" || bad "$f:$n: agent-gh $verb is not a row 2 verb"
done < <(printf '%s\n' "$files" | xargs grep -noE 'agent-gh [a-z][a-z-]*' 2>/dev/null || true)

# 2. row 6's strings, exactly as the seam writes them.
mark=$(grep -oE '<!-- arkan:verifier -->' "$seam" | head -n1)
[ -n "$mark" ] || bad "$seam has no agent mark"
grep -qF 'arkan:risk head=<sha> label=<auto\|manual> -->' "$seam" || bad "$seam has no risk marker"
for f in ci/github/arkan-merge.yml .github/workflows/arkan-merge.yml; do
	[ -f "$f" ] || continue
	grep -qF "AGENT_MARK: \"$mark\"" "$f" || bad "$f: AGENT_MARK is not $mark"
	grep -qF '"<!-- arkan:risk head=$HEAD label=auto -->"' "$f" || bad "$f: the risk marker it reads is not row 6's"
done
for f in ci/github/arkan-risk.yml .github/workflows/arkan-risk.yml; do
	[ -f "$f" ] || continue
	grep -qF "'<!-- arkan:risk head=%s label=%s -->" "$f" || bad "$f: the risk marker it writes is not row 6's"
done

# 3. no file outside .scratch/ names a path inside underground.
while IFS= read -r hit; do
	[ -n "$hit" ] && bad "${hit%%:*}:$(printf '%s' "$hit" | cut -d: -f2): names a path inside underground; cite a seam row"
done < <(printf '%s\n' "$files" | xargs grep -noE 'parts/(gh-broker|agent-[a-z-]+)|staged/[0-9]+|probes/[a-z_]+\.(py|sh)|THREAT-MODEL\.md|docs/adr/0002' 2>/dev/null || true)

[ "$fail" = 0 ] && echo "check-seam: ok"
exit "$fail"
