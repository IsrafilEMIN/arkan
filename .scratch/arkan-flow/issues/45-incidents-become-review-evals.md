# 45: incidents become review evals

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 30

**What to build:** every merged change that broke main becomes a test case for the ci reviewer, so a change to the reviewer (its prompt, tools or model) is kept only if it still catches the old misses. from the claude code team's review post: "any incidents are now an eval"; this was parked in `.scratch/review-ci/spec.md` and noted in ticket 08.

**Blocked by:** None (can start immediately). it has no reviewer to score until `arkan-review` runs in a repo (ticket 42's runner decision).

- [x] `post-merge` (ticket 08) saves each confirmed miss as one eval case: the bad diff, the bug, where it lived, and the fix pr
- [x] the cases live in one folder per repo, in a format a script and an agent can both read
- [x] a script runs the reviewer against every case and prints, per case, caught or missed
- [x] a change to `arkan-review` or the `code-review` / `security-review` skills is kept only when it misses no case it caught before
- [x] proof: one planted past bug is saved as a case, the script reports it caught, and a weakened reviewer prompt reports it missed

## Comments

- 2026-10-19, owner: capture this so it is actually built, not left parked.
- 2026-10-19, agent: built on `agent/ticket-45-review-evals`. one case is one folder under `docs/agents/review-evals/<NN>-<slug>/`: `case.md` holds the bug, `Path`, `Lines`, `Fix PR` and `Broke main`; `bad.diff` holds the change that shipped it. the folder's `README.md` documents the format. `ci/review-eval.sh` runs a reviewer with the prompt on stdin (`REVIEW_CMD`, default `omp -p --no-session --tools=read,grep,glob`), prints `<case> caught|missed`, and grades deterministically: a finding line must name the case path and a line in its `Lines:` range. `ci/review-prompt.md` is the default prompt; `--prompt FILE` swaps it, and the case diff and the output rule are appended either way. `--compare` exits 1 when a baseline case is missed; `--update-baseline` records the caught cases in `baseline.txt`; `--check` validates the files without a model, and `scripts/check.sh` runs it. case 01 is a real arkan miss: commit `c59d6c7` added `scripts/check-seam.sh`, which searches every tracked file for seam patterns, itself included, so its own pattern lines match and the check fails; commit `5563418` fixed it. the keep rule for `ci/github/arkan-review.yml`, `ci/review-prompt.md`, `skills/code-review/` and `skills/security-review/` is in `REVIEW.md` and `ci/README.md`, with no ci job: the person or agent changing the reviewer runs it. `arkan-review`'s `NEVER_DOCS_REGEX` now treats `docs/agents/review-evals/` and `review-prompt.md` as reviewer-steering, so a change to a case is always reviewed. `post-merge` step 7 saves a case after a confirmed miss.
- 2026-10-19, agent: proof. `omp -p --no-session --tools=read,grep,glob` runs headless here; `codex exec` fails with `failed to initialize in-process app-server client: Operation not permitted`. real prompt, `ci/review-eval.sh --compare`: `01-check-seam-own-patterns caught`, `review-eval: 1 caught, 0 missed`, exit 0. weakened prompt, `ci/review-eval.sh --prompt /tmp/weakened-prompt.md --compare --show` (the prompt checks only that a new file has a shebang): `01-check-seam-own-patterns missed`, `review-eval: 0 caught, 1 missed`, `review-eval: 01-check-seam-own-patterns was caught in the baseline and is now missed`, exit 1. stubs: a reviewer printing `scripts/check-seam.sh:38` reports `caught` and compare exits 0; a reviewer printing `scripts/check-seam.sh:9-10` (a range that covers the defect) reports `caught`; a reviewer printing `none`, or `scripts/check-seam.sh:39-50` (outside it), reports `missed`; the `none` stub with `--compare` exits 1. `scripts/check.sh` prints `check: ok`; `scripts/board.sh check` prints `check-board: ok (49 cards)`.
