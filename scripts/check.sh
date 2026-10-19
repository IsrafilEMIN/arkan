#!/usr/bin/env bash
# arkan's own check: what ci runs on each pull request (job `check`).
set -eu
cd "$(git rev-parse --show-toplevel)"
fail=0

# the board matches the tickets.
scripts/board.sh check || fail=1

# arkan matches its seam with underground (docs/seam.md).
scripts/check-seam.sh || fail=1

# every shell script parses.
while IFS= read -r f; do
	bash -n "$f" || { printf 'check: %s does not parse\n' "$f" >&2; fail=1; }
done < <(git ls-files '*.sh')

# every skill has front matter whose name is its folder.
for s in skills/*/SKILL.md; do
	dir="${s#skills/}"; dir="${dir%/SKILL.md}"
	if [ "$(head -n1 "$s")" != "---" ]; then
		printf 'check: %s has no front matter\n' "$s" >&2; fail=1; continue
	fi
	name="$(sed -n '2,/^---$/{s/^name:[[:space:]]*//p;}' "$s" | head -n1 | tr -d '"')"
	if [ "$name" != "$dir" ]; then
		printf 'check: %s names itself "%s", not "%s"\n' "$s" "$name" "$dir" >&2; fail=1
	fi
done

# every skill has agents/openai.yaml, and its policy agrees with the front matter
# (the same rule as symlink-first's link-agents.sh --check).
for d in skills/*/; do
	y="${d}agents/openai.yaml"
	if [ ! -f "$y" ]; then
		printf 'check: %s is missing\n' "$y" >&2; fail=1; continue
	fi
	manual=0 implicit_off=0
	grep -q '^disable-model-invocation:[[:space:]]*true' "${d}SKILL.md" && manual=1
	grep -q '^[[:space:]]*allow_implicit_invocation:[[:space:]]*false' "$y" && implicit_off=1
	if [ "$manual" != "$implicit_off" ]; then
		printf 'check: %s and %sSKILL.md disagree on who starts the skill\n' "$y" "$d" >&2; fail=1
	fi
done

[ "$fail" = 0 ] && echo "check: ok"
exit "$fail"
