# 42: risk tier picks auto or manual

**Role:** ready-for-agent
**Closed:** no
**Priority:** 35

**What to build:** each pull request gets the label `auto` or `manual`, set in ci, never by the author. a path on `docs/agents/sensitive-paths.md` makes it `manual`; for the rest, a vote of fresh-context agents picks the label, and a second check can only raise it to `manual`. the merge gate (`ci/github/arkan-merge.yml`) merges an `auto` pr on the agent verifier's marked `PASS`, and a `manual` pr only on an unmarked `PASS`, which only the person can post. this was the risk-tier section of `.scratch/review-ci/spec.md`, cut to two labels by ticket 05.

**Blocked by:** None (can start immediately). the marked `PASS` needs the broker change drafted in ticket 05's answer (underground).

- [x] the label is set in ci and shown on the pr, with one line of reason
- [x] a pr that touches a sensitive path is `manual`, whatever the vote says
- [x] a `manual` pr with only the verifier's marked `PASS` does not merge
- [ ] an `auto` pr merges on the marked `PASS` once every check is green
- [x] until this ships, every pr is `manual` (the default in `docs/agents/approvals.md`)

## Comments

- 2026-10-19, agent: the fixed rules and the gate are built on `claude/ticket-42-risk-tier`. `ci/github/arkan-risk.yml` (and arkan's own copy in `.github/workflows/`): a pr is `manual` when its author is not the repo owner, when the base has no `docs/agents/sensitive-paths.md`, or when it touches a path on that list (read from the base, renames by both names); the rest goes to the vote, which is `off` (`RISK_VOTE`), so every pr is `manual` for now. the run posts a sticky comment whose first line is `<!-- arkan:risk head=<sha> label=<auto|manual> -->` and sets the label `arkan:auto` or `arkan:manual`. `arkan-merge` reads the marker after the checks: an agent's marked `PASS` merges only an `auto` pr; no marker, or one for an older head, is `manual`. `pre-setup` gains the `ci-risk` item.
- 2026-10-19, proof (the workflow steps run locally against a fake `gh`): a stranger's pr, a pr that touches `.github/workflows/x.yml`, one that touches `AGENTS.md`, one with the vote off, and one on a base without the list each came out `manual` with the matching reason; with the vote on and no rule hit, it went to the vote. the gate merged an agent's `PASS` on an `auto` marker for the head, refused it on a `manual` marker, on a marker for an older head and with no marker, and merged a person's `PASS` on `manual`.
- 2026-10-19, still open: the vote itself (fresh-context agents, majority, then a second check that can only raise to `manual`). it needs a model runner in ci: the `CLAUDE_CODE_OAUTH_TOKEN` secret, or a self-hosted runner with a logged-in `claude` (the owner is weighing the second). the box "an `auto` pr merges on the marked `PASS`" waits for the vote and for underground 48.
- 2026-10-19, owner: the vote is deferred for now. the fixed rules and the gate ship as they are; every pr stays `manual`.
