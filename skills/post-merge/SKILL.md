---
name: post-merge
description: "After a merged change breaks main: find the bad merge, make main safe, and ticket the miss."
disable-model-invocation: true
---

A merged change broke something. You make main safe, then turn the **miss** (the bug that got past the task loop) into a ticket a person can act on. Run each step in order; each ends on its criterion.

## Steps

1. **Read the repo's setup.** Read `docs/agents/issue-tracker.md` (and `docs/agents/triage-labels.md` if it exists) for where tickets go and how they are published. Find the check that shows the break: the failing CI job's command, or the test, build or verify step the person names. _Done when_ you can run that check locally and name the tracker. If the repo has no `docs/agents/issue-tracker.md`, ask the person where the ticket goes.

2. **Read the signals.** The person may name the break. Also read what the repo has: CI runs on main (`gh run list --branch <main>`), error logs or alerts it exposes, revert commits (`git log -i --grep=revert`), open incident issues. Classify a CI failure before you trust it: flake earns one fresh run, and an identical second failure is real. _Done when_ you have one confirmed failure and its check exits non-zero on main's head. If nothing is broken, report the signals you read and stop.

3. **Find the first bad commit.** Pick the last commit where the check passes, then bisect along main's merges only: `git bisect start --first-parent <bad> <good>`, then `git bisect run <check>`. Read the merge back (`gh pr view <pr> --json state,mergedAt,baseRefName`, or `git log -1 <sha>`) so the ticket names the PR that really landed. If `gh pr` is blocked, use the view call in **Forge without GraphQL** in the `arkan-mode` skill's `playbooks/opening-a-pr.md`. Run `git bisect reset` after. _Done when_ the check fails on that commit and passes on its first parent.

4. **Make main safe.** On a new branch from main, choose whichever is safer, faster:
   - **revert**: `git revert -m 1 <merge>` (no `-m` for a squash commit). The fallback whenever a fix is unclear.
   - **fix forward**: a small change, red first, through `tdd`, when the cause is plain and a revert would undo more than it saves.

   _Done when_ the check passes on the branch, the repo's other checks still pass, and the branch is pushed. Open the PR with the `pr` skill. Merging is the person's call. In ci, the workflow pushes the branch and opens the PR from your output; you never push or merge.

5. **Name the node that should have caught it.** Walk the task loop in order: build + `tdd` (a test for this case), prove (tests, build, lint, verify), `code-review`, `security-review`. Pick the first node that had what it needed to catch the bug, and say what it lacked: a missing test, a check that never ran, a rule the reviewer does not hold. _Done when_ the answer cites evidence from the bad diff or the node's own output, not a guess.

6. **Ticket the miss.** Publish one ticket on the repo's tracker, as `docs/agents/issue-tracker.md` says, with the `needs-triage` role if the repo uses triage labels. It holds: the bad merge (SHA and PR), the confirmed bug (the check and its failing output), the revert or fix PR, and step 5's answer. If the miss needs a look back over the session that made it, say so in the ticket, then start `retro` (proposals only). In ci, return the ticket content; the workflow publishes it after it opens the PR. _Done when_ the ticket exists and its link or path is in your reply.

## In ci

[`ci/github/arkan-post-merge.yml`](../../ci/github/arkan-post-merge.yml) starts this skill with no person. It runs:

- on a `workflow_run` of `check` finishing on the default branch, for any conclusion from a push to that branch. The run checks main, then reads the merged commits to see whether a revert landed. A revert merged with `--merge` keeps "Merge pull request ..." as its head message, so the workflow reads the first-parent bodies `<sha>^1..<sha>` with `--first-parent` instead of the head subject; a revert inside the merged pull request does not count.
- once a day (`schedule`, 06:17 utc) and on `workflow_dispatch`, for slow signals. The run checks main first, so a red main is a signal on its own, and reads `SIGNAL_COMMAND`, the reverts since the last successful run of this workflow, and open `incident` issues. That lookback is what keeps the daily run from ticketing a revert the event run already ticketed.

A merge whose commit message carries `post-merge` starts neither job again, including a failed one. The daily run catches a red main. The work is in two jobs:

- `diagnose` has the model and read-only permissions. It runs the check, detects the revert, and returns the structured output and a `git bundle` of the fix branch.
- `publish` has no model and the write permissions. It applies the bundle, pushes the branch, opens the pull request, and publishes the ticket.

The run gives you:

- `CHECK_COMMAND`: the check to run, from the workflow's `env:`. The same command runs on main and while bisecting.
- the signal: the check run and its head, a revert, or the slow signals above.
- no person. Take each "ask the person" as the repo's default: the tracker from `docs/agents/issue-tracker.md`, the check above, and the branch you create.
- no push, merge, issue or pull request access. The `diagnose` job has read-only permissions, and its checkout stores no credential. Return the structured output. The `publish` job pushes the branch, opens the pull request, and publishes the ticket.

So in ci:

- do not push, merge, create a pull request, create or edit an issue, or change repo settings.
- do not write the ticket file either. Return its path, title and body, with `{{pr}}` where the pull request url goes. The body carries the fields `board.sh` reads, including `**Blocked by:** none` when nothing blocks. The `publish` job fills the url and rebuilds the board for a local tracker.
- title the pull request `post-merge: ...`, and start the commit `post-merge: revert ...` or `post-merge: fix ...`. That word keeps the landed merge from starting the workflow again.
- when the trigger is a revert and main is green, open no branch: the revert already made main safe. Return the ticket for the miss.
- when nothing is broken, return `broken` false and `action` none with the signals you read, and stop.

## Reply

The signal, the first bad commit, the revert or fix PR, the node that should have caught it, and the ticket.
