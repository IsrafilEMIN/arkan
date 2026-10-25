# Review evals

Each confirmed miss by the ci reviewer becomes one case here. The cases keep the reviewer honest: a change to `.github/workflows/arkan-review.yml`, `ci/opencode_agent.py`, `skills/code-review/` or `skills/security-review/` is kept only when it misses no case caught before.

## A case

One folder per case, `<NN>-<slug>/`, numbered from `01`. It holds:

- `bad.diff`: the diff that shipped the bug, as a git diff.
- `case.md`: the bug in one line, where it lived, the fix, and the change that broke main:

```markdown
# 01: one line bug title

**Bug:** one sentence: what is wrong and what it breaks.
**Path:** `scripts/example.sh`
**Lines:** 12
**Bad PR:** the pull request that shipped it, or `none` when a commit went straight to main.
**Fix PR:** the pull request, or the fix commit when there was no pull request.
**Broke main:** the merge or commit that shipped it.
```

`Lines:` is the defect's range in the new side of `bad.diff`; a one-line defect uses its line. The script grades `**Path:**` and `**Lines:**`, and checks that `**Bug:**`, `**Bad PR:**`, `**Fix PR:**` and `**Broke main:**` exist. `Broke main:` holds the bad commit, which the script checks out. The prompt's pull request number is the bad PR: `Bad PR:` when it names one, else a pull request named in `Broke main:`, else `0`. It is never the fix PR.

## One reviewer

`ci/review-eval.sh` reads the prompt, `REVIEW_MODEL` and `MAX_TURNS` from `.github/workflows/arkan-review.yml`, the file ci runs. It fills the workflow's `${{ }}` inputs with the case's values, so a change to that file changes the eval. One file, not a second prompt copy that can drift. The script dies when the prompt holds an input it does not fill, or the workflow uses a `${{ env.* }}` setting it does not read.

The default reviewer is `ci/opencode_agent.py review --eval` with that model and turn limit: the reviewer ci runs. Set `REVIEW_CMD`, or pass `--reviewer`, to use another headless harness. A swapped harness is a weaker proof, because it does not run the command ci runs.

Each case runs in a temp git repo. One commit holds the bad commit's parent tree; the next applies `bad.diff`. The checkout is the bad commit, so the workflow's `git diff <base>...<head>` returns the case's diff. `.claude/skills/` holds the branch's `code-review` and `security-review`: each replaces the parent tree's copy as a whole, from `skills/<name>` when present, else `.claude/skills/<name>`. The repo never holds `docs/agents/review-evals/`: no case, baseline or example is in reach.

## Run the cases

```sh
ci/review-eval.sh                    # one line per case: <case> caught|missed
ci/review-eval.sh --compare          # exit 1 when a baseline case is now missed
ci/review-eval.sh --update-baseline  # add every case caught now to the baseline
ci/review-eval.sh --prompt weak.md   # test another reviewer prompt
ci/review-eval.sh --check            # check the cases, prompt and baseline, no model
```

A finding counts when its line names the case's `Path:` at a line start, or after a character that is not a letter, digit, `.`, `_`, `-` or `/`, and the path is followed by `:`. That `:` must be followed by a line or an `A-B` range. The line or range must sit inside `Lines:`, and a range must be no wider than `Lines:`. So for a case at `Lines: 10`, `scripts/check-seam.sh:10:` counts; `:13`, `1-99999`, `scripts/check-seam.sh.orig:20`, `./scripts/check-seam.sh:10` and prose that names the file without `:<line>` do not. The runner's `--eval` mode prints one `file:line: body` line per finding, or `none`. A custom `REVIEW_CMD` gets the one-line output rule appended, because the script grades text.

`--prompt FILE` replaces the workflow's prompt. The file must name the diff, as the workflow's prompt does: the checkout is at `HEAD`, the bad commit, and `HEAD^` is its parent. A weaker prompt is the proof that a case can go from caught to missed.

A missed case gets one fresh run before it is reported `missed`, the same rule `post-merge` uses for a flaky check.

`baseline.txt` lists the cases caught when it was last written. `--update-baseline` adds the caught cases and never drops one (`sort -u`). A new case the reviewer misses stays out of the baseline until a reviewer change catches it. A baseline case that a change misses fails `--compare`.

No ci job runs a model. `scripts/check.sh` runs `ci/review-eval.sh --check`, which reads the workflow and validates the case files without one. The person or agent that changes the reviewer runs `--compare` locally before the change lands. The `post-merge` skill adds a case after a confirmed miss.
