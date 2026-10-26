# 64: arkan-review posts its verdict as a commit status

**Role:** ready-for-agent
**Closed:** no
**Priority:** 72
**Blocked by:** None (can start immediately).

**What to build:** the underground broker can no longer read check runs. fine-grained tokens cannot call the Checks API ([permissions for fine-grained tokens](https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens)), so every `commits/<sha>/check-runs` read returned HTTP 403 and no pr merged. underground replaced that read with commit statuses (owner decision 2026-10-26, option d): the broker gates on the paginated workflow runs plus the `commits/<sha>/status` contexts, and a per-repo required context (`IsrafilEMIN/arkan arkan-review` in the broker's `required-contexts` file) must be present and `success` on the head. an absent required context reads as pending, so an arkan pr waits until this ticket lands.

today `arkan-review` reports its verdict two ways: the job result on a `pull_request` run, and a check run on the head from an `issue_comment` run (`ci/github/arkan-review.yml` `finish()`, posted with `gh api repos/$REPO/check-runs`). a red verdict from an `issue_comment` run lives only in that check run, and the run itself is green on the default branch. the broker sees neither. the verdict must also be a commit status with context `arkan-review` on the pr head.

- [ ] `ci/github/arkan-review.yml` and `.github/workflows/arkan-review.yml` (byte-identical today) grant `statuses: write`
- [ ] at the start of every run that will decide a verdict, the head gets status `arkan-review` = `pending`
- [ ] `finish()` posts status `arkan-review` on `HEAD_SHA` with `success` or `failure` and the same text, on every event (`pull_request`, `issue_comment`, `pull_request_review_comment`), next to today's check run and job result
- [ ] every skip path (fork, docs-only, first install) posts `success` with its skip text, so a skipped pr does not wait forever on the required context
- [ ] a run that dies before `finish()` leaves the status `pending`, so the broker waits and a person sees it
- [ ] `docs/seam.md` row 6 names the `arkan-review` status as the broker's review signal
- [ ] `scripts/check.sh` prints `check: ok`

## Comments

- 2026-10-26, agent (underground session): underground's side is the broker change on branch `agent/broker-status` (combined status, `total_count == 0` is no block, never the top-level `state`, which reads `pending` with zero statuses). until this ticket ships, arkan prs read `checks.state` `pending` and the merge loop skips them.
