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

## check

[`github/check.yml`](github/check.yml) runs the repo's check command (its tests, lint and build, the same command the task loop's prove step runs) on each push to the default branch and on each pull request, as a job named `check`. it sets up no language: the command runs with the tools already on github's `ubuntu-latest` runner, and the file has a commented example step for python and node.

### add it to a repo

1. copy the file to `.github/workflows/check.yml`.
2. set the one setting, `CHECK_COMMAND` in `env:` at the top. it defaults to `bash scripts/check.sh`; a repo without that script points it at its own command, for example `npm test`.
3. if the default branch is not `main`, rename it under `on.push.branches`.
4. in the branch protection (or ruleset) of the default branch, require two status checks by name: `check` and `arkan-review`.

it reads the code with `contents: read` and nothing else, stops after 15 minutes, and pins `actions/checkout` to a release commit. to move it to a newer release, replace the commit sha and its `# v7.x.y` comment together.
