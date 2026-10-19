---
name: pre-setup
description: "Set up the machine and this repo for the arkan skills: issue tracker, triage labels, domain docs, the Tern board, the sensitive-path list, the approval rule, REVIEW.md, the ci jobs and the merge path. Safe to run again: it checks first and only works on what is missing or out of date."
disable-model-invocation: true
---

# Pre-Setup

Set up what the other arkan skills assume. A script checks; you ask the person and write.

- [scripts/setup.sh](./scripts/setup.sh) `check [repo-root]` prints one line per item: `ok`, `missing`, `out-of-date`, `hint` or `skip`. It changes nothing.
- `setup.sh apply <item> [repo-root]` installs an item that needs no choice, then prints the item's new state.
- [scripts/board.sh](./scripts/board.sh) `build|check [repo-root]` writes and checks `TODO.md` for a local tracker. Repos run it from this skill; they get no copy.
- The seeds are in [references/](./references/).

## Process

### 1. Check

Run `setup.sh check` from the repo root. Copy the result into your todo list, one entry per line that is not `ok` or `skip`. Do nothing for an `ok` item, and do not ask about it.

On a re-run, this list is the whole job. When every line is `ok`, `skip` or `hint`, say so and stop: a re-run with nothing to fix changes nothing.

### 2. Work the items in order

For each item, lead with your recommendation so the person can accept it in one word. Ask only where the table says so. Install a no-choice item with `setup.sh apply <item>` without asking.

Any change on the host (github, gitlab) asks first, even when there is no choice: show the exact change (the command, or the setting and its new value), then wait for a yes.

| item | what to do | ask? |
|---|---|---|
| `git` | `apply git` (runs `git init`) | yes |
| `tracker` | GitHub if a remote points at github, GitLab if at gitlab, else local markdown; "other" gets a one-paragraph description. Write `docs/agents/issue-tracker.md` from `references/issue-tracker-<kind>.md`. For "other", write it from the description and copy the `## Board` section from the github seed | yes, which kind |
| `labels` | write `docs/agents/triage-labels.md` from `references/triage-labels.md`, as it is. With a github or gitlab tracker, also create the five labels on the host | only before creating labels on the host |
| `domain` | single-context: write `docs/agents/domain.md` from `references/domain.md`. Offer multi-context only when the repo has monorepo signals (`pnpm-workspace.yaml`, `workspaces` in `package.json`, a populated `packages/*`) | only with monorepo signals |
| `gitattributes` | `apply gitattributes` (adds `GLOSSARY.md merge=union`) | no |
| `agents-block` | write the block below into `AGENTS.md` | no |
| `board` | `apply board` (seeds `TODO.md`, removes a `TODO.md` line from `.gitignore`). With a local tracker, then run `board.sh build` and `board.sh check`; it must print `ok`. With github or gitlab, the board is written by hand, as that tracker's seed says | no |
| `sensitive-paths` | start from `references/sensitive-paths.md` and add what the repo has: installer scripts, auth, billing, release workflows. Show the list | yes, the person approves or edits the list |
| `approvals` | `apply approvals` (the fixed rule: `auto` and `manual`) | no |
| `review-md` | `apply review-md` (seeds `REVIEW.md`). Fill in the failure line from what the repo is, if it is plain | no |
| `ci-review`, `ci-check`, `ci-risk` | `apply <item>` copies arkan's file into `.github/workflows/`. Then follow that file's steps in arkan's `ci/README.md` (secrets, the `CHECK_COMMAND` setting) | before the push, and before each secret or setting |
| `ci-merge` | ask gate or broker. Record the answer as the exact line in `docs/agents/approvals.md`: broker installs no gate; gate does. See [Merge path](#merge-path) | yes, which path |
| `codeowners` | write `.github/CODEOWNERS`: each sensitive path, owned by the repo owner. With the gate path, then offer the branch rule from `ci/README.md` (`arkan-merge`): require a pull request, require `check` and `arkan-review`, dismiss stale approvals, empty bypass list | before the branch rule |
| `verify`, `hooks` (`hint`) | tell the person once: "no verify skill: run `create-verification`", or "this js/ts repo has no commit hooks: run `setup-pre-commit`". Change nothing | no |

A `hint` on `ci-check` means the repo already runs its own ci: keep it, and copy `check.yml` only if the person wants arkan's `check` job beside it.

Offer `ci-review` only when the person has added the `CLAUDE_CODE_OAUTH_TOKEN` secret (or `ANTHROPIC_API_KEY`) and arkan's skills in `.claude/skills/` on the default branch. Without them `arkan-review` fails on every pull request, and the gate refuses every merge. Otherwise skip it and say why.

#### Merge path

`ci-merge` is a choice, not a default. Ask which path the repo merges through and record the answer as the exact line in `docs/agents/approvals.md`:

- broker: `**Merge path:** broker`. The broker on the person's machine merges. Install no gate; the check reads `ci-merge ok broker (docs/agents/approvals.md)`. If `.github/workflows/arkan-merge.yml` is present, the check reads `out-of-date`: show the conflict, and remove the file only after the person says yes. Broker availability is the person's call, not a probe: do not claim a broker loop runs unless they say it is deployed. Until it is, the agent calls `agent-merge <pr> <sha>` after the person's `PASS`.
- gate: `**Merge path:** gate`. Run `apply ci-merge`, then follow its steps in `ci/README.md`. The check compares the copy as before.

`apply ci-merge` reads that record. Under broker it prints the broker state and copies nothing. With both lines it refuses and says which line to keep. With no record it refuses and asks for a line, because a copy would otherwise leave the path ambiguous. A gate that is already installed with no record counts as the gate: the check reports that copy, and shipping uses it, so an existing gate needs no record to keep working.

An `out-of-date` line is a ci file that differs from arkan's copy, or a gate installed where `docs/agents/approvals.md` records broker. Show the diff or conflict and ask before you change it: the person may have changed a setting (`CHECK_COMMAND`, the `env:` lines). Keep their settings in the new copy.

Write nothing over a file the person edited, except an `out-of-date` ci file they agreed to update. A doc that exists is `ok`, whatever its wording.

### 3. The `AGENTS.md` block

If `AGENTS.md` has no `## Agent skills` section, add it. If it has one, update that section in place and leave the rest of the file alone. Drop the `### Board` script line for a github or gitlab tracker.

```markdown
## Agent skills

### Issue tracker

[one line: where issues live]. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

[one line: single-context or multi-context]. See `docs/agents/domain.md`.

### Board

`TODO.md` (the Tern board) shows one card per ticket; the details stay in the ticket. See the `## Board` section of `docs/agents/issue-tracker.md`. Do not edit `TODO.md` by hand: run the `pre-setup` skill's `scripts/board.sh build` from the repo root, then `scripts/board.sh check`; it must print `ok`.

### Approvals

Pull requests are `auto` or `manual`; the person approves `manual` ones. The merge path (`broker` or `gate`) is recorded in the same file. See `docs/agents/approvals.md` and `docs/agents/sensitive-paths.md`.

### Review

What the reviewer cares about in this repo. See `REVIEW.md`.
```

### 4. Check again, then commit

Run `setup.sh check` again. Every item you worked must now read `ok` (a `hint` stays a `hint`). If one does not, fix it or tell the person why.

Show the person the whole diff (`git status` and `git diff`). Commit only after their yes. Pushing is a change on the host, so it asks again.

### 5. Done

Tell the person what was set up, what was already there, and which hints you gave. A re-run is safe at any time: it reports what is done and works only on the rest.
