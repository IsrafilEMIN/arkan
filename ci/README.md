# ci

## arkan-review

[`github/arkan-review.yml`](github/arkan-review.yml) reviews each push to an open pull request with arkan's `code-review` and `security-review` skills, in a github actions run that no session drives. it runs [`anthropics/claude-code-action`](https://github.com/anthropics/claude-code-action), pinned to a release commit.

### add it to a repo

1. put arkan's skills in the repo's `.claude/skills/`, on the default branch. the action reads `.claude/` from the pr's base branch, never from the pr, so a pr cannot change its own reviewer.
2. add a repo secret `CLAUDE_CODE_OAUTH_TOKEN`: run `claude setup-token` on a pro or max plan and paste the token. to pay per token instead, add `ANTHROPIC_API_KEY` and swap the `claude_code_oauth_token` line for the commented `anthropic_api_key` line.
3. copy the file to `.github/workflows/arkan-review.yml`, on the default branch too: a pr comment command runs the default branch's copy.
4. to block merges on it, add `arkan-review` as a required status check in the branch protection of the base branch.

### what one run does

- **runs on** `pull_request` `opened`, `synchronize` (each push) and `reopened`. a newer push cancels the run on the older head. it also runs on a pr comment (`issue_comment`, only when the comment has `arkan:` in it) and on an inline reply (`pull_request_review_comment`, each one: a skipped job would pass the check), to apply a person's command (below) with no model call. a comment run waits for the run in progress on the pr, and never starts a round. github runs an `issue_comment` run from the default branch's copy of this file, and its own check lands there, so it posts the `arkan-review` check run on the pr head itself; an inline reply runs the pr's copy, and its job is the check.
- **skips**, with a pr comment that says why, a pr from a fork (its run gets no secrets, and its token cannot comment, so there the reason is a notice on the check) and a docs-only pr (every changed file matches `DOCS_ONLY_REGEX`). a pr that touches a file that steers the agent or its reviewer (`NEVER_DOCS_REGEX`: `.claude/`, `.scratch/`, `.github/`, `docs/agents/review-evals/`, `AGENTS.md`, `CLAUDE.md`, `CODING_STANDARDS.md`, `REVIEW.md`, `SKILL.md`, `review-prompt.md`) is always reviewed. a skipped run passes the check, so a person reviews those prs by hand.
- **counts rounds** in one sticky pr comment, which it edits in place. the comment's first line is a hidden marker, the only state a fresh run reads:

  ```
  <!-- arkan:review round=<n> head=<sha> reviewed=<sha> findings=<id>:<tag>:<state>,... blocking=<id>,... -->
  ```

  `head` is the commit of round `n`, `reviewed` the last commit a review ran on (the same, except after round 4), `findings` every finding posted so far with its tag (`important`, `nit`, `pre-existing`) and its state, and `blocking` the ids that block (`important` or security-review). only a comment by `github-actions[bot]` counts, so nobody else can plant a marker. below the marker, the comment lists every finding of every round as `` `id` state `tag` `file:line` `symbol` ``. a marker written before tags were kept has `<id>:<state>`; a run reads each tag from that finding's line and writes the new form.
- **end states**: a finding is `open` until it ends as one of:
  - `fixed`: the model checked that the defect is gone at the head (below).
  - `wrong`: it was not a real problem.
  - `intended`: it is real, but the author meant it.
  - `did-not-matter`: it is real, but not worth fixing.

  a person sets the last three with a line in a pr comment or in a reply to the finding's inline comment: `arkan: <id> wrong`, `arkan: <id> intended` or `arkan: <id> did-not-matter`, one per line, several in one comment if needed. a command counts only from someone whose repo permission is `write`, `maintain` or `admin` (`gh api repos/<repo>/collaborators/<login>/permission`), never from a bot; others are ignored, and the run log says so. each run reads every comment on the pr, so a command applies on its own comment run or on any later run; for one id the latest command wins. a person's state overrides `fixed`, and the model never changes it. a closed finding is not `open`, so it stops blocking.
- **the round** goes up by one only when the head commit changed since the marker's `head`. a rerun of the same head keeps its round, and if that head was already reviewed it does not call the model again: the check is decided from the marker. a run that returns no findings leaves the marker alone, so the next run is the same round again.
- **reviews** in round 1 `git diff <base>...<head>`, the full pr diff. a later round reviews only `git diff <reviewed>..<head>`, the commits since the last review. if `reviewed` is not an ancestor of the head (a force-push or rebase), it reviews the full pr diff again, and the comment says so.
- **limits** one model (`REVIEW_MODEL`), a turn limit (`MAX_TURNS`), a 30-minute job timeout, and read-only tools: the model reads files and runs read-only `git` commands, and posts nothing itself.
- **returns** its findings as structured output (a json schema in `claude_args`): `source`, `tag` (`important`, `nit`, `pre-existing`), `class` (a short kebab-case name for the kind of defect), `symbol` (the function or class it is in), `file`, `line`, `body`; plus `fixed`, the ids of earlier findings it checked are gone at the head.
- **finding ids** are the first 8 hex of `sha256("<class>|<file>|<symbol>")`, worked out in shell, so an id does not move when lines shift. each earlier finding goes to the model with its id, so it does not report it again; a returned finding whose id is already in the marker is dropped all the same, and is never posted twice.
- **fixed**: an earlier finding goes from `open` to `fixed` only when the model lists its id in `fixed` (it reads the code at that file and symbol at the head). the shell trusts only ids that are in the marker and `open`; it never reopens one.
- **posts** the sticky comment with the round's verdict, the diff it reviewed, and all findings; and a pr review with an inline comment per new finding of this round only. if github refuses an inline line (outside the diff), the findings are still in the sticky comment.
- **sets the check** `arkan-review` (the job name) by a shell step, not the model: it fails while any id in `blocking` is `open` in the marker, earlier rounds' included, or if the review returned no findings (turn limit, auth or quota), and passes otherwise. a comment run decides it from the marker the same way, and fails while the head has no finished review.
- **round 4** (`RETHINK_ROUND`) reviews nothing. it writes "step back and rethink the approach" in the sticky comment, adds the label `arkan:rethink` (`RETHINK_LABEL`, created if missing), and fails the check. while the label is on the pr, every run fails the check at once, with no model call. a person removes the label to resume: the next run reviews everything since `reviewed`, and the round count goes on (5, 6, and so on, with no second stop).
- **permissions**: `contents: read`, `pull-requests: write`, and `checks: write` for the check run an `issue_comment` run posts on the head. it passes the job's `github.token` to the action, so it needs neither the claude github app nor `id-token: write`; comments show as `github-actions`. the action reads `.claude/` from the base branch, so a pr cannot change its own reviewer.

### change it

the settings are the `env:` lines at the top: `REVIEW_MODEL`, `MAX_TURNS`, `RETHINK_ROUND`, `RETHINK_LABEL`, `DOCS_ONLY_REGEX`, `NEVER_DOCS_REGEX`.

**on a pro or max plan,** each review uses the plan's usage; a later round reviews only its new commits, and a rerun of a reviewed head calls no model. when the plan hits its limit, the review returns nothing, the check stays red, and nothing merges until the limit resets: the gate fails closed. if reviews run out often, set `REVIEW_MODEL` to a lighter model. to move the action to a newer release, replace the commit sha and its `# v1.x.y` comment together, and read that release's inputs in its `action.yml` first.

### noise report

[`finding-report.sh`](finding-report.sh) counts how the reviewer's findings ended. it reads the sticky comment of every pr in the repo, open and closed, through the rest api (`gh` logged in, and `jq`):

```sh
ci/finding-report.sh <owner/repo> [<since YYYY-MM-DD>]
```

`since` keeps only the prs created on or after that day. it prints one row per tag and one for all: the count of each state, `closed-out` (every finding no longer `open`), and `noise`, which is `(wrong + did-not-matter) / closed-out`:

```
arkan-review findings in <owner/repo>: <n> prs with a review marker
tag           open  fixed  wrong  intended  did-not-matter  closed-out  noise
important        0      5      1         1               0           7    14%
...
```

a finding nobody closed stays `open`, so the report is only as good as the commands people leave. judge a change to the reviewer or to `CODING_STANDARDS.md` against the noise rate per tag, before and after.

## review evals

A merged change that broke main becomes a case under the repo's `docs/agents/review-evals/`, so a change to the reviewer is scored on the misses it must not repeat. [`review-eval.sh`](review-eval.sh) runs the reviewer on each case's `bad.diff` and prints `<case> caught` or `<case> missed`:

```sh
ci/review-eval.sh --compare
```

The default reviewer is `omp -p --no-session --tools=read,grep,glob`; set `REVIEW_CMD` to another command that reads the prompt on stdin. The default prompt is [`review-prompt.md`](review-prompt.md); `--prompt FILE` tests a weaker one. `--update-baseline` records the cases caught now in `docs/agents/review-evals/baseline.txt`; `--compare` exits 1 when a baseline case is now missed. The case format and the full command list are in [the cases doc](../docs/agents/review-evals/README.md).

A change to `github/arkan-review.yml`, `review-prompt.md`, `skills/code-review/` or `skills/security-review/` is kept only when `--compare` misses no case caught before. No ci job runs this: it needs a model, and a github actions runner has no model. The person or agent that changes the reviewer runs it locally before the change lands. The `post-merge` skill adds the case.

A repo that installs `arkan-review` copies `review-eval.sh` and `review-prompt.md` into its own `ci/` and keeps its cases in its own `docs/agents/review-evals/`.

## check

[`github/check.yml`](github/check.yml) runs the repo's check command (its tests, lint and build, the same command the task loop's prove step runs) on each push to the default branch and on each pull request, as a job named `check`. it sets up no language: the command runs with the tools already on github's `ubuntu-latest` runner, and the file has a commented example step for python and node.

### add it to a repo

1. copy the file to `.github/workflows/check.yml`.
2. set the one setting, `CHECK_COMMAND` in `env:` at the top. it defaults to `bash scripts/check.sh`; a repo without that script points it at its own command, for example `npm test`.
3. if the default branch is not `main`, rename it under `on.push.branches`.
4. in the branch protection (or ruleset) of the default branch, require two status checks by name: `check` and `arkan-review`.

it reads the code with `contents: read` and nothing else, stops after 15 minutes, and pins `actions/checkout` to a release commit. to move it to a newer release, replace the commit sha and its `# v7.x.y` comment together.

## arkan-risk

[`github/arkan-risk.yml`](github/arkan-risk.yml) gives each pull request a risk label, `auto` or `manual`, that its author cannot pick. `arkan-merge` and the broker's `pr-merge` read it: an `auto` pr merges on the agent verifier's `PASS`, a `manual` pr only on a person's `PASS`. the rules follow the claude code team's review post: the change sets the tier, some paths always need a person, an agent's approval never counts as a person's, and start strict.

### add it to a repo

1. write `docs/agents/sensitive-paths.md` on the default branch (`pre-setup` does it): one glob per line in its first fenced block.
2. copy the file to `.github/workflows/arkan-risk.yml`.

### what one run does

- **runs on** `pull_request` `opened`, `synchronize` and `reopened`. a newer push cancels the run on the older head.
- **fixed rules first**, each one makes the pr `manual`: the author is not the repo owner; the base branch has no `PATHS_FILE`; the pr touches a path (or the old name of a renamed path) that matches a glob in it. the list is read from the base branch, so a pr cannot edit its way out. `*` and `**` also match `/`.
- **the vote** (`RISK_VOTE`) labels the rest. it is `off` until arkan ticket 42 builds it, so every pr is `manual`. with it `on` and no vote step yet, the run still says `manual`: it fails closed.
- **posts** one sticky pr comment, edited in place. its first line is the marker `arkan-merge` and the broker read: `<!-- arkan:risk head=<sha> label=<auto|manual> -->`. only a comment by `github-actions[bot]` counts. it also sets the pr label `arkan:auto` or `arkan:manual` for people to see; the gate and the broker never read the label.
- **permissions**: `contents: read`, `pull-requests: write`, `issues: write`.

## arkan-merge

[`github/arkan-merge.yml`](github/arkan-merge.yml) is a merge gate a repo can install once. arkan does not use it: arkan's merge path is the broker (`agent-merge <pr> <sha>` on the owner's machine). a repo that installs the gate merges a pull request once its verifier posts a `PASS` verdict on the head commit and every check on that commit passed; after that the agent never merges: it opens the pr, its verifier posts the verdict, and the repo merges. it uses no third-party actions, only `gh` on the runner.

### add it to a repo

a repo that chose the gate path follows these steps; a repo on the broker path skips them.

1. add `arkan-review` first (above), so each push gets a review check.
2. copy the file to `.github/workflows/arkan-merge.yml` on the default branch, and on each base branch a pr can target.
3. allow merge commits in the repo settings: the workflow merges with `--merge`, so main keeps every commit of the pr. to squash instead, set `MERGE_METHOD: squash` and allow squash merges.
4. add a branch rule (a ruleset or branch protection) on each base branch:
   - require a pull request before merging.
   - require the status checks `check` (the repo's tests) and `arkan-review` to pass.
   - leave the bypass list empty, so nobody, the owner included, can merge around the rules.
   - if new branches that the rule covers are created by a push (for example `run/**` trunks), turn on "do not require status checks on creation", or the first push is refused.

### gate or broker

a repo uses one merge path, recorded in `docs/agents/approvals.md` as `**Merge path:** gate` or `**Merge path:** broker`. `pre-setup` asks for the choice; the broker never reads the file.

the gate path needs required status checks, which need github pro on a private repo, or a public repo. on the free plan a private repo refuses a ruleset (403), so the gate cannot bind: nothing requires `check` or `arkan-review`, and nothing stops a merge around them. that repo uses the broker path instead: `agent-merge <pr> <sha>`.

the broker path needs no ruleset. the broker applies row 6's rule itself (seam row 6, `docs/seam.md`): a `manual` pull request lands only on the person's unmarked `PASS` on the head, and an `auto` one may land on the agent verifier's marked `PASS`. it merges with `--merge --delete-branch` and the head pinned.

### what one run does

- **runs on** `pull_request_review` `submitted`, only for a review whose body begins with `PASS` from an author association of `OWNER`, `MEMBER` or `COLLABORATOR`. this filter only keeps strangers on a public repo from starting runs.
- **counts the verdict** only when the reviewer's repo permission is `write`, `maintain` or `admin` (`gh api repos/<repo>/collaborators/<login>/permission --jq .permission`). an author association does not prove write access: an org member can have read only.
- **refuses an agent's verdict on a manual pr**: after the checks, it reads `arkan-risk`'s marker for the head. a review whose body holds `AGENT_MARK` (`<!-- arkan:verifier -->`, which the broker adds to every verdict an agent posts; seam row 6, `docs/seam.md`) merges only an `auto` pr. no marker, or a marker for an older head, counts as `manual`.
- **refuses** when the review's `commit_id` is not the pr's current head: a push after the verdict needs a new verdict.
- **waits** up to 35 minutes, longer than `arkan-review`'s 30-minute job limit, for every other check run on the head. it refuses if any check ends other than `success` or `skipped`.
- **merges** with `gh pr merge --merge --match-head-commit <head>` (`MERGE_METHOD`), so github refuses the merge if the head moved while the run waited. the branch rule still applies: a missing required check stops the merge.
- **sets the check** `arkan-merge` (the job name). a refusal fails it with the reason in the log.
- **permissions**: `contents: write` and `pull-requests: write` to merge, `checks: read` to read the check runs.

### why the verdict is a COMMENT review

on github, a pr author cannot approve their own pr. the agent's verifier posts as the same account that opened the pr, so its verdict is a `COMMENT` review on the head commit whose body begins with `PASS`, not an approval:

```sh
gh api -X POST repos/<owner>/<repo>/pulls/<n>/reviews -f event=COMMENT -f commit_id=<head-sha> -F body=@verdict.md
```

a merge made with the job's `github.token` does not start `push` workflows on the base branch. if the base runs ci on push, that run does not happen for these merges.
