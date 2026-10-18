# 29: trigger phrases for skills the agent can now start

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 3

**What to build:** ticket 23 made `retro` startable by both the person and the agent, and `test-to-break` by the agent only. their descriptions are still written for a person and say nothing about when the agent should start them, so the agent may never pick them up. `skills/writing-for-agents/SKILL-MECHANICS.md` says a skill the agent can start needs trigger branches in its description. rewrite both descriptions so they do.

**Blocked by:** None (can start immediately).

today:

- `retro`: "Conduct a retrospective on a coding session." `arkan-mode` section 2 may start it after review round 3, and ticket 22 gave it the repeated-findings case.
- `test-to-break`: "Suite strategy for tests - plan, audit, list, or prune; the policy the tdd engine reads when the suite shape is unsettled." `tdd` reads it.

- [x] `skills/retro/SKILL.md` description names when the agent starts it: the same finding in review round after round, a review loop stopped at round 3, a merged change that broke main (`post-merge`), and the person asking for a retro
- [x] `skills/test-to-break/SKILL.md` description names when the agent starts it: planning a new suite, an audit or prune of slow, flaky or overlapping tests, listing what tests exist, and `tdd` finding the suite shape unsettled
- [x] the who-starts flags from ticket 23 stay as they are; beside the descriptions, only the lines the owner's decisions need change (see comments)
- [x] proof: in a fresh agent session given each description trigger, the agent starts the right skill on its own

## Comments

- 2026-10-18, owner: keep a ticket for this, though it was not agreed in detail.
- 2026-10-18, owner: `retro` starts on (a) the person asking for a retro or a look back, (b) the review loop stopping after round 3, (c) the same class of finding in a second review round, (d) `post-merge` ticketing a miss; not at the end of every long run. started by the agent, it only proposes and writes nothing. `test-to-break` stays agent only; the person reaches it by asking in words. so beside the two descriptions: `retro`'s opening line fits either starter, `test-to-break` drops "run it by hand", `arkan-mode` section 2 starts `retro` when a class of finding comes back in a second round, and `post-merge` step 6 starts `retro` instead of suggesting it.
- 2026-10-18: proof, fresh headless claude code sessions on throwaway projects with `skills/` copied into `.claude/skills/`, reading which Skill calls each made. "audit our test suite, it has slow and overlapping tests" started `test-to-break`. a look back on what went wrong started `retro` (which loaded `writing-for-agents`, as its step 1 says). "add a function that sums a list" started neither. not tested: (b), (c) and (d) are lines in `arkan-mode` and `post-merge`, checked by reading only; a staged run for (c) was cut off before it finished. ticket 19's review-loop and post-merge scenarios exercise them.
