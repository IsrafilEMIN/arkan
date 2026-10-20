#!/usr/bin/env bash
set -eu

repo="$(cd "$(dirname "$0")/.." && pwd -P)"
scanner="$repo/skills/pre-setup/scripts/name-scan.sh"
setup="$repo/skills/pre-setup/scripts/setup.sh"
base="$(mktemp -d "${TMPDIR:-/tmp}/arkan-name-tests.XXXXXX")"
trap 'rm -rf "$base"' EXIT HUP INT TERM
export PATH=/usr/bin:/bin
unset CODEX_HOME

bad() { printf 'check-name-scan: %s\n%s\n' "$1" "${out:-}" >&2; exit 1; }
has() { printf '%s\n' "$out" | grep -Fq -- "$1" || bad "$2"; }
lacks() { if printf '%s\n' "$out" | grep -Fq -- "$1"; then bad "$2"; fi; }
skill() {
	mkdir -p "$1"
	printf -- '---\nname: %s\ndescription: Regression fixture\n---\nFixture body\n' "$2" >"$1/SKILL.md"
}
new_home() { export HOME="$base/$1"; mkdir -p "$HOME"; }
scan() { out="$(/bin/bash "$scanner" "$@")"; }

new_home aliases
skill "$HOME/.agents/skills/real" shared
mkdir -p "$HOME/.claude/skills" "$HOME/.codex/skills"
ln -s "$HOME/.agents/skills/real" "$HOME/.claude/skills/alias"
ln -s "$HOME/.agents/skills/real" "$HOME/.codex/skills/alias"
scan codex omp
has 'no same-name sources' 'aliases to one source must dedupe'
lacks 'out-of-date' 'aliases must not clash'
skill "$HOME/.codex/skills/independent" shared
scan codex omp
has 'codex: shared from ' 'independent codex sources must clash'
has 'omp: shared from ' 'independent omp sources must clash'
has "$HOME/.agents/skills/real" 'clash must identify first source'
has "$HOME/.codex/skills/independent" 'clash must identify independent source'
scan pi codex hermes
has 'unverified: pi, hermes' 'unsupported harnesses must be unverified'
has 'codex: shared from ' 'unsupported arguments must not hide supported results'

new_home incoming
skill "$HOME/.codex/skills/foreign-folder" pre-setup
scan codex
lacks 'codex: pre-setup from ' 'plain check must not include incoming skills'
out="$(/bin/bash "$setup" apply arkan "$repo")"
has 'codex: pre-setup from ' 'first install must report incoming clash'
has "$repo/skills/pre-setup" 'incoming clash must identify checkout source'
case "$out" in *'codex: pre-setup from '*'setup: linked '*) ;; *) bad 'incoming clash must precede link summary' ;; esac
[ -L "$HOME/.agents/skills/pre-setup" ] || bad 'first install must actually link incoming skill'

new_home upgrade
skill "$base/old/skills/pre-setup" pre-setup
mkdir -p "$HOME/.agents/skills" "$HOME/.claude/skills" "$HOME/.codex" "$base/bin"
ln -s "$base/old/skills/pre-setup" "$HOME/.agents/skills/pre-setup"
printf 'pre-setup\t%s\n' "$base/old/skills/pre-setup" >"$HOME/.agents/skills/.arkan-links"
ln -s ../../.agents/skills/pre-setup "$HOME/.claude/skills/pre-setup"
skill "$base/old/skills/retired" pre-setup
ln -s "$base/old/skills/retired" "$HOME/.agents/skills/retired"
printf 'retired\t%s\n' "$base/old/skills/retired" >>"$HOME/.agents/skills/.arkan-links"
ln -s ../../.agents/skills/retired "$HOME/.claude/skills/retired"
printf '#!/bin/sh\nexit 0\n' >"$base/bin/omp"
chmod +x "$base/bin/omp"
scan --pending "$repo/skills" omp codex
has 'no same-name sources' 'owned upgrade and mirror must model incoming source'
lacks "$base/old/skills/pre-setup" 'owned upgrade must not retain obsolete source'
out="$(PATH="$base/bin:$PATH" /bin/bash "$setup" apply arkan "$repo")"
lacks 'out-of-date' 'actual apply must not report owned mirror clash'
[ "$(readlink "$HOME/.agents/skills/pre-setup")" = "$repo/skills/pre-setup" ] || bad 'apply must upgrade owned link'
[ "$(cd -P "$HOME/.claude/skills/pre-setup" && pwd -P)" = "$repo/skills/pre-setup" ] || bad 'mirror must follow actual upgraded link'
[ ! -L "$HOME/.agents/skills/retired" ] || bad 'apply must remove obsolete owned link'
scan omp codex
has 'no same-name sources' 'post-upgrade check must be clean'
ln -s "$base/old/skills/pre-setup" "$HOME/.claude/skills/old-direct"
scan --pending "$repo/skills" omp
has 'omp: pre-setup from ' 'direct foreign link to old checkout must stay independent'

new_home foreign
skill "$HOME/.agents/skills/pre-setup" pre-setup
skill "$base/foreign/skills/tdd" tdd
ln -s "$base/foreign/skills/tdd" "$HOME/.agents/skills/tdd"
printf 'pre-setup\t%s\n' "$base/old/skills/pre-setup" >"$HOME/.agents/skills/.arkan-links"
scan --pending "$repo/skills" codex omp
has 'codex: pre-setup from ' 'owned marker must not hide real foreign directory'
has 'omp: pre-setup from ' 'real foreign directory must clash for omp'
has 'codex: tdd from ' 'unowned link must stay independent'
has 'omp: tdd from ' 'unowned link must clash for omp'

new_home fallback
mkdir -p "$HOME/.claude/skills/fallback" "$HOME/.agents/skills/fallback" "$HOME/.codex/skills/other"
printf -- '---\ndescription: Regression fixture\n---\nFixture\n' >"$HOME/.claude/skills/fallback/SKILL.md"
cp "$HOME/.claude/skills/fallback/SKILL.md" "$HOME/.agents/skills/fallback/SKILL.md"
skill "$HOME/.codex/skills/other" fallback
scan 'claude code' codex omp
has 'codex: fallback from ' 'codex must use directory name when name omitted'
has 'omp: fallback from ' 'omp must use directory name when name omitted'
skill "$HOME/.claude/skills/other" fallback
scan 'claude code'
has 'claude code: fallback from ' 'claude must use directory name when name omitted'
mkdir -p "$HOME/.claude/skills/simplify"
printf 'A skill without frontmatter\n' >"$HOME/.claude/skills/simplify/SKILL.md"
scan 'claude code'
has 'simplify shadows built-in /simplify' 'claude fallback must retain built-in shadow reporting'

new_home bounded
skill "$HOME/.agents/skills/group/nested" nested
skill "$HOME/.codex/skills/peer" nested
skill "$HOME/.codex/skills/.system/ignored" nested
scan codex omp
has 'codex: nested from ' 'codex must discover nested candidates'
lacks 'omp: nested from ' 'omp must not recurse or include .system'
lacks '/.system/' 'codex must exclude .system'

snapshot() {
	find "$HOME" -print | LC_ALL=C sort
	find "$HOME" -type f -exec cksum '{}' \;
	find "$HOME" -type l -exec readlink '{}' \;
}
snapshot >"$base/before"
scan 'claude code' codex omp pi
out="$(/bin/bash "$setup" check "$repo")"
snapshot >"$base/after"
cmp -s "$base/before" "$base/after" || bad 'plain checks must change no home files'
printf 'check-name-scan: ok\n'
