# 41: build the pre-setup redesign

**Role:** ready-for-agent
**Closed:** no
**Priority:** 10

**What to build:** `skills/pre-setup/` as ticket 05's `## Answer` lays it out: a routing `SKILL.md`, `scripts/setup.sh` with `check` and `apply <item>`, and the seeds moved to `references/`. the repo sections (4 to 14) come first; the machine sections (1 to 3) belong to tickets 04, 06 and 17 and plug into the same script.

**Blocked by:** None (can start immediately).

- [x] `setup.sh check` prints one line per item, `ok`, `missing` or `out of date`, and changes nothing
- [x] `setup.sh apply <item>` installs an item that has no choice; a second run changes nothing
- [x] the skill skips each `ok` item, asks only where 05's table says it asks, and asks before any change on the host
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
- 2026-10-19, owner (underground, macos): the installed skill was updated (`arkan-install` at `734617e`), then `/bin/bash ~/.agents/skills/pre-setup/scripts/setup.sh check` ran clean on the macos system bash: `git`, `tracker`, `labels`, `domain`, `agents-block` and `board` `ok`; `gitattributes`, `sensitive-paths`, `approvals`, `review-md`, the four ci items and `codeowners` `missing`; `verify` `hint`; `hooks` `skip`. the earlier underground run (its pr 32) used the old, pre-41 skill copy, so it is not evidence for this ticket.
- 2026-10-19, agent: that run showed a gap: `ci-check` read `missing` in a repo that already runs its own ci (underground's `ci.yml`), and copying `check.yml` there would fail on every pr (`bash scripts/check.sh` does not exist). `setup.sh` now reports `ci-check` as a `hint` naming the repo's own workflow files when any exist besides arkan's; `SKILL.md` says to keep them. proof in a scratch repo: no workflows → `missing`; `ci.yml` → `hint` naming it; arkan's files alone → `missing`; `apply ci-check` still → `ok`.
- 2026-10-19, owner (underground, live session, its pr 33): the updated skill skipped the six `ok` items (git, tracker, labels, domain, agents-block, board) without a question, set up every missing item, asked the owner to approve the sensitive-path list (approved with `install.sh`, `bootstrap.sh`, `parts/**`, the srt settings, `VERSIONS` and `THREAT-MODEL.md` added), and asked about the branch rule (owner: not now). the broker refused its push of the workflow files (the broker token has no `workflow` scope, on purpose); the owner pushed from tab 2. pr 33 then merged through underground's new gate on the owner's `PASS` (`github-actions[bot]`, `975f170`).
- 2026-10-19, agent: two bugs from that run, fixed here. (1) the skill copied `arkan-review.yml` without the `CLAUDE_CODE_OAUTH_TOKEN` secret, so `arkan-review` failed and would have blocked every merge; `SKILL.md` now offers `ci-review` only when the secret and `.claude/skills/` exist. (2) the session uncommented `check.yml`'s example `setup-python` pin, which github could not resolve (`Unable to resolve action actions/setup-python@2499707…`); the example pins in `check.yml` are now placeholders that say to copy a real release sha. both workflow files were removed from underground's pr 33 before it merged.
- 2026-10-19, agent: arkan's own items set up the same way (`setup.sh apply approvals`, `apply review-md`, plus `docs/agents/sensitive-paths.md`, `.github/CODEOWNERS`, `REVIEW.md` and the `AGENTS.md` pointers); `setup.sh check` now reads every item `ok` except `ci-review` (deferred with 42), `verify` (`hint`) and `hooks` (`skip`).
