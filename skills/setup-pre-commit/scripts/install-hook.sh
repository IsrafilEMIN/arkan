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

hooks=$(git -C "$root" rev-parse --git-path hooks)
case "$hooks" in
	/*) ;;
	*) hooks="$root/$hooks" ;;
esac
hook="$hooks/pre-commit"

tmp=$(mktemp "${TMPDIR:-/tmp}/arkan-hook.XXXXXX")
trap 'rm -f "$tmp"' 0

case "$lang" in
	rust)
		cat >"$tmp" <<'HOOK'
#!/bin/sh
# arkan setup-pre-commit
set -eu
cd "$(git rev-parse --show-toplevel)"
staged="$(git diff --cached --name-only --diff-filter=ACMR -- '*.rs')"
[ -n "$staged" ] || exit 0
cargo fmt --check
cargo clippy
HOOK
		;;
	python)
		cat >"$tmp" <<'HOOK'
#!/bin/sh
# arkan setup-pre-commit
set -eu
cd "$(git rev-parse --show-toplevel)"
staged="$(git diff --cached --name-only --diff-filter=ACMR -- '*.py')"
[ -n "$staged" ] || exit 0
printf '%s\n' "$staged" | {
	status=0
	while IFS= read -r f; do
		[ -n "$f" ] || continue
		ruff format --check "$f" || status=1
		ruff check "$f" || status=1
	done
	exit "$status"
}
HOOK
		;;
	go)
		cat >"$tmp" <<'HOOK'
#!/bin/sh
# arkan setup-pre-commit
set -eu
cd "$(git rev-parse --show-toplevel)"
staged="$(git diff --cached --name-only --diff-filter=ACMR -- '*.go')"
[ -n "$staged" ] || exit 0
unformatted="$(printf '%s\n' "$staged" | {
	while IFS= read -r f; do
		[ -n "$f" ] || continue
		gofmt -l "$f"
	done
})"
if [ -n "$unformatted" ]; then
	printf 'gofmt -l:\n%s\n' "$unformatted" >&2
	exit 1
fi
dirs="$(printf '%s\n' "$staged" | {
	while IFS= read -r f; do
		[ -n "$f" ] || continue
		dirname "$f"
	done
} | sort -u)"
set --
for d in $dirs; do
	if [ "$d" = . ]; then
		set -- "$@" .
	else
		set -- "$@" "./$d"
	fi
done
go vet "$@"
HOOK
		;;
esac

if [ -e "$hook" ]; then
	if grep -qxF "$marker" "$hook" 2>/dev/null; then
		if cmp -s "$tmp" "$hook"; then
			chmod +x "$hook"
			printf 'hook unchanged: %s\n' "$hook"
			exit 0
		fi
	else
		printf 'install-hook: %s exists and arkan did not write it\n' "$hook" >&2
		printf -- '--- %s ---\n' "$hook" >&2
		cat "$hook" >&2
		printf -- '--- end ---\n' >&2
		printf 'install-hook: show it to the user and ask before replacing it; nothing changed\n' >&2
		exit 1
	fi
fi

mkdir -p "$hooks"
chmod 755 "$tmp"
mv "$tmp" "$hook"
printf 'hook written: %s\n' "$hook"
