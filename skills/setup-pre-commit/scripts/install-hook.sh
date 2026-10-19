#!/bin/sh
# arkan setup-pre-commit
set -eu

marker='# arkan setup-pre-commit'

usage() {
	printf 'usage: install-hook.sh <rust|python|go> [repo-root]\n' >&2
	exit 2
}

[ $# -ge 1 ] || usage
lang=$1
root=${2:-$(pwd -P)}
[ -d "$root" ] || { printf 'install-hook: no directory %s\n' "$root" >&2; exit 2; }
root=$(cd "$root" && pwd -P)

case "$lang" in
	rust | python | go) ;;
	js | ts | js/ts | javascript | typescript)
		printf 'install-hook: js/ts uses husky + lint-staged + prettier; follow the skill steps for it\n' >&2
		exit 2
		;;
	*)
		printf 'install-hook: unsupported language %s; use rust, python or go\n' "$lang" >&2
		exit 2
		;;
esac

git -C "$root" rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
	printf 'install-hook: %s is not a git work tree\n' "$root" >&2
	exit 2
}

if local_hooks=$(git -C "$root" config --local --get core.hooksPath 2>/dev/null); then
	case "$local_hooks" in
		"~") local_hooks="$HOME" ;;
		"~/"*) local_hooks="$HOME/${local_hooks#\~/}" ;;
	esac
	case "$local_hooks" in
		/*) ;;
		*) local_hooks="$root/$local_hooks" ;;
	esac
else
	local_hooks=$(git -C "$root" rev-parse --git-common-dir)
	case "$local_hooks" in
		/*) ;;
		*) local_hooks="$root/$local_hooks" ;;
	esac
	local_hooks="$local_hooks/hooks"
fi
hooks=$local_hooks

case "$hooks" in
	"$root" | "$root"/*) ;;
	*) printf 'install-hook: warning: %s is outside %s, so this hook runs for every repo that shares it\n' "$hooks" "$root" >&2 ;;
esac

hook="$hooks/pre-commit"
mkdir -p "$hooks"
tmp=$(mktemp "$hooks/.pre-commit.XXXXXX")
trap 'rm -f "$tmp"' 0

case "$lang" in
	rust)
		cat >"$tmp" <<'HOOK'
#!/bin/sh
# arkan setup-pre-commit
set -eu
cd "$(git rev-parse --show-toplevel)"
staged="$(git -c core.quotePath=false diff --cached --name-only --diff-filter=ACMR -- '*.rs')"
[ -n "$staged" ] || exit 0
status=0
while IFS= read -r f; do
	[ -n "$f" ] || continue
	if ! git diff --quiet -- "$f"; then
		printf 'pre-commit: %s has unstaged changes; stage the whole file first\n' "$f" >&2
		status=1
	fi
done <<EOF
$staged
EOF
[ "$status" = 0 ] || exit 1
cargo fmt --check
cargo clippy --workspace -- -D warnings
HOOK
		;;
	python)
		cat >"$tmp" <<'HOOK'
#!/bin/sh
# arkan setup-pre-commit
set -eu
cd "$(git rev-parse --show-toplevel)"
staged="$(git -c core.quotePath=false diff --cached --name-only --diff-filter=ACMR -- '*.py')"
[ -n "$staged" ] || exit 0
status=0
while IFS= read -r f; do
	[ -n "$f" ] || continue
	if ! git diff --quiet -- "$f"; then
		printf 'pre-commit: %s has unstaged changes; stage the whole file first\n' "$f" >&2
		status=1
		continue
	fi
	ruff format --check --force-exclude -- "./$f" || status=1
	ruff check --force-exclude -- "./$f" || status=1
done <<EOF
$staged
EOF
[ "$status" = 0 ]
HOOK
		;;
	go)
		cat >"$tmp" <<'HOOK'
#!/bin/sh
# arkan setup-pre-commit
set -eu
cd "$(git rev-parse --show-toplevel)"
staged="$(git -c core.quotePath=false diff --cached --name-only --diff-filter=ACMR -- '*.go')"
[ -n "$staged" ] || exit 0
status=0
while IFS= read -r f; do
	[ -n "$f" ] || continue
	if ! git diff --quiet -- "$f"; then
		printf 'pre-commit: %s has unstaged changes; stage the whole file first\n' "$f" >&2
		status=1
		continue
	fi
	if [ -n "$(gofmt -l "./$f")" ]; then
		printf 'gofmt needs to format %s\n' "$f" >&2
		status=1
	fi
done <<EOF
$staged
EOF
[ "$status" = 0 ] || exit 1
set --
seen=""
while IFS= read -r f; do
	[ -n "$f" ] || continue
	d=$(dirname "./$f")
	case "$seen" in
		*" $d"*) continue ;;
	esac
	seen="$seen $d"
	set -- "$@" "$d"
done <<EOF
$staged
EOF
go vet "$@"
HOOK
		;;
esac

if [ -e "$hook" ] && cmp -s "$tmp" "$hook"; then
	chmod +x "$hook"
	printf 'hook unchanged: %s\n' "$hook"
	exit 0
fi

if [ -e "$hook" ]; then
	if grep -qxF "$marker" "$hook" 2>/dev/null; then
		printf 'install-hook: %s was edited after arkan wrote it\n' "$hook" >&2
	else
		printf 'install-hook: %s exists and arkan did not write it\n' "$hook" >&2
	fi
	printf -- '--- %s ---\n' "$hook" >&2
	cat "$hook" >&2
	printf -- '--- end ---\n' >&2
	printf 'install-hook: show it to the user and ask before replacing it; nothing changed\n' >&2
	exit 1
fi

chmod 755 "$tmp"
mv "$tmp" "$hook"
printf 'hook written: %s\n' "$hook"
