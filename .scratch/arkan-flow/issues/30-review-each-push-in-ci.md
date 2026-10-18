# 30: review each pull request push in ci

**Role:** ready-for-agent
**Closed:** no
**Priority:** 3

**What to build:** a github workflow, shipped in arkan, that a repo copies in. on every pr open and every push to an open pr, it runs `anthropics/claude-code-action` with arkan's `code-review` and `security-review` skills on the new diff, so the review does not depend on the author's own session. it posts the findings on the pr, each with its tag (`important`, `nit`, `pre-existing`) and `file:line`, and sets a required check named `arkan-review` that fails while an `important` or security finding is open. this was section 09 of `.scratch/review-ci/spec.md`.

**Blocked by:** None (can start immediately).

**Touches:** a new `ci/` folder in arkan, `skills/code-review/`, `skills/security-review/`.

- [ ] the workflow runs on pr open and on each push, with the `CLAUDE_CODE_OAUTH_TOKEN` secret (the owner's subscription; an `ANTHROPIC_API_KEY` works too)
- [ ] it posts findings with tag and `file:line`, and sets the `arkan-review` check
- [ ] it skips docs-only prs and prs from forks, and says so on the pr; each run has a turn limit
- [ ] `README.md` says how a repo adds it
- [ ] proof: in `IsrafilEMIN/arkan-sandbox`, a push with a planted bug gets a failing `arkan-review` check with no session open, and the fixed push turns it green

## Comments

- 2026-10-18, owner: plan b for ticket 19: build the parked review and ci spec, so the scenario runs go all the way to a merge. the runner uses the owner's pro subscription through `CLAUDE_CODE_OAUTH_TOKEN`, not a per-token api key; keep usage low (new diff only, skip docs-only prs, a turn limit).
