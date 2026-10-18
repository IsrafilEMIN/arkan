# 16: approval rule for high-tier prs in a repo with one person

**What to build:** `pre-setup` asks how many people can approve prs in this repo, and records a rule for `high` that the repo can meet.

**Blocked by:** 05

options to offer when there is one person (recommended first):

1. **you plus a wait plus an outside check.** you approve, the pr waits a fixed time (for example 24 hours), and a fresh verifier agent that did not write the code runs the change the way a user would and posts a pass (pstack's shipping playbook does this).
2. **you plus one named outside reviewer** for `high` paths only.
3. **no auto path for `high`.** you merge it by hand after your own review.

- [ ] pre-setup asks the question and records the answer where ticket 05 decides
- [ ] the approval step (node 7) reads the recorded rule
- [ ] the github self-approval limit from ticket 14 is handled
