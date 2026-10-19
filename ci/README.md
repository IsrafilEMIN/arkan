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
- **counts rounds** in one sticky pr comment, which it edits in place. the comment's first line is a hidden marker, the only state a fresh run reads:

  ```
  <!-- arkan:review round=<n> head=<sha> reviewed=<sha> findings=<id>:<state>,... blocking=<id>,... -->
  ```

  `head` is the commit of round `n`, `reviewed` the last commit a review ran on (the same, except after round 4), `findings` every finding posted so far with its state (`open` or `fixed`), and `blocking` the ids that block (`important` or security-review). only a comment by `github-actions[bot]` counts, so nobody else can plant a marker. below the marker, the comment lists every finding of every round as `` `id` state `tag` `file:line` `symbol` ``.
- **the round** goes up by one only when the head commit changed since the marker's `head`. a rerun of the same head keeps its round, and if that head was already reviewed it does not call the model again: the check is decided from the marker. a run that returns no findings leaves the marker alone, so the next run is the same round again.
- **reviews** in round 1 `git diff <base>...<head>`, the full pr diff. a later round reviews only `git diff <reviewed>..<head>`, the commits since the last review. if `reviewed` is not an ancestor of the head (a force-push or rebase), it reviews the full pr diff again, and the comment says so.
- **limits** one model (`REVIEW_MODEL`), a turn limit (`MAX_TURNS`), a 30-minute job timeout, and read-only tools: the model reads files and runs read-only `git` commands, and posts nothing itself.
- **returns** its findings as structured output (a json schema in `claude_args`): `source`, `tag` (`important`, `nit`, `pre-existing`), `class` (a short kebab-case name for the kind of defect), `symbol` (the function or class it is in), `file`, `line`, `body`; plus `fixed`, the ids of earlier findings it checked are gone at the head.
- **finding ids** are the first 8 hex of `sha256("<class>|<file>|<symbol>")`, worked out in shell, so an id does not move when lines shift. each earlier finding goes to the model with its id, so it does not report it again; a returned finding whose id is already in the marker is dropped all the same, and is never posted twice.
- **fixed**: an earlier finding goes from `open` to `fixed` only when the model lists its id in `fixed` (it reads the code at that file and symbol at the head). the shell trusts only ids that are in the marker and `open`; it never reopens one.
- **posts** the sticky comment with the round's verdict, the diff it reviewed, and all findings; and a pr review with an inline comment per new finding of this round only. if github refuses an inline line (outside the diff), the findings are still in the sticky comment.
- **sets the check** `arkan-review` (the job name) by a shell step, not the model: it fails while any id in `blocking` is `open` in the marker, earlier rounds' included, or if the review returned no findings (turn limit, auth or quota), and passes otherwise.
- **round 4** (`RETHINK_ROUND`) reviews nothing. it writes "step back and rethink the approach" in the sticky comment, adds the label `arkan:rethink` (`RETHINK_LABEL`, created if missing), and fails the check. while the label is on the pr, every run fails the check at once, with no model call. a person removes the label to resume: the next run reviews everything since `reviewed`, and the round count goes on (5, 6, and so on, with no second stop).
- **permissions**: `contents: read` and `pull-requests: write`. it passes the job's `github.token` to the action, so it needs neither the claude github app nor `id-token: write`; comments show as `github-actions`. the action reads `.claude/` from the base branch, so a pr cannot change its own reviewer.

### change it

the settings are the `env:` lines at the top: `REVIEW_MODEL`, `MAX_TURNS`, `RETHINK_ROUND`, `RETHINK_LABEL`, `DOCS_ONLY_REGEX`, `NEVER_DOCS_REGEX`.

**on a pro or max plan,** each review uses the plan's usage; a later round reviews only its new commits, and a rerun of a reviewed head calls no model. when the plan hits its limit, the review returns nothing, the check stays red, and nothing merges until the limit resets: the gate fails closed. if reviews run out often, set `REVIEW_MODEL` to a lighter model. to move the action to a newer release, replace the commit sha and its `# v1.x.y` comment together, and read that release's inputs in its `action.yml` first.

## check

[`github/check.yml`](github/check.yml) runs the repo's check command (its tests, lint and build, the same command the task loop's prove step runs) on each push to the default branch and on each pull request, as a job named `check`. it sets up no language: the command runs with the tools already on github's `ubuntu-latest` runner, and the file has a commented example step for python and node.

### add it to a repo

1. copy the file to `.github/workflows/check.yml`.
2. set the one setting, `CHECK_COMMAND` in `env:` at the top. it defaults to `bash scripts/check.sh`; a repo without that script points it at its own command, for example `npm test`.
3. if the default branch is not `main`, rename it under `on.push.branches`.
4. in the branch protection (or ruleset) of the default branch, require two status checks by name: `check` and `arkan-review`.

it reads the code with `contents: read` and nothing else, stops after 15 minutes, and pins `actions/checkout` to a release commit. to move it to a newer release, replace the commit sha and its `# v7.x.y` comment together.

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

### the plan gate

required status checks need github pro on a private repo, or a public repo. on the free plan a private repo refuses a ruleset (403), so the gate cannot bind: nothing requires `check` or `arkan-review`, and nothing stops a merge around them. where the gate cannot bind, the merge goes through the broker instead: `agent-merge <pr> <sha>`.

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
