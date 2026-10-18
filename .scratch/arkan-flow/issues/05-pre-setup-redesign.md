# 05: grill the pre-setup redesign

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

- [ ] each question above has an answer recorded here
- [ ] the section list, their order, and each section's shape are agreed
- [ ] ticket 06, and sections 12, 13, 14 and 16 of the parked spec, are updated to match

## Comments

- 2026-10-18: round 1 asked, not yet answered; the owner put the grill on hold. proposed answers: (1) leave sections f to j out while `.scratch/review-ci/spec.md` is parked, add only section k now; (2) two skills, a machine skill built last with 04, 06 and 17, and `pre-setup` for the repo; (3) check mode is the default on a re-run; (4) keep one `SKILL.md` until the review-ci sections return.
