# 62: the verifier retries when its results skip a candidate

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 70
**Blocked by:** None (can start immediately).

**What to build:** `arkan-review` can fail with `no findings returned (review step: failure; error, turns N: the verifier did not check every finding)`. `_parse_verify` in `ci/opencode_agent.py` raises that when a `submit_verify` result does not cover exactly the candidates `1..N`, and it runs only after `_conversation` has accepted the result. the model can submit incomplete coverage early in the verify phase, while it still has turns left. the runner must run the same coverage check at each submission boundary and return the problem to the model, so it can submit again within the existing turn limit. a model that never submits complete coverage still fails the review closed.

- [x] a tool-call `submit_verify` that misses, adds or repeats an index gets a tool reply that names the missing, unexpected or repeated index, and the verify phase goes on
- [x] a nonempty partial result for two candidates gets the same correction and cannot finish the review
- [x] a content-only result with the same coverage problem gets the same message as a user turn
- [x] the final no-tools request after the turns run out runs the same check, with one more try
- [x] coverage stays exact: integer non-boolean indexes, no duplicates, one result per candidate `1..N`; every result needs a boolean `keep`, and a kept result needs a valid `tag`
- [x] a model that never fixes its coverage still fails the review closed
- [x] six consumer-visible recovery cases fail on the old runner and pass on the new one; the persistent-omission case still fails closed
- [x] a submission that fails to parse gets the same correction in every review phase: standards and spec findings, security candidates, the security filter decision and the fixed ids
- [x] `PYTHONDONTWRITEBYTECODE=1 bash scripts/check.sh` prints `check: ok` with 56 tests
- [ ] `ci/review-eval.sh --compare` misses no case caught before (`REVIEW.md`, review evals). this needs a headless reviewer and a model key on the person's machine

#wontfix: the owner merged #95 by hand on 2026-10-26 (merge commit `86978ad`) without the live compare. the compare was not run.

## Live-model comparison

attempted `PYTHONDONTWRITEBYTECODE=1 bash ci/review-eval.sh --compare`. the command exited 2. both attempts reported `every model provider is unavailable: opencode-go, codex, claude`. opencode-go reported `OPENCODE_API_KEY is missing`; codex reported a transport, login or quota failure; claude could not start a turn. the result was `0 caught, 1 missed`, so this is not comparison evidence and the acceptance box stays open.

## Comments

- 2026-10-25, owner: reported `the verifier did not check every finding` from a review run.
- 2026-10-25, agent: local repro with one draft: `submit_verify` with `results: []` returns from `_conversation` in one call, then `_parse_verify` raises the reported error. a complete `keep: false` result for index 1 passes; missing index 1, extra index 2 and a duplicate index 1 each fail. `turns 16` in the log is the configured limit, not the turns used. the regression tests are written but not run in this worktree; the parent runs the red/green proof and the checks.
- 2026-10-25, agent: the seven new tests pass with the fix. against `f9fff69`, six recovery cases raise the old verifier errors; the persistent-omission case still fails closed but lacks the new missing-index diagnostic. a separate `run_review` smoke with two candidates returned one kept finding after the verifier corrected `missing index 2`. boolean indexes, non-boolean `keep`, and kept results without a tag remain invalid.
- 2026-10-25, owner: the same class fired on a live run of this ticket's own pr: `no findings returned (review step: failure; error, turns 16: the model returned a malformed candidate severity)`. the security finder submitted a candidate whose severity did not parse, and the review died after the finder phase returned. the retry now covers the finder submissions too, so the model sees the problem and submits again within the turn limit.
- 2026-10-25, agent: the `arkan-review` check on this pr runs the runner from the base commit, not from the pr (`.github/workflows/arkan-review.yml:110-112`, `git show "$BASE_SHA:ci/opencode_agent.py"`). main still has the bug, so this pr's own review fails with `malformed candidate severity` even with the fix in the pr. the check cannot pass before this pr merges. a live comparison is unavailable on the owner's machine; the codex and claude logins exist, but both providers report transport or quota failures, and the local rig takes about 11 seconds per model call with tens of calls per run.
- 2026-10-25, agent: `scripts/check.sh` passed with 52 tests. independent standards and spec reviews found no defects. the security review found no new high-confidence high or medium issue. no live model result is proven.

## Answer

- the review now retries every submission that fails to parse, at each submission boundary: `submit_verify` coverage, standards and spec findings, security candidates, the security filter decision and the fixed ids. a submission that never parses still fails the review closed.
- evidence: 56 tests pass, and `PYTHONDONTWRITEBYTECODE=1 bash scripts/check.sh` prints `check: ok`. commits `25ec2ba`, `bb7a51c`, `463be85`, `ed60341`; merged as `86978ad` in pr #95.
- live proof of the fixed runner: pr #89's `arkan-review` passed on head `39d9709` after the merge (`checks passed: check=success, arkan-risk=success, arkan-review=success`). its previous head `7c16420` failed on `the verifier did not check every finding`, the coverage error this ticket fixes. the `malformed candidate severity` error came from #95's own review, and `bb7a51c` covers it.
- left open: the live `--compare` never ran; the owner merged by hand. that box carries `#wontfix`. a nightly run of `bash ci/review-eval.sh --compare` with a model key would close it.
