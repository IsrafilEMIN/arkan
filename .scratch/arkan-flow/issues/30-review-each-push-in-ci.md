# 30: review each pull request push in ci

**Role:** ready-for-agent
**Closed:** no
**Priority:** 3

**What to build:** a github workflow, shipped in arkan, that a repo copies in. on every pr open and every push to an open pr, it runs `anthropics/claude-code-action` with arkan's `code-review` and `security-review` skills on the new diff, so the review does not depend on the author's own session. it posts the findings on the pr, each with its tag (`important`, `nit`, `pre-existing`) and `file:line`, and sets a required check named `arkan-review` that fails while an `important` or security finding is open. this was section 09 of `.scratch/review-ci/spec.md`.

**Blocked by:** None (can start immediately).

**Touches:** a new `ci/` folder in arkan, `skills/code-review/`, `skills/security-review/`.

- [x] the workflow runs on pr open and on each push, with the `CLAUDE_CODE_OAUTH_TOKEN` secret (the owner's subscription; an `ANTHROPIC_API_KEY` works too)
- [ ] it posts findings with tag and `file:line`, and sets the `arkan-review` check
- [ ] it skips docs-only prs and prs from forks, and says so on the pr; each run has a turn limit
- [x] `README.md` says how a repo adds it
- [ ] proof: in `IsrafilEMIN/arkan-sandbox`, a push with a planted bug gets a failing `arkan-review` check with no session open, and the fixed push turns it green

## Comments

- 2026-10-18, owner: plan b for ticket 19: build the parked review and ci spec, so the scenario runs go all the way to a merge. the runner uses the owner's pro subscription through `CLAUDE_CODE_OAUTH_TOKEN`, not a per-token api key; keep usage low (new diff only, skip docs-only prs, a turn limit).
- 2026-10-18: built `ci/github/arkan-review.yml` and `ci/README.md`, and a "review in ci" section in `README.md`. the action is `anthropics/claude-code-action` v1.0.252, pinned to its commit; its inputs were read from its `action.yml`, `docs/usage.md` and `src/` at that tag. the model returns findings as structured output (`--json-schema`), and a shell step posts them as one pr review and fails the check on an `important` or security-review finding, or on no findings. it passes the job's `github.token`, so it needs neither the claude github app nor `id-token: write`.
- 2026-10-18: proof in `IsrafilEMIN/arkan-sandbox`, stopped by the secret. base `ci-review-base` (`pre-break` plus the workflow), pr https://github.com/IsrafilEMIN/arkan-sandbox/pull/6 from `ci-review-proof` with a planted bug (`Inventory.discounted_value_cents` keeps `percent` instead of taking it off, and takes any percent). the workflow is on the base, so the reviewed diff holds only the bug. three runs, on opened, reopened and a push: check runs 117786441093, 117786849128 and 117787019098, each `arkan-review` `failure` in about 25 seconds, before any review. the action's error: "Invalid auth token · Fix external auth token · Invalid Authorization header value from CLAUDE_CODE_OAUTH_TOKEN: it contains a line break at character 66 (110 characters on 2 lines)." so the sandbox secret was pasted wrapped. the workflow posted that cause on the pr and kept the check red, as it should, but the red is not from a finding, so the planted-bug and fixed-push proof is not done. next: the owner sets the secret again on one line, reopens pr 6 (that reruns it), and pushes the fix (a 0 to 100 check with a new `InvalidDiscount`, `(100 - percent)`, two tests).
- 2026-10-18: docs-only skip proven: pr https://github.com/IsrafilEMIN/arkan-sandbox/pull/7 (one `README.md` line) got check run 117787295179 `success` in 7 seconds with no model call, and the comment "arkan-review skipped: every changed file is docs (matches `(\.(md|mdx|txt|rst)$|^docs/|^LICENSE$|^NOTICE$)`), so no review ran." the fork skip is built but not run (no fork to test from). posting findings as a review with inline comments is tested only by running the step's script on sample findings, not in ci. both proof prs are closed, not merged.
