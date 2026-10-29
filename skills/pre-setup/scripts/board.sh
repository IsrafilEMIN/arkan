#!/usr/bin/env bash
set -eu

verb=${1:-}
case "$verb" in
	build) prefix=build-board ;;
	check) prefix=check-board ;;
	fields) prefix=fields ;;
	*)
		printf 'usage: board.sh <build|check|fields> [repo-root]\n' >&2
		exit 2
		;;
esac
shift
root="${1:-$(git rev-parse --show-toplevel)}"
board="$root/TODO.md"

problems=0
fail() { printf '%s: %s\n' "$1" "$2" >&2; problems=$((problems + 1)); }
trim() { local s="$1"; s="${s#"${s%%[![:space:]]*}"}"; printf '%s' "${s%"${s##*[![:space:]]}"}"; }

roles=" needs-triage needs-info ready-for-agent ready-for-human wontfix "
types=" research prototype grilling task "
fields=" Role Type Closed Priority Due Blocked-by "
labels=0
if [ -f "$root/docs/agents/triage-labels.md" ]; then labels=1; fi

real_date() {
	[[ $1 =~ ^([0-9]{4})-([0-9]{2})-([0-9]{2})$ ]] || return 1
	local y=$((10#${BASH_REMATCH[1]})) m=$((10#${BASH_REMATCH[2]})) d=$((10#${BASH_REMATCH[3]})) max=31
	case $m in
		4 | 6 | 9 | 11) max=30 ;;
		2) if (( (y % 4 == 0 && y % 100 != 0) || y % 400 == 0 )); then max=29; else max=28; fi ;;
		1 | 3 | 5 | 7 | 8 | 10 | 12) ;;
		*) return 1 ;;
	esac
	(( d >= 1 && d <= max ))
}

if [ "$verb" = check ]; then
	[ -f "$board" ] || { printf '%s: no TODO.md in %s\n' "$prefix" "$root" >&2; exit 2; }
fi

t_path=() t_feat=() t_nn=() t_id=() t_title=() t_role=() t_type=() t_due=() t_closed=() t_prio=() t_refs=() t_spec=()

files=""
if [ -e "$root/.scratch" ]; then
	if ! files="$(find "$root/.scratch" -type f \( -path '*/issues/*.md' -o -name spec.md \))"; then
		printf '%s: cannot read every file under .scratch/; TODO.md not changed\n' "$prefix" >&2
		exit 2
	fi
	files="$(printf '%s\n' "$files" | sort)"
fi

while IFS= read -r f; do
	[ -n "$f" ] || continue
	rel="${f#"$root"/}" feat="${rel#.scratch/}"; feat="${feat%%/*}"
	spec=0 nn=""
	if [[ $rel == */spec.md ]]; then
		spec=1
	else
		nn="${rel##*/}"; nn="${nn%%-*}"
	fi
	title="" role="" type="" due="" closed="" prio="" refs="" seen=" "
	while IFS= read -r line || [ -n "$line" ]; do
		line="${line%$'\r'}"
		if [[ $line =~ ^\*\*([^*]+):\*\* ]]; then
			name="${BASH_REMATCH[1]// /-}"
			if [[ $fields != *" $name "* ]]; then
				fail "$rel" "unknown field '**${BASH_REMATCH[1]}:**' before the first '## ' heading (known: Role, Type, Closed, Priority, Due, Blocked by; body text goes under a '## ' heading)"
			elif [[ $seen == *" $name "* ]]; then
				fail "$rel" "field '**${BASH_REMATCH[1]}:**' appears twice"
			fi
			seen="$seen$name "
		fi
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
				text="${text%% —*}"; text="${text%%. *}"; text="${text%.}"
				IFS=, read -ra parts <<<"$text"
				text=""
				for part in "${parts[@]+"${parts[@]}"}"; do
					part="$(trim "${part%%(*}")"
					[ -z "$part" ] || text="${text:+$text, }$part"
				done
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
	elif [[ ${rel##*/} =~ ^([0-9]{2})- ]]; then
		nn="${BASH_REMATCH[1]}"
		if [[ $rel != ".scratch/$feat/issues/$nn-"*.md ]]; then
			fail "$rel" "a ticket must sit at .scratch/<feature-slug>/issues/NN-<slug>.md"
		fi
	else
		nn=""
		fail "$rel" "the file name must be <NN>-<slug>.md, two digits and a dash"
	fi

	if [ -n "$nn" ] && [[ $title != "$nn: "* ]]; then
		fail "$rel" "heading must be '# $nn: <title>'"
	fi
	if [ "$spec" = 0 ] && [ -n "$nn" ]; then
		title="${title#"$nn: "}"
	fi
	[ -n "$title" ] || fail "$rel" "no '# ' heading"
	title="$(printf '%s' "${title:0:1}" | tr '[:lower:]' '[:upper:]')${title:1}"
	[ "$spec" = 1 ] || [ $labels = 0 ] || [[ $roles == *" $role "* ]] || [[ $types == *" $type "* ]] ||
		fail "$rel" "needs a **Role:** line (one of:${roles% }) or a **Type:** line (one of:${types% })"
	[ -z "$role" ] || [[ $roles == *" $role "* ]] || fail "$rel" "unknown role '$role'"
	[ -z "$type" ] || [[ $types == *" $type "* ]] || fail "$rel" "unknown type '$type'"
	[ -z "$due" ] || real_date "$due" || fail "$rel" "**Due:** must be a real date, YYYY-MM-DD, got '$due'"
	[[ $closed == yes || $closed == no ]] || fail "$rel" "needs a **Closed:** line, yes or no"
	[[ $prio =~ ^[0-9]+$ ]] || fail "$rel" "needs a **Priority:** line, a number"
	if [ -z "$refs" ]; then
		if [ "$spec" = 1 ]; then refs=none; else fail "$rel" "needs a **Blocked by:** line"; fi
	fi

	for seen in "${t_id[@]+"${t_id[@]}"}"; do
		if [ "$spec" = 0 ] && [ -n "$nn" ] && [ "$seen" = "$feat $nn" ]; then
			fail "$rel" "ticket number $nn is used twice in .scratch/$feat/issues/"
		fi
	done

	k=${#t_path[@]}
	t_path+=("$rel"); t_feat+=("$feat"); t_nn+=("$nn"); t_id+=("$feat $nn"); t_title+=("$title")
	t_role+=("$role"); t_type+=("$type"); t_due+=("$due"); t_closed+=("$closed")
	t_prio+=("${prio:-0}"); t_refs+=("$refs"); t_spec+=("$spec")
done <<<"$files"

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
	if [ $labels = 1 ] && [ "${t_role[$k]}" != ready-for-agent ] && [ "${t_role[$k]}" != ready-for-human ] && [ -z "${t_type[$k]}" ]; then
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

card() {
	local k="$1" tick=" " head="" tags="#${t_feat[$1]}"
	if [ "${t_lane[$k]}" = Done ]; then tick=x; fi
	if [ -n "${t_nn[$k]}" ]; then head="${t_nn[$k]}: "; fi
	[ -z "${t_role[$k]}" ] || tags="$tags #${t_role[$k]}"
	[ -z "${t_type[$k]}" ] || tags="$tags #${t_type[$k]}"
	[ "${t_spec[$k]}" = 0 ] || tags="$tags #spec"
	[ -z "${t_due[$k]}" ] || tags="$tags 📅 ${t_due[$k]}"
	local title="${t_title[$k]//#/＃}"
	printf -- '- [%s] %s%s %s\n  `%s` · blocked by: %s\n' "$tick" "$head" "$title" "$tags" "${t_path[$k]}" "${t_refs[$k]}"
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

if [ $problems -gt 0 ]; then
	if [ "$verb" = build ]; then
		printf '%s: %s problem(s), TODO.md not written\n' "$prefix" "$problems" >&2
	else
		printf '%s: %s problem(s)\n' "$prefix" "$problems" >&2
	fi
	exit 1
fi

if [ "$verb" = fields ]; then
	generate >/dev/null
	printf 'fields: ok (%s cards)\n' "${#t_path[@]}"
	exit 0
fi

out="$(mktemp "$root/.TODO.md.XXXXXX")"
trap 'rm -f "$out"' EXIT
generate >"$out"

if [ "$verb" = build ]; then
	if [ -f "$board" ] && cmp -s "$board" "$out"; then
		printf 'build-board: TODO.md is up to date (%s cards)\n' "${#t_path[@]}"
		exit 0
	fi
	chmod 644 "$out"
	mv -f "$out" "$board"
	printf 'build-board: wrote TODO.md (%s cards)\n' "${#t_path[@]}"
elif cmp -s "$board" "$out"; then
	printf 'check-board: ok (%s cards)\n' "${#t_path[@]}"
else
	printf 'check-board: TODO.md does not match the tickets:\n' >&2
	diff -u -L TODO.md -L '(the tickets)' "$board" "$out" >&2 || true
	exit 1
fi
