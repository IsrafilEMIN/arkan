# 08: post-merge skill and what starts it

**What to build:** after a change merges, something watches main, and when a merged change breaks something, an agent fixes forward or reverts, asks which node should have caught it, and opens a ticket for the miss so a person can act on it (with `retro` if it needs a look back). no person has to start it.

**Blocked by:** 03

what post-merge does (from `docs/core-skills.md` node 9, now removed; see git history):

1. read the signals: ci on main, error logs or alerts the repo has, revert commits, incident issues.
2. tie a failure to the merge that caused it (the first bad commit on main).
3. make main safe: a revert pr, or a fix-forward pr, whichever is safer faster. a revert is always the fallback.
4. ask "which node should have caught this?" (review, prove, tier, ...).
5. open a ticket for the miss on the repo's tracker: the bad diff, the confirmed bug, the fix pr and the answer to step 4. (saving it as a reviewer eval case is parked with review in `.scratch/review-ci/spec.md`.)

what can start it (proposal: a and b together):

- a. **event:** a ci job on main. when main's ci fails, or a revert lands, it starts an agent headless (for example claude code in github actions) with the post-merge skill. fast and cheap: it runs only when something broke.
- b. **schedule:** a daily job for slow signals (error logs, incident issues). on github actions this is a `schedule` trigger; claude code on the web can also run scheduled tasks.
- c. in-session `/loop` only while a person keeps a session open. good for a test, not a base.

pstack parts to draw from (read in pstack's `poteto-mode` on 2026-10-18; the playbooks now live in `skills/arkan-mode/playbooks/`):

- `playbooks/orchestrate.md`: "one retro watcher follows merged PRs for reverts, post-merge CI breaks, and orphaned follow-ups". the closest idea; it lives only inside a long orchestrate run.
- `playbooks/babysit.md` and `scripts/watch-pr/`: a watcher whose output drives each wake-up, under `/loop`, with no sleep loops; and "classify ci before any retrigger" (one retry, then it is real).
- `playbooks/shipping.md` step 4: read the pr back after a merge, because a merge command can report success when the queue only queued it.
- `playbooks/autopilot-full.md` step 6: an hourly `/loop` audit that re-reads its playbook and probes each agent by what it changed, not what it says.

none of these is a full post-merge skill, so arkan writes its own and uses these as parts.

- [ ] a post-merge skill exists, with the 5 steps above
- [ ] `pre-setup` offers the ci job (a) and the scheduled job (b) per repo (ticket 05 decides how)
- [ ] proof: a planted bad merge in a test repo gets a revert or fix pr and a ticket for the miss, with no person in the loop
