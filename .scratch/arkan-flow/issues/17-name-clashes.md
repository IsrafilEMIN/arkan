# 17: no two skills or commands share a name

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 15

**What to build:** inventory candidate skill names for the owner's three harnesses, Claude code, Codex and Omp, and report same-name independent sources before machine linking. This is the owner's 2026-10-20 replacement for the original eight-harness scan scope. No naming changes.

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

- 2026-10-20, owner: "scan your three harnesses" replaces the eight-harness design after its three-round review loop stopped. Supported name inventories are Claude code, Codex and Omp only. Pi, Hermes, dsh, Cursor and Opencode scan traversal and config parsing are removed. Their setup and detection stay unchanged. Unsupported scanner arguments say `unverified` and do not terminate supported scans.
- 2026-10-20, agent: replaced the earlier implementation under that new decision. The earlier eight-harness smoke reports are historical, not proof of the current scope. Current record shape is `(harness, namespace, effective name, canonical source, discovery root)`, grouped within harness, namespace and name. Canonical aliases dedupe. Plugins remain separate and unscanned. Claude plain shadows cover `simplify`, `code-review` and `security-review`. No rename or prefix.
  `skills/pre-setup/harnesses.md` records the exact roots and source-backed missing-name fallback for these three. Codex uses the canonical directory name when frontmatter omits a name. Claude and Omp use the discovery directory name. Codex traversal is bounded recursive discovery through depth 6. The inventory reads simple scalar names, not arbitrary YAML, and does not validate all metadata or evaluate provider enable flags. A candidate clash is not proof every candidate loads.
  `apply arkan` adds incoming candidates for Codex and Omp only. It models owned links being replaced or removed, and follows `.claude` mirrors through those links. Foreign real directories, unowned links and direct links to old checkouts stay independent. Plain `check` inventories only on-disk state and changes no home files.
  Permanent consumer-visible regression checks are in `scripts/check-name-scan.sh`, wired into `scripts/check.sh`. They create real temp homes and call the actual scanner and setup scripts. They cover canonical aliases, independent same-name sources, first-install incoming clash before the link summary, owned upgrade plus `.claude` mirror, obsolete owned removal, foreign and unowned sources, unsupported arguments, directory-name fallback, Codex recursive discovery, `.system` exclusion and unchanged home files after plain checks.
  CLI proof: `/bin/bash /tmp/arkan17-incoming-smoke.sh`, updated to valid name-and-description frontmatter, prints `names out-of-date 1 clash(es)` with both the foreign Codex source and incoming `skills/pre-setup` before `setup: linked 84`. Its on-disk before check is clean and its after check retains the real clash. `/bin/bash /tmp/arkan17-owned-mirror-smoke.sh` prints `names ok 84 skill(s), 1 harness(es); no same-name sources` for preflight, actual apply and on-disk after check. Both the direct link and mirror resolve to the incoming checkout's `skills/pre-setup`.
  Final checks on 2026-10-20 under `/bin/bash`: `scripts/check-name-scan.sh` printed `check-name-scan: ok`; `scripts/board.sh build` wrote 54 cards; `scripts/board.sh check` printed `check-board: ok (54 cards)`; `scripts/check.sh` printed `check-board: ok (54 cards)`, `check-seam: ok`, `review-eval: ok (1 case(s))`, `check-name-scan: ok` and `check: ok`. Closed under the approved three-harness candidate-inventory scope, not as verification of all eight harnesses or every harness loader option.
  Claude mirror regression: the permanent temp-home CLI case failed before the fix with `pending claude mirrors must resolve to incoming owned source` and a false old-versus-incoming `pre-setup` clash. Existing Claude roots now use the same proposed-link model, without adding incoming Claude candidates. The test also checks the plain on-disk clash before apply, clean actual inventory after apply and an independent real foreign Claude directory. After the fix, `scripts/check.sh` passed, as did both smoke scripts above and `/bin/bash /tmp/arkan17-claude-mirror-smoke.sh`. The Claude smoke printed `names ok 1 skill(s), 1 harness(es); no same-name sources` for both proposed and actual post-apply inventories.
