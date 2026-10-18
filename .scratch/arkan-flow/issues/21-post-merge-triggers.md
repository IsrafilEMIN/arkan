# 21: what starts post-merge

**What to build:** `post-merge` (ticket 08) starts by itself, so no person has to start it after a bad merge.

**Blocked by:** 08, 05 (pre-setup decides how it offers the jobs)

what can start it (proposal: a and b together):

- a. **event:** a ci job on main. when main's ci fails, or a revert lands, it starts an agent headless (for example claude code in github actions) with the post-merge skill. fast and cheap: it runs only when something broke.
- b. **schedule:** a daily job for slow signals (error logs, incident issues). on github actions this is a `schedule` trigger; claude code on the web can also run scheduled tasks.
- c. in-session `/loop` only while a person keeps a session open. good for a test, not a base.

pushing ci files and changing repo settings are outward actions: show the exact change and ask first.

- [ ] `pre-setup` offers the ci job (a) and the scheduled job (b) per repo
- [ ] proof: a planted bad merge in a test repo gets a revert or fix pr and a ticket for the miss, with no person in the loop
