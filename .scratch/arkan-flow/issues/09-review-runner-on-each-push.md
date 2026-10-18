# 09: run review on each pr push, outside the author's session

**What to build:** on every push to an open pr, a ci job starts a fresh agent that runs the review skill (code and security lenses) on the diff and posts its findings, so the review does not depend on the author's own session.

**Blocked by:** 03

what "runner" means: before the pr (node 4), the author's agent runs review in a subagent. that is the author checking its own work. at node 6, review must run again on each push, started by something the author does not control. that something is the runner: a ci job.

- [ ] a ci workflow (written or proposed by `pre-setup`, per ticket 05) runs on pr open and on each push
- [ ] it starts a fresh agent with the review skill and posts findings as pr comments with `file:line`
- [ ] it reports a required status check, so a pr with an open `important` or security finding cannot merge
- [ ] it works on prs from forks without leaking secrets, or skips them and says so
- [ ] proof: a push to a test pr gets review comments with no session open
