# 17: no two skills or commands share a name

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 15

**What to build:** across all the harnesses a user has, no arkan skill shares a name with another skill or a built-in command, so the agent never picks the wrong one.

**Blocked by:** 04

proposal:

- `code-review` and `security-review` stay two skills (owner decision, ticket 03), so their clash with claude code's built-in `/code-review` and `/security-review` stays. needs a decision: prefix them (`arkan-code-review`, `arkan-security-review`), or keep the names and make sure the harness loads the arkan skill (check how each harness resolves a skill and a built-in with one name).
- pstack's `tdd` is not installed; `triage` stays matt's, and the after-merge skill is `post-merge`.
- add the `arkan-` prefix only where a clash with a harness's built-in command is left. no blanket prefix.
- `pre-setup` (machine scope) scans each chosen harness's skill folders and built-in commands, and reports each clash before it links anything.

- [x] the owner accepts or changes the proposal
- [x] after ticket 03, `code-review` and `security-review` keep their builtin names and load as `arkan:<name>` through the claude code plugin (owner decision)
- [x] pre-setup reports a planted clash in a test setup

## Comments

- 2026-10-18, owner: no rename and no `arkan-` prefix. what each harness does:
  - claude code: a plain skill replaces a built-in command of the same name (not its aliases); a plugin skill is named `<plugin>:<skill>`, so both stay. fix: install as a plugin (ticket 04).
  - codex: skills are called with `$name`, built-in commands with `/`, so they never clash. two skills with one name both load; a plain `$name` runs only when the name is unique.
  - pi: skills are called with `/skill:name`, so no clash with built-ins. two skills with one name: the first found wins, with a warning.
  - omp: skills are called with `/skill:name`. two skills with one name: the higher-ranked keeps the plain name, the other becomes `<namespace>/<name>`.
  left for this ticket: the scan that reports a skill-against-skill clash (pi drops one), in the machine-scope setup built with 04.
  sources read 2026-10-18: claude code <https://code.claude.com/docs/en/skills>; codex source `codex-rs/skills/src/` in <https://github.com/openai/codex> (its docs page was blocked from the cloud session); pi <https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/skills.md>; omp <https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md>.

- 2026-10-19, agent: built the scan in `skills/pre-setup/scripts/name-scan.sh`, called by `setup.sh check` as the `names` item and by `apply arkan` before its first write. shape compared: one inline `check_names()` in `setup.sh` keeps detection and `say` in one file, but puts the root table, frontmatter parser and grouping in an already 892-line script and gives no direct chosen-harness entry. the helper keeps `setup.sh` to a wrapper, is read-only, and takes harness labels as argv, so detection stays in `setup.sh` (`detect_harnesses`) and the roots live in one small table. chose the helper.
  record `(harness, namespace, declared name, canonical source, root)`; group by `(harness, namespace, declared name)`; two distinct canonical sources are a clash. links resolve with `cd -P` and `pwd -P`, so a mirror is one source. the `name:` frontmatter is read only in the first `---` block; a missing name is a hint, never a clash. codex `.system` is excluded from user skills. claude plugin skills are namespaced as `arkan:<name>` and are not scanned; only plain skills in `~/.claude/skills` are compared, so a plain builtin name is reported as a shadow. the builtin check is the minimum `simplify code-review security-review` list from `symlink-first/scripts/link-agents.sh`, applied only to claude plain skills.
  on the apply path `$arkan/skills` is also a pending source at `~/.agents/skills` for codex, pi, omp, cursor and opencode, for dsh when its root is `~/.agents`, and for hermes when its external dirs name that root; canonical dedupe keeps a rerun clean. plain `check` stays on-disk only.
  scope: the machine user roots in `harnesses.md` (claude `~/.claude/skills`; codex `~/.agents/skills` and `${CODEX_HOME:-~/.codex}/skills`; dsh `${DSH_AGENTS_HOME:-~/.agents}/skills`; pi `~/.agents/skills`; omp `~/.agents/skills`, `~/.claude/skills`, `~/.codex/skills`; cursor the same three; opencode the first two; hermes only `skills.external_dirs`). project roots, the hermes local root and plugin caches are unverified or namespaced and were not scanned; the scan says so in `SKILL.md` and `harnesses.md`. dsh is scanned when `DSH_AGENTS_HOME` names an existing skills root even if `${DSH_HOME:-~/.dsh}` is absent; the `harnesses` item keeps its old detection output.
  proof on `/bin/bash` 3.2.57 and temp homes only: 95 smoke assertions in `/tmp/arkan17-smoke.sh` (0 fail); the red-first runs of the same suite had 13 fail before the round-1 fixes and 5 fail before the round-2 fixes. coverage: planted `.agents`/`.claude` and codex/`CODEX_HOME` clashes, mirror aliases, cross-harness isolation, frontmatter name over directory name, missing name hint, plugin records ignored, plain builtin shadow, codex and omp/cursor `.system` exclusion, pending clashes for codex, pi, dsh, omp, cursor, opencode and hermes, no pending for claude, dsh outside `~/.agents`, or hermes outside `~/.agents/skills`, paths with spaces, HOME unset, absent roots, chosen harnesses, Hermes inline and list external dirs with a trailing yaml comment, a quoted `#` and the inline `["~/my #dir"]` form, pi loader pruning (dot names, `node_modules`, stop below `SKILL.md`; a nested non-skill parent still clashes), owned old-copy links relinked without a false pending clash while an unowned foreign skill still clashes, and no `claude` call. `/tmp/arkan17-incoming-smoke.sh` now prints the planted `pre-setup` clash in the apply preflight, before `setup: linked`; the same `check` before that apply still reads one source. tree hash before and after `name-scan.sh` plus `setup.sh check` on the evidence home: both `6b569947048381a7ae41a4115cb61aa83d56864a1af603ef58f73a9e92a7b7f8`. `apply arkan` on a planted clash printed `names out-of-date` on line 1 and `setup: linked ...` on line 3, so the preflight precedes the first write. `scripts/check.sh` -> `check-board: ok (54 cards)`, `check-seam: ok`, `review-eval: ok (1 case(s))`, `check: ok`.
  box 2: reworded to the owner decision. `code-review` and `security-review` keep the builtin names and load as `arkan:<name>` through the claude code plugin; a plain skill in `~/.claude/skills` with one of those names is reported as a shadow. no rename and no prefix.
