# 61: the reviewer asks the model again when its result has the wrong shape

**Role:** ready-for-agent
**Closed:** no
**Priority:** 69
**Blocked by:** None (can start immediately).

**What to build:** `arkan-review` failed on prs 79, 80, 81 and 82 with `no findings returned (review step: failure; error, turns 16: the model returned malformed findings)`. that error comes from `_parse_findings` in `ci/opencode_agent.py`: the model submitted a result whose `findings` field was missing or not a list. the runner then fails the whole review, although the model still had turns left to fix the result. when a submitted result lacks a required field, or an array field is not an array, tell the model what is wrong and let it submit again. a model that never fixes its result still fails the review.

- [x] a `submit_*` call without a required field gets a tool reply that names the field, and the conversation goes on
- [x] a content-only JSON reply with the wrong shape gets the same message as a user turn
- [x] when the turns run out, the last result is parsed as before, so a wrong shape still fails the review closed
- [x] tests: two new tests fail on the old runner and pass on the new one; a third proves the review still fails when the model never fixes its result
- [ ] `ci/review-eval.sh --compare` misses no case caught before (`REVIEW.md`, review evals). this needs a headless reviewer and a model key on the person's machine
- [x] `bash scripts/check.sh` prints `check: ok` (43 tests)

## Comments

- 2026-10-25, owner: reported the `malformed findings` failure on pr 79.
- 2026-10-25, agent: `_shape_problem` reads the submit tool's own schema (`required` and array `type`) and returns the first problem. `_conversation` uses it on both submit paths. item-level checks stay in the parsers (`_draft`), so one bad finding item still fails the review, as before. [inference] the failure on prs 79–82 comes from the model, not from their diffs: #83 and #84 passed on the same runner. a rerun of the same head (github "re-run failed jobs") keeps the round, and is the way to unblock those prs before this lands; an empty commit would use up a round, and round 4 stops the review.
