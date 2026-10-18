# 22: retro turns repeated review findings into rules

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 8

**What to build:** when review keeps flagging the same kind of problem, `retro` moves the fix upstream so the problem stops being written: a check (lint rule, type, test, hook) when the rule is mechanical, else a line in the repo's `CODING_STANDARDS.md`, which `code-review` already reads. this is the job the article gives to a `REVIEW.md` file and that the dropped `learn` skill was going to do (ticket 03). no new file: `CODING_STANDARDS.md` is that file.

**Blocked by:** None (can start immediately).

today `retro` covers "the reviewer failed to catch a mistake". it has no case for "the reviewer caught the same class of mistake again and again", which costs a review round each time.

- [x] `skills/retro/SKILL.md` has a candidate for repeated findings: the same class of finding in two or more review rounds or sessions. it classifies it as mechanical (build the check) or judgment (write the standard), like the coding-standards candidate
- [x] `retro` reads the review findings of the session it looks at (the `code-review` reports in that session)
- [x] `CODING_STANDARDS.md` stays short: `retro` proposes removing a standard that a check now enforces
- [x] proof: on a session where `code-review` flagged the same problem in two rounds, `retro` proposes one check or one standard for it

## Comments

- 2026-10-18: resolved on branch `claude/ticket-22-retro-repeat-findings`. `skills/retro/SKILL.md` step 2 now also reads the `code-review` reports in the session, with each finding's tag and `file:line` (the tags from ticket 27) where it has them. step 3 has a new **Repeated findings** candidate: the same class of finding in two or more rounds or sessions, sorted as mechanical (build a check) or judgement call (one line in `CODING_STANDARDS.md`), one check or one standard per class. it counts `important` and `nit` findings, not `pre-existing` ones. the `CODING_STANDARDS.md` line under Files now says to propose removing a standard once a check enforces it. the frontmatter did not change.
- 2026-10-18, proof: simulated. i wrote the session transcript by hand: `code-review` round 1 flags `console.log` at `src/cart.ts:22` plus a nit and a spec finding; round 2 flags `console.log` at `src/checkout.ts:9` plus a `pre-existing` one at `src/log.ts:3`. a small planted repo sits next to it, with `CODING_STANDARDS.md` holding a "no `console.log` in `src/`" line, an eslint config without `no-console`, and a ci job that runs `npm run lint`. i then followed the new retro steps by hand on that transcript, with no fresh agent and no real session log.
  - result: it found one class in two rounds, `console.log` left in `src/`, and called it mechanical. it proposed one check, `no-console: error` in `.eslintrc.json` with `src/log.ts` exempt (already wired, since ci runs lint), and proposed removing the matching line from `CODING_STANDARDS.md`. the nit, the spec finding and the `pre-existing` finding gave no candidate.
  - limit: the same agent wrote the skill text, the transcript and the retro run. eslint was not run, so the rule is checked by reading only. a run on a real session in a fresh context is still worth doing.
