---
name: pre-setup
description: "Link the arkan skills into omp and set up this repo for them: issue tracker, triage labels, domain docs and the Tern board. Safe to run again: it checks first and only works on what is missing or out of date."
disable-model-invocation: true
---

# Pre-Setup

Set up what the other arkan skills assume. A script checks; you ask the person and write.

- [scripts/setup.sh](./scripts/setup.sh) `check [repo-root]` prints one line per item: `ok`, `missing`, `out-of-date`, `hint` or `skip`. It changes nothing.
- `setup.sh apply <item> [repo-root]` installs an item that needs no choice, then prints the item's new state. `apply omp` also prints the names it linked and removed.
- [scripts/board.sh](./scripts/board.sh) `build|check|fields [repo-root]` writes and checks `TODO.md` for a local tracker; `fields` checks only the ticket fields and needs no `TODO.md`. Repos run it from this skill; they get no copy.
- The seeds are in [references/](./references/).

## Process

### 1. Check

Run `setup.sh check` from the repo root. Copy the result into your todo list, one entry per line that is not `ok` or `skip`. Do nothing for an `ok` item, and do not ask about it.

On a re-run, this list is the whole job. When every line is `ok`, `skip` or `hint`, say so and stop: a re-run with nothing to fix changes nothing.

### 2. Work the items in order

For each item, lead with your recommendation so the person can accept it in one word. Ask only where the table says so. Install a no-choice item with `setup.sh apply <item>` without asking.

#### Machine

This item is about this machine, not the repo. It prints from any directory, before the repo items. Pre-setup sets up nothing else on the machine: for any other harness, the person links or copies `skills/<name>` into that harness's skills folder.

| item | what to do | ask? |
|---|---|---|
| `omp` | the target is `$(omp config path)/skills` when `omp` is on PATH and that command succeeds, else `~/.omp/agent/skills`. `check` reads `ok` when every `skills/<name>` of this arkan checkout has a link `<target>/<name>` to it; `missing` names the skills with nothing there; `out-of-date` names a clash (something else at a skill's name) or a stale link (a link into this checkout's `skills/` whose skill is gone). `apply omp` creates the target folder, removes stale links, links the missing skills and prints the new state. It never touches a clash: it reports it and exits 1 | no |

#### Repo

Any change on the host (github) asks first, even when there is no choice: show the exact change (the command, or the setting and its new value), then wait for a yes.

| item | what to do | ask? |
|---|---|---|
| `git` | `apply git` (runs `git init`) | yes |
| `tracker` | GitHub only when a remote points at github and `gh repo view` prints the project from this directory; else local markdown, because ticket writes go through `gh` and the broker has no issue commands. "other" gets a one-paragraph description. When the person asks for github and no `git remote` points at github, get the repo url from the person and wire it (`git init` if needed, `git remote add origin <url>`) before writing the tracker doc; done when `gh repo view` prints the project from this directory, else stop and say what is missing. Write `docs/agents/issue-tracker.md` from `references/issue-tracker-<kind>.md`. For "other", write it from the description and copy the `## Board` section from the github seed. With a local tracker, the check also runs `board.sh fields`: a ticket that breaks the field contract reads `out-of-date` | yes, which kind |
| `labels` | write `docs/agents/triage-labels.md` from `references/triage-labels.md`, as it is. With a github tracker, also create the five labels on the host | only before creating labels on the host |
| `domain` | single-context: write `docs/agents/domain.md` from `references/domain.md`. Offer multi-context only when the repo has monorepo signals (`pnpm-workspace.yaml`, `workspaces` in `package.json`, a populated `packages/*`) | only with monorepo signals |
| `gitattributes` | `apply gitattributes` (adds `GLOSSARY.md merge=union`) | no |
| `agents-block` | write the block below into `AGENTS.md`. With a local tracker, the `### Board` line must name `board.sh build` and `board.sh check`; the check reads `out-of-date` when it does not | no |
| `claude-md` | with claude code detected (`claude` on PATH, or `~/.claude` exists) and `AGENTS.md` in the repo, a missing `CLAUDE.md` is `missing`; `apply claude-md` creates the relative link `CLAUDE.md -> AGENTS.md`. An existing `CLAUDE.md` of any kind is `ok` and untouched. With no `AGENTS.md`, or no claude code, it is `skip` | no |
| `board` | `apply board` (seeds `TODO.md`, creates `.scratch/` for a local tracker, removes a `TODO.md` line from `.gitignore`). With a local tracker, the check runs `board.sh check` and reads `ok` only on `check-board: ok`; then run `board.sh build` and `board.sh check` until it passes. With github, the board is written by hand, as that tracker's seed says | no |
| `verify`, `hooks` (`hint`, `out-of-date`) | tell the person once: "no verify skill: run `verification`"; for hooks, "no commit hook for <languages>: run `setup-pre-commit`", or show the hooks path git uses and say the repo hook will not run. Change nothing | no |

An `out-of-date` line on `hooks` means git's effective hooks path shadows the repo hook: show both paths and change nothing.

Write nothing over a file the person edited. A doc that exists is `ok`, whatever its wording.

### 3. The `AGENTS.md` block

If `AGENTS.md` has no `## Agent skills` section, add it. If it has one, update that section in place and leave the rest of the file alone. Drop the `### Board` script line for a github tracker.

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
```

### 4. Check again, then commit

Run `setup.sh check` again. Every item you worked must now read `ok` (a `hint` stays a `hint`). If one does not, fix it or tell the person why.

Show the person the whole diff (`git status` and `git diff`). Commit only after their yes. Pushing is a change on the host, so it asks again.

### 5. Done

Tell the person what was set up, what was already there, and which hints you gave. A re-run is safe at any time: it reports what is done and works only on the rest.
