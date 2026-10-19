# 42: risk tier picks auto or manual

**Role:** ready-for-agent
**Closed:** no
**Priority:** 27

**What to build:** each pull request gets the label `auto` or `manual`, set in ci, never by the author. a path on `docs/agents/sensitive-paths.md` makes it `manual`; for the rest, a vote of fresh-context agents picks the label, and a second check can only raise it to `manual`. the merge gate (`ci/github/arkan-merge.yml`) merges an `auto` pr on the agent verifier's marked `PASS`, and a `manual` pr only on an unmarked `PASS`, which only the person can post. this was the risk-tier section of `.scratch/review-ci/spec.md`, cut to two labels by ticket 05.

**Blocked by:** None (can start immediately). the marked `PASS` needs the broker change drafted in ticket 05's answer (underground).

- [ ] the label is set in ci and shown on the pr, with one line of reason
- [ ] a pr that touches a sensitive path is `manual`, whatever the vote says
- [ ] a `manual` pr with only the verifier's marked `PASS` does not merge
- [ ] an `auto` pr merges on the marked `PASS` once every check is green
- [ ] until this ships, every pr is `manual` (the default in `docs/agents/approvals.md`)

## Comments
