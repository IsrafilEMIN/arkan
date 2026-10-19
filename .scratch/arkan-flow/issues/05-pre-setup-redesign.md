# 05: grill the pre-setup redesign

**Role:** ready-for-human
**Closed:** yes
**Priority:** 10

**What to build:** a grilled design for `pre-setup` as an interactive checklist (a playbook it runs with the user) that sets up the machine and each repo for the whole arkan flow, safe to run again at any time. the result updates `skills/pre-setup/` and unblocks ticket 06. numbers 09 to 18 below are sections of the parked spec `.scratch/review-ci/spec.md`.

**Blocked by:** None (can start immediately). a person must take part (grilling).

brainstorm to start the grill from:

- **two scopes.** machine scope, once per machine: install or update (ticket 04), harness links (06), name-clash scan (17). repo scope, once per repo: tracker, labels, domain docs, board, change log (today's sections a to e), then the new ones below. question: one skill with two scopes, or two skills (`arkan-install` for the machine, `pre-setup` for the repo)?
- **new repo sections.** f: sensitive-path list (12). g: files the agent must not change (13). h: ci jobs for the review runner and post-merge (09, 08). i: repo host settings (14). j: how many people approve, and the rule for `high` (16). k: is there a verify skill? if not, tell the person to run `create-verification` (15).
- **one shape per section.** detect what is there, recommend, ask only when the choice branches, show the draft, write, then check that the write took effect. each section is idempotent: a re-run with nothing to change changes nothing.
- **a check mode.** a re-run first reports drift (a missing file, a setting turned off, a stale link) section by section, and fixes only what the person accepts.
- **where answers live.** today in `docs/agents/*.md` and the `AGENTS.md` block. new answers (people count, tier rule, sensitive paths) need one home each.
- **file layout.** a short `SKILL.md` that routes, a `checklist.md` with one block per section, and reference files (`harnesses.md`, seeds). the agent copies the checklist into its todo list, like a playbook.
- **outward actions.** changing repo host settings or pushing ci files is outward-facing: pre-setup shows the exact change and asks before each one.

questions for the grill:

1. one skill or two (machine and repo)?
2. does pre-setup write the ci workflow files itself, or only propose them?
3. where does the guard repo live, and what does pre-setup hand to it?
4. which host settings does it change itself, and which does it only print steps for?
5. is check mode the default on a re-run?

- [x] each question above has an answer recorded here
- [x] the section list, their order, and each section's shape are agreed
- [x] ticket 06, and sections 12, 13, 14 and 16 of the parked spec, are updated to match

## Answer

grilled with the owner on 2026-10-19. the build is ticket 41; the risk tier is ticket 42.

**the questions above:**

1. one skill or two: one skill, `pre-setup`, plus a script it owns. no `arkan-install`.
2. ci workflow files: pre-setup copies them in; pushing them asks first.
3. guard repo: underground (`IsrafilEMIN/underground`). it reads each repo's sensitive-path list and blocks the agent's edits to those paths; pre-setup writes the list.
4. host settings: pre-setup makes each change itself, after it shows the exact change and the person says yes.
5. check mode is the default on a re-run.

**shape:**

- `skills/pre-setup/` holds `SKILL.md`, `scripts/setup.sh` and `references/` (the seeds move there).
- `setup.sh check` reports each item, machine first (from any repo), then the repo: `ok`, `missing`, or `out of date`. `setup.sh apply <item>` installs an item that has no choice.
- the skill runs the script, skips each `ok` item, asks the person about each item that has a choice, and writes the docs.
- a local install needs no question. a change on the host (github, gitlab) shows the exact change and asks first, even when there is no choice.
- a re-run checks every item for `missing`. only the ci workflow files that pre-setup copied are checked for `out of date` against arkan's copy, and the skill asks before it updates one. the person's docs and the host settings are not checked for drift.
- after the repo sections, the skill shows the whole diff and commits after a yes. a push asks again.
- first run on a new machine: ticket 04's one command (clone arkan, run `setup.sh`), which also installs the claude code plugin; then `/arkan:pre-setup` in each repo.

**sections, in order:**

| # | section | asks the person? |
|---|---|---|
| 1 | arkan installed and current: the plugin in claude code, `~/.agents/skills/` elsewhere (04) | no |
| 2 | harnesses (06): claude code gets the plugin, no links in `~/.claude/skills/` | which harnesses |
| 3 | name clashes (17) | only when one is found |
| 4 | git repo (`git init`) | yes |
| 5 | issue tracker | yes, which type |
| 6 | triage labels: the five defaults | no; creating them on a host asks first |
| 7 | domain docs, plus `GLOSSARY.md merge=union` in `.gitattributes` | no |
| 8 | board: `TODO.md`. a local tracker builds it with the skill's own `board.sh` (no copy in the repo); a github or gitlab tracker keeps a hand-written board | no |
| 9 | sensitive-path list, `docs/agents/sensitive-paths.md`, one path per line. defaults: every ci workflow file, installers, auth, billing, release workflows | yes, the person approves the list |
| 10 | approval rule, `docs/agents/approvals.md`: two labels, `auto` and `manual`. a sensitive path is always `manual`. the trusted author is the owner only; anyone else's pr is `manual`. an agent's `PASS` never counts as the person's | no, the rule is fixed |
| 11 | `REVIEW.md` seed | no |
| 12 | ci jobs: the review job (30) and the test job (38) | before the push |
| 13 | merge gate (34), branch protection with "dismiss stale approvals", codeowners for the sensitive paths | before each change |
| 14 | pointers only: `create-verification` when there is no verify skill; `setup-pre-commit` for a js/ts repo with no hooks | no, changes nothing |

dropped: the change-log section (the tickets and the git log already record changes), a pull request template (the `pr` skill owns it; ticket 43 adds its "how to revert" line), and the parked "how many people approve" question (the fixed two-label rule replaces it).

**source for the approval rule:** "how the claude code team does code review" (claude.dev blog, 2026-10-15): the change sets the tier, not the author; some paths always need a person; an agent's approval never counts as a person's; the person who directs the agent counts as one reviewer; an approval covers one commit; start strict. a solo repo cannot meet "two people", so arkan uses two labels.

**follow-ups:**

- arkan 41: build the redesign in `skills/pre-setup/`.
- arkan 42: the risk tier (an agent vote picks `auto` or `manual`) and the merge gate's marked-`PASS` rule. until it ships, every pr is `manual`.
- arkan 43: the `pr` skill gets a "how to revert" line.
- arkan 04, 06, 07 and `.scratch/review-ci/spec.md`: updated to match (see their comments).
- underground, drafts only, not filed (the owner files them):
  - the broker marks each verdict it posts for an agent (for example `<!-- arkan:verifier -->`) and refuses a review from an agent without the mark, so an unmarked `PASS` can only be the person's.
  - the guard reads each repo's `docs/agents/sensitive-paths.md` and denies or flags an agent's direct edit to a path on it.

## Comments

- 2026-10-18: round 1 asked, not yet answered; the owner put the grill on hold. proposed answers: (1) leave sections f to j out while `.scratch/review-ci/spec.md` is parked, add only section k now; (2) two skills, a machine skill built last with 04, 06 and 17, and `pre-setup` for the repo; (3) check mode is the default on a re-run; (4) keep one `SKILL.md` until the review-ci sections return.
- 2026-10-18: for the grill: the domain-docs section could write `GLOSSARY.md merge=union` into the repo's `.gitattributes`, as this repo does, since an agent (`domain-modeling`) adds terms.
- 2026-10-18: owner: the seed `skills/pre-setup/issue-tracker-local.md` still describes the hand-edited board; the redesign must update it to the generated board (edit the ticket, run `scripts/build-board.sh`), and decide how `pre-setup` gives a repo the two board scripts.
- 2026-10-18, owner: `setup-pre-commit` is a one-time repo setup, so `pre-setup` can take it over as a repo section (for js/ts repos), with check mode covering drift. if it should be re-run from time to time instead, it stays its own skill.
- 2026-10-19: grilled to the end with the owner; answers under `## Answer`. closed.
