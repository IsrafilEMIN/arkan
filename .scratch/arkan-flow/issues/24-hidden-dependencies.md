# 24: catch a hidden dependency before the work is wasted

**Role:** ready-for-agent
**Closed:** no
**Priority:** 5

**What to build:** two guards against work done twice or failing because a dependency was never written down. (1) `to-tickets` writes a `touches:` line on each ticket (the folders or modules it will change), and a check asks the person about any two tickets that touch the same area with no blocking edge between them. (2) `arkan-mode` rule: a missing piece is a blocker, not a bug. when the code a task needs belongs to another open ticket, the agent stops, adds the blocker to its ticket, drops its claim and reports, instead of debugging.

**Blocked by:** None (can start immediately).

- [ ] `to-tickets` writes `touches:` and runs the overlap check before it publishes
- [ ] `arkan-mode` step 0 and the build step carry the missing-piece rule
- [ ] proof: two planted tickets that touch one module with no edge make the check ask; a task whose needed function is another open ticket's work stops and reports within one round
