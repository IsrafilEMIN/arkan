# 01: implement mental models into the arkan skillset

**Role:** needs-triage
**Closed:** no
**Priority:** 27

**What to build:** the arkan skillset carries mental models: the thinking frames an agent applies when it judges a design, a plan, a decision or a failure. a frame an agent holds while it works, not another procedure to follow.

origin: owner request, 2026-10-18: "implement mental models into the arkan skillset".

the shape is open. proposals for the owner to confirm, correct or drop:

- one agent-only skill (`mental-models`), read while working, like `codebase-design`
- one file in `arkan-mode`'s `principles/`, next to `core`, `verification`, `architecture` and `agents`, that the playbooks point at
- lines inside the playbooks that already make these calls: `feature`, `bug-fix`, `refactoring`, `spec`, `investigation`

questions for the owner:

1. which models make the set? common candidates: inversion, second-order effects, opportunity cost, feedback loops, bottlenecks, margin of safety, Chesterton's fence.
2. does the text come written for arkan, or from a named source with its license added to `NOTICE`?
3. who applies a model: the agent mid-task, or the person who calls the skill?
4. is this the `mizan` loop (guess, predict, test, log, judge) applied to engineering work, or a set of frames separate from it?

**Blocked by:** None (can start immediately) — after the owner answers the questions above.

- [ ] the owner answers the questions; the answers are recorded here
- [ ] the agreed models live in the agreed place, and each one names where its text comes from
- [ ] every skill that should apply a model names it; `README.md` records a new skill if one lands
- [ ] proof: one real task runs with the models applied, and the run's result is recorded here
