# Review evals

Each confirmed miss by the ci reviewer becomes one case here. The cases keep a change to the reviewer honest: a change to `ci/github/arkan-review.yml`, `ci/review-prompt.md`, `skills/code-review/` or `skills/security-review/` is kept only when it misses no case caught before.

## A case

One folder per case, `<NN>-<slug>/`, numbered from `01`. It holds:

- `bad.diff`: the diff that shipped the bug, as a git diff.
- `case.md`: the bug in one line, where it lived, the fix, and the change that broke main:

```markdown
# 01: check-seam fails on its own patterns

**Bug:** one sentence: what is wrong and what it breaks.
**Path:** `scripts/check-seam.sh`
**Lines:** 10-38
**Fix PR:** the pull request, or the fix commit when there was no pull request.
**Broke main:** the merge or commit that shipped it.
```

`Lines:` is the defect's range in the new side of `bad.diff`. The script reads `**Path:**` and `**Lines:**`; keep the other lines for the person.

## Run the cases

```sh
ci/review-eval.sh                    # one line per case: <case> caught|missed
ci/review-eval.sh --compare          # exit 1 when a baseline case is now missed
ci/review-eval.sh --update-baseline  # record every case caught now
ci/review-eval.sh --prompt weak.md   # test another reviewer prompt
ci/review-eval.sh --check            # check the files and the baseline, no model
```

A case is caught when the review output names the case's path and a line inside its range on the same line. The default reviewer is `omp -p --no-session --tools=read,grep,glob`; set `REVIEW_CMD` to any command that reads the prompt on stdin. The default prompt is [`ci/review-prompt.md`](../../../ci/review-prompt.md). A prompt passed with `--prompt` replaces it; the diff and the output rule are appended either way.

`baseline.txt` lists the cases caught when it was last written. A new case the reviewer misses stays out of the baseline until a reviewer change catches it. A baseline case that a change misses fails `--compare`.

No ci job runs this: it needs a model, and arkan's ci has none. The person or agent that changes the reviewer runs it before the change lands. The `post-merge` skill adds a case after a confirmed miss.
