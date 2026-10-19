# 41: build the pre-setup redesign

**Role:** ready-for-agent
**Closed:** no
**Priority:** 10

**What to build:** `skills/pre-setup/` as ticket 05's `## Answer` lays it out: a routing `SKILL.md`, `scripts/setup.sh` with `check` and `apply <item>`, and the seeds moved to `references/`. the repo sections (4 to 14) come first; the machine sections (1 to 3) belong to tickets 04, 06 and 17 and plug into the same script.

**Blocked by:** None (can start immediately).

- [x] `setup.sh check` prints one line per item, `ok`, `missing` or `out of date`, and changes nothing
- [x] `setup.sh apply <item>` installs an item that has no choice; a second run changes nothing
- [ ] the skill skips each `ok` item, asks only where 05's table says it asks, and asks before any change on the host
- [x] the seed `references/issue-tracker-local.md` says to edit the ticket and run the skill's `board.sh`, not to edit the board by hand
- [x] the domain-docs section writes `GLOSSARY.md merge=union` to `.gitattributes`
- [x] `docs/agents/sensitive-paths.md` and `docs/agents/approvals.md` are written, each with a one-line entry in the `AGENTS.md` block
- [x] a re-run in a set-up repo changes nothing; a ci workflow file older than arkan's copy is offered as an update, with its diff
- [ ] after the repo sections, the skill shows the diff and commits only after a yes
- [x] proof: run in a fresh scratch repo, then again; the second run reports every item `ok` and leaves `git status` clean

## Comments
- 2026-10-19, agent: built on `claude/vigilant-cerf-35or7b` ([pr 35](https://github.com/IsrafilEMIN/arkan/pull/35)). `skills/pre-setup/` now has a routing `SKILL.md`, `scripts/setup.sh` (`check`, `apply <item>`), `scripts/board.sh` (moved from `scripts/`; `scripts/board.sh` is now a symlink to it, and with no argument it uses the current repo, not its own folder), and `references/` (the old seeds, plus `approvals.md`, `sensitive-paths.md`, `review.md`). the local seed now describes the generated board.
- 2026-10-19, proof (scratch repo): the first `check` in an empty folder printed 14 `missing`, one `hint`, one `skip`. `apply` for git, gitattributes, board, approvals, review-md and the three ci files each printed `ok`; a second `apply` left the tree byte-identical (`diff -r` empty); `apply tracker` refused with exit 2. after the skill-written files, `board.sh build` and `check` (`ok (1 cards)`), and a commit, a second `check` printed every item `ok` (verify `hint`, hooks `skip`) and `git status` was clean. an edited `.github/workflows/check.yml` read `out-of-date`; a `TODO.md` line in `.gitignore` read `missing` and `apply board` removed it.
- 2026-10-19, still open: the two boxes on the skill's own behaviour (skip `ok`, ask only where the table says, ask before host changes; commit only after a yes) are written in `SKILL.md` but not yet proven by a live agent run of `/pre-setup`. not tested on macos `/bin/bash` 3.2; the script avoids bash 4 features. ticket stays open for that run.
