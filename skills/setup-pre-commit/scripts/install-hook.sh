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
root=$(git -C "$root" rev-parse --show-toplevel)
root=$(cd "$root" && pwd -P)

canon_dir() {
	if [ -d "$1" ]; then
		cd -- "$1" && pwd -P
		return
	fi
	parent=$(dirname "$1")
	base=$(basename "$1")
	if [ -d "$parent" ]; then
		printf '%s/%s\n' "$(cd -- "$parent" && pwd -P)" "$base"
	else
		printf '%s\n' "$1"
	fi
}

if target=$(git -C "$root" config --local --path --get core.hooksPath 2>/dev/null) && [ -n "$target" ]; then
	case "$target" in
		/*) ;;
		*) target="$root/$target" ;;
	esac
else
	target=$(git -C "$root" rev-parse --git-common-dir)
	case "$target" in
		/*) ;;
		*) target="$root/$target" ;;
	esac
	target="$target/hooks"
fi
target=$(canon_dir "$target")

effective=$(git -C "$root" rev-parse --git-path hooks)
case "$effective" in
	/*) ;;
	*) effective="$root/$effective" ;;
esac
effective=$(canon_dir "$effective")

common=$(git -C "$root" rev-parse --git-common-dir)
case "$common" in
	/*) ;;
	*) common="$root/$common" ;;
esac
common=$(canon_dir "$common/hooks")

if [ "$target" != "$effective" ]; then
	if [ "$target" = "$common" ] && [ -x "$effective/pre-commit" ] && grep -q 'git-common-dir' "$effective/pre-commit" 2>/dev/null; then
		printf 'install-hook: note: git runs hooks from %s, which delegates to the repo hook\n' "$effective" >&2
	else
		printf 'install-hook: warning: git runs hooks from %s, so %s will not run until that path delegates to it\n' "$effective" "$target" >&2
	fi
fi

root_c=$(canon_dir "$root")
case "$target" in
	"$root_c" | "$root_c"/*) ;;
	*) printf 'install-hook: warning: %s is outside %s, so this hook runs for every repo that shares it\n' "$target" "$root" >&2 ;;
esac

hook="$target/pre-commit"
mkdir -p "$target"
tmp=$(mktemp "$target/.pre-commit.XXXXXX")
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
	if ! git diff --quiet -- ":(literal)$f"; then
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
	if ! git diff --quiet -- ":(literal)$f"; then
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
	if ! git diff --quiet -- ":(literal)$f"; then
		printf 'pre-commit: %s has unstaged changes; stage the whole file first\n' "$f" >&2
		status=1
		continue
	fi
	if ! out=$(gofmt -l "./$f"); then
		status=1
	elif [ -n "$out" ]; then
		printf 'gofmt needs to format %s\n' "$f" >&2
		status=1
	fi
done <<EOF
$staged
EOF
[ "$status" = 0 ] || exit 1
set --
while IFS= read -r d; do
	[ -n "$d" ] || continue
	set -- "$@" "$d"
done <<EOF
$(printf '%s\n' "$staged" | while IFS= read -r f; do
	[ -n "$f" ] || continue
	dirname "./$f"
done | sort -u)
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
