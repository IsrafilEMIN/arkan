# 13: protect the review rules from the agent

**What to build:** the agent cannot weaken its own reviewer. `REVIEW.md`, the eval cases, the sensitive-path list and the ci workflow files can change only with a person's approval.

**Blocked by:** 05, 12

- [ ] these files are on the sensitive-path list with the floor "always a person"
- [ ] `pre-setup` sets codeowners (or the host's equivalent) for them, after the person agrees
- [ ] the guard repo denies or flags an agent's direct edit to them, if the guard repo can see it
- [ ] proof: an agent's pr that edits `REVIEW.md` waits for a person, whatever its tier
