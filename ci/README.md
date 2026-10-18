# ci

## arkan-review

[`github/arkan-review.yml`](github/arkan-review.yml) reviews each push to an open pull request with arkan's `code-review` and `security-review` skills, in a github actions run that no session drives. it runs [`anthropics/claude-code-action`](https://github.com/anthropics/claude-code-action), pinned to a release commit.

### add it to a repo

1. put arkan's skills in the repo's `.claude/skills/`, on the default branch. the action reads `.claude/` from the pr's base branch, never from the pr, so a pr cannot change its own reviewer.
2. add a repo secret `CLAUDE_CODE_OAUTH_TOKEN`: run `claude setup-token` on a pro or max plan and paste the token. to pay per token instead, add `ANTHROPIC_API_KEY` and swap the `claude_code_oauth_token` line for the commented `anthropic_api_key` line.
3. copy the file to `.github/workflows/arkan-review.yml`.
4. to block merges on it, add `arkan-review` as a required status check in the branch protection of the base branch.

### what one run does

- **runs on** `pull_request` `opened`, `synchronize` (each push) and `reopened`. a newer push cancels the run on the older head.
- **skips**, with a pr comment that says why, a pr from a fork (its run gets no secrets, and its token cannot comment, so there the reason is a notice on the check) and a docs-only pr (every changed file matches `DOCS_ONLY_REGEX`). a pr that touches a file that steers the agent or its reviewer (`NEVER_DOCS_REGEX`: `.claude/`, `.scratch/`, `.github/`, `AGENTS.md`, `CLAUDE.md`, `CODING_STANDARDS.md`, `REVIEW.md`, `SKILL.md`) is always reviewed. a skipped run passes the check, so a person reviews those prs by hand.
- **reviews** `git diff <base>...<head>`, the full pr diff. narrowing a later push to its new commits is arkan ticket `arkan-flow` 31.
- **limits** one model (`REVIEW_MODEL`), a turn limit (`MAX_TURNS`), a 30-minute job timeout, and read-only tools: the model reads files and runs read-only `git` commands, and posts nothing itself.
- **returns** its findings as structured output (a json schema in `claude_args`): `source`, `tag` (`important`, `nit`, `pre-existing`), `file`, `line`, `body`.
- **posts** them as one pr review: a summary with each finding as `` `tag` `file:line` ``, and an inline comment per finding. if github refuses an inline line (outside the diff), the review goes up without the inline comments.
- **sets the check** `arkan-review` (the job name) by a shell step, not the model: it fails if any finding is `important` or comes from `security-review`, or if the review returned no findings (turn limit, auth or quota), and passes otherwise.
- **permissions**: `contents: read` and `pull-requests: write`. it passes the job's `github.token` to the action, so it needs neither the claude github app nor `id-token: write`; comments show as `github-actions`.

### change it

the settings are the `env:` lines at the top: `REVIEW_MODEL`, `MAX_TURNS`, `DOCS_ONLY_REGEX`, `NEVER_DOCS_REGEX`.

**on a pro or max plan,** each review uses the plan's usage. when the plan hits its limit, the review returns nothing, the check stays red, and nothing merges until the limit resets: the gate fails closed. if reviews run out often, set `REVIEW_MODEL` to a lighter model (the sandbox uses `claude-sonnet-5-5`). to move the action to a newer release, replace the commit sha and its `# v1.x.y` comment together, and read that release's inputs in its `action.yml` first.

## arkan-merge

[`github/arkan-merge.yml`](github/arkan-merge.yml) merges a pull request once its verifier posts a `PASS` verdict on the head commit and every check on that commit passed. the person installs it once in a repo. after that the agent never merges: it opens the pr, its verifier posts the verdict, and the repo merges. it uses no third-party actions, only `gh` on the runner.

### add it to a repo

1. add `arkan-review` first (above), so each push gets a review check.
2. copy the file to `.github/workflows/arkan-merge.yml` on the default branch, and on each base branch a pr can target.
3. allow squash merges in the repo settings: the workflow merges with `--squash`.
4. add a branch rule (a ruleset or branch protection) on each base branch:
   - require a pull request before merging.
   - require the status checks `check` (the repo's tests) and `arkan-review` to pass.
   - leave the bypass list empty, so nobody, the owner included, can merge around the rules.
   - if new branches that the rule covers are created by a push (for example `run/**` trunks), turn on "do not require status checks on creation", or the first push is refused.

### what one run does

- **runs on** `pull_request_review` `submitted`, only for a review whose body begins with `PASS` from an author association of `OWNER`, `MEMBER` or `COLLABORATOR`. this filter only keeps strangers on a public repo from starting runs.
- **counts the verdict** only when the reviewer's repo permission is `write`, `maintain` or `admin` (`gh api repos/<repo>/collaborators/<login>/permission --jq .permission`). an author association does not prove write access: an org member can have read only.
- **refuses** when the review's `commit_id` is not the pr's current head: a push after the verdict needs a new verdict.
- **waits** up to 35 minutes, longer than `arkan-review`'s 30-minute job limit, for every other check run on the head. it refuses if any check ends other than `success` or `skipped`.
- **merges** with `gh pr merge --squash --match-head-commit <head>`, so github refuses the merge if the head moved while the run waited. the branch rule still applies: a missing required check stops the merge.
- **sets the check** `arkan-merge` (the job name). a refusal fails it with the reason in the log.
- **permissions**: `contents: write` and `pull-requests: write` to merge, `checks: read` to read the check runs.

### why the verdict is a COMMENT review

on github, a pr author cannot approve their own pr. the agent's verifier posts as the same account that opened the pr, so its verdict is a `COMMENT` review on the head commit whose body begins with `PASS`, not an approval:

```sh
gh api -X POST repos/<owner>/<repo>/pulls/<n>/reviews -f event=COMMENT -f commit_id=<head-sha> -F body=@verdict.md
```

a merge made with the job's `github.token` does not start `push` workflows on the base branch. if the base runs ci on push, that run does not happen for these merges.
