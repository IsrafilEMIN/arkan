# 29: trigger phrases for skills the agent can now start

**Role:** ready-for-agent
**Closed:** no
**Priority:** 3

**What to build:** ticket 23 made `retro` startable by both the person and the agent, and `test-to-break` by the agent only. their descriptions are still written for a person and say nothing about when the agent should start them, so the agent may never pick them up. `skills/writing-for-agents/SKILL-MECHANICS.md` says a skill the agent can start needs trigger branches in its description. rewrite both descriptions so they do.

**Blocked by:** None (can start immediately).

today:

- `retro`: "Conduct a retrospective on a coding session." `arkan-mode` section 2 may start it after review round 3, and ticket 22 gave it the repeated-findings case.
- `test-to-break`: "Suite strategy for tests - plan, audit, list, or prune; the policy the tdd engine reads when the suite shape is unsettled." `tdd` reads it.

- [ ] `skills/retro/SKILL.md` description names when the agent starts it: the same finding in review round after round, a review loop stopped at round 3, a merged change that broke main (`post-merge`), and the person asking for a retro
- [ ] `skills/test-to-break/SKILL.md` description names when the agent starts it: planning a new suite, an audit or prune of slow or flaky tests, and `tdd` finding the suite shape unsettled
- [ ] only the `description` lines change; the who-starts flags from ticket 23 stay as they are
- [ ] proof: in a fresh agent session given each trigger case, the agent starts the right skill on its own

## Comments

- 2026-10-18, owner: keep a ticket for this, though it was not agreed in detail.
