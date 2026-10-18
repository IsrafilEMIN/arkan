# 22: retro turns repeated review findings into rules

**Role:** ready-for-agent
**Closed:** no
**Priority:** 8

**What to build:** when review keeps flagging the same kind of problem, `retro` moves the fix upstream so the problem stops being written: a check (lint rule, type, test, hook) when the rule is mechanical, else a line in the repo's `CODING_STANDARDS.md`, which `code-review` already reads. this is the job the article gives to a `REVIEW.md` file and that the dropped `learn` skill was going to do (ticket 03). no new file: `CODING_STANDARDS.md` is that file.

**Blocked by:** None (can start immediately).

today `retro` covers "the reviewer failed to catch a mistake". it has no case for "the reviewer caught the same class of mistake again and again", which costs a review round each time.

- [ ] `skills/retro/SKILL.md` has a candidate for repeated findings: the same class of finding in two or more review rounds or sessions. it classifies it as mechanical (build the check) or judgment (write the standard), like the coding-standards candidate
- [ ] `retro` reads the review findings of the session it looks at (the `code-review` reports in that session)
- [ ] `CODING_STANDARDS.md` stays short: `retro` proposes removing a standard that a check now enforces
- [ ] proof: on a session where `code-review` flagged the same problem in two rounds, `retro` proposes one check or one standard for it
