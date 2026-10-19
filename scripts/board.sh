#!/usr/bin/env bash
set -eu

verb=${1:-}
case "$verb" in
	build) prefix=build-board ;;
	check) prefix=check-board ;;
	*)
		printf 'usage: board.sh <build|check> [repo-root]\n' >&2
		exit 2
		;;
esac
shift
root="${1:-$(git -C "$(dirname "$0")" rev-parse --show-toplevel)}"
board="$root/TODO.md"

problems=0
fail() { printf '%s: %s\n' "$1" "$2" >&2; problems=$((problems + 1)); }
trim() { local s="$1"; s="${s#"${s%%[![:space:]]*}"}"; printf '%s' "${s%"${s##*[![:space:]]}"}"; }

roles=" needs-triage needs-info ready-for-agent ready-for-human wontfix "
types=" research prototype grilling task "

[ -d "$root/.scratch" ] || { printf '%s: no .scratch/ in %s\n' "$prefix" "$root" >&2; exit 2; }
if [ "$verb" = check ]; then
	[ -f "$board" ] || { printf '%s: no TODO.md in %s\n' "$prefix" "$root" >&2; exit 2; }
fi

t_path=() t_feat=() t_nn=() t_id=() t_title=() t_role=() t_type=() t_due=() t_closed=() t_prio=() t_refs=() t_spec=()

while IFS= read -r f; do
	rel="${f#"$root"/}" feat="${rel#.scratch/}"; feat="${feat%%/*}"
	spec=0 nn=""
	if [[ $rel == */spec.md ]]; then
		spec=1
	else
		nn="${rel##*/}"; nn="${nn%%-*}"
	fi
	title="" role="" type="" due="" closed="" prio="" refs=""
	while IFS= read -r line; do
		case "$line" in
			'## '*) break ;;
			'# '*) [ -n "$title" ] || title="${line#'# '}" ;;
			'**Role:**'*) role="$(trim "${line#'**Role:**'}")" ;;
			'**Type:**'*) type="$(trim "${line#'**Type:**'}")" ;;
			'**Due:**'*) due="$(trim "${line#'**Due:**'}")" ;;
			'**Closed:**'*) closed="$(trim "${line#'**Closed:**'}")" ;;
			'**Priority:**'*) prio="$(trim "${line#'**Priority:**'}")" ;;
			'**Blocked by:**'*)
				text="${line#'**Blocked by:**'}"
				text="${text//\`/}"
				text="$(trim "$(printf '%s' "$text" | tr '[:upper:]' '[:lower:]')")"
				text="${text%%(*}"; text="${text%% —*}"; text="${text%%. *}"; text="${text%.}"
				refs="$(trim "$text")"
				if [ "${refs%% *}" = none ]; then refs=none; fi
				;;
		esac
	done <"$f"

	if [[ ! $feat =~ ^[a-z0-9-]+$ ]]; then
		fail "$rel" "feature directory must be lowercase letters, digits or dashes, got '$feat'"
	fi
	if [ "$spec" = 1 ]; then
		if [ "$rel" != ".scratch/$feat/spec.md" ]; then
			fail "$rel" "a spec must sit at .scratch/<feature-slug>/spec.md"
		fi
	else
		if [[ ! $nn =~ ^[0-9]{2}$ ]]; then
			fail "$rel" "the file name must start with two digits, NN-<slug>.md"
		fi
		if [[ $rel != ".scratch/$feat/issues/$nn-"*.md ]]; then
			fail "$rel" "a ticket must sit at .scratch/<feature-slug>/issues/NN-<slug>.md"
		fi
	fi

	if [ "$spec" = 0 ] && [[ $title != "$nn: "* ]]; then
		fail "$rel" "heading must be '# $nn: <title>'"
	fi
	if [ "$spec" = 0 ]; then
		title="${title#"$nn: "}"
	fi
	[ -n "$title" ] || fail "$rel" "no '# ' heading"
	title="$(printf '%s' "${title:0:1}" | tr '[:lower:]' '[:upper:]')${title:1}"
	[ "$spec" = 1 ] || [[ $roles == *" $role "* ]] || [[ $types == *" $type "* ]] ||
		fail "$rel" "needs a **Role:** line (one of:${roles% }) or a **Type:** line (one of:${types% })"
	[ -z "$role" ] || [[ $roles == *" $role "* ]] || fail "$rel" "unknown role '$role'"
	[ -z "$type" ] || [[ $types == *" $type "* ]] || fail "$rel" "unknown type '$type'"
	[ -z "$due" ] || [[ $due =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || fail "$rel" "**Due:** must be YYYY-MM-DD, got '$due'"
	[[ $closed == yes || $closed == no ]] || fail "$rel" "needs a **Closed:** line, yes or no"
	[[ $prio =~ ^[0-9]+$ ]] || fail "$rel" "needs a **Priority:** line, a number"
	if [ -z "$refs" ]; then
		if [ "$spec" = 1 ]; then refs=none; else fail "$rel" "needs a **Blocked by:** line"; fi
	fi

	k=${#t_path[@]}
	t_path+=("$rel"); t_feat+=("$feat"); t_nn+=("$nn"); t_id+=("$feat $nn"); t_title+=("$title")
	t_role+=("$role"); t_type+=("$type"); t_due+=("$due"); t_closed+=("$closed")
	t_prio+=("${prio:-0}"); t_refs+=("$refs"); t_spec+=("$spec")
done < <(find "$root/.scratch" -path '*/issues/*.md' -o -name spec.md 2>/dev/null | sort)

lookup() {
	local ref="$1" home="$2" k=0
	case "$ref" in
		[0-9][0-9]) ref="$home $ref" ;;
	esac
	while [ $k -lt ${#t_id[@]} ]; do
		if [ "${t_id[$k]}" = "$ref" ]; then
			printf '%s' "$k"
			return 0
		fi
		k=$((k + 1))
	done
}

t_lane=() t_block=()
k=0
while [ $k -lt ${#t_path[@]} ]; do
	refs="${t_refs[$k]}"; ready=1; block=""; open=""
	if [ "$refs" != none ]; then
		IFS=, read -ra parts <<<"$refs"
		i=0
		while [ $i -lt ${#parts[@]} ]; do
			r="$(trim "${parts[$i]}")"
			i=$((i + 1))
			b="$(lookup "$r" "${t_feat[$k]}")"
			if [ -z "$b" ]; then
				fail "${t_path[$k]}" "blocker '$r' is not a ticket"
				continue
			fi
			block="$block $b"
			if [ "${t_closed[$b]}" = yes ]; then
				continue
			fi
			ready=0
			if [ -z "$open" ]; then open="$r"; else open="$open, $r"; fi
		done
		if [ -z "$open" ]; then t_refs[$k]=none; else t_refs[$k]="$open"; fi
	fi
	t_block+=("$block ")
	if [ "${t_spec[$k]}" = 1 ]; then ready=0; fi
	if [ "${t_role[$k]}" != ready-for-agent ] && [ "${t_role[$k]}" != ready-for-human ] && [ -z "${t_type[$k]}" ]; then
		ready=0
	fi
	if [ "${t_closed[$k]}" = yes ]; then
		t_lane+=(Done)
	elif [ $ready = 1 ]; then
		t_lane+=(Todo)
	else
		t_lane+=(Backlog)
	fi
	k=$((k + 1))
done

if [ $problems -gt 0 ]; then
	if [ "$verb" = build ]; then
		printf '%s: %s problem(s), TODO.md not written\n' "$prefix" "$problems" >&2
	else
		printf '%s: %s problem(s)\n' "$prefix" "$problems" >&2
	fi
	exit 1
fi

card() {
	local k="$1" tick=" " head="" tags="#${t_feat[$1]}"
	if [ "${t_lane[$k]}" = Done ]; then tick=x; fi
	if [ -n "${t_nn[$k]}" ]; then head="${t_nn[$k]}: "; fi
	[ -z "${t_role[$k]}" ] || tags="$tags #${t_role[$k]}"
	[ -z "${t_type[$k]}" ] || tags="$tags #${t_type[$k]}"
	[ "${t_spec[$k]}" = 0 ] || tags="$tags #spec"
	[ -z "${t_due[$k]}" ] || tags="$tags 📅 ${t_due[$k]}"
	printf -- '- [%s] %s%s %s\n  `%s` · blocked by: %s\n' "$tick" "$head" "${t_title[$k]}" "$tags" "${t_path[$k]}" "${t_refs[$k]}"
}

generate() {
	printf '# TODO\n'
	for lane in Backlog Todo Done; do
		printf '\n## %s\n' "$lane"
		order=""; left=0
		while IFS= read -r line; do
			order="$order$line"$'\n'
			left=$((left + 1))
		done < <(
			k=0
			while [ $k -lt ${#t_path[@]} ]; do
				if [ "${t_lane[$k]}" = "$lane" ]; then
					printf '%s\t%s\t%s\t%s\n' "${t_prio[$k]}" "${t_feat[$k]}" "${t_nn[$k]:-00}" "$k"
				fi
				k=$((k + 1))
			done | sort -t$'\t' -k1,1n -k2,2 -k3,3 -k4,4n
		)
		placed=" "
		while [ $left -gt 0 ]; do
			placed_one=0
			while IFS=$'\t' read -r _ _ _ k; do
				case "$placed" in
					*" $k "*) continue ;;
				esac
				wait=0
				for b in ${t_block[$k]}; do
					if [ "${t_lane[$b]}" = "$lane" ]; then
						case "$placed" in
							*" $b "*) ;;
							*) wait=1 ;;
						esac
					fi
				done
				if [ $wait = 1 ]; then continue; fi
				printf '\n'
				card "$k"
				placed="$placed$k "
				left=$((left - 1))
				placed_one=1
				break
			done <<<"$order"
			if [ $placed_one = 0 ]; then
				printf '%s: blockers in a loop in lane %s\n' "$prefix" "$lane" >&2
				exit 1
			fi
		done
	done
}

out="$(mktemp)"
trap 'rm -f "$out"' EXIT
generate >"$out"

if [ "$verb" = build ]; then
	cat "$out" >"$board"
	printf 'build-board: wrote TODO.md (%s cards)\n' "${#t_path[@]}"
elif cmp -s "$board" "$out"; then
	printf 'check-board: ok (%s cards)\n' "${#t_path[@]}"
else
	printf 'check-board: TODO.md does not match the tickets:\n' >&2
	diff -u -L TODO.md -L '(the tickets)' "$board" "$out" >&2 || true
	exit 1
fi
