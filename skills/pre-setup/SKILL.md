---
name: pre-setup
description: "Set up the machine and this repo for the arkan skills: issue tracker, triage labels, domain docs, the Tern board, the sensitive-path list, the approval rule, REVIEW.md, the ci jobs and the merge path. Safe to run again: it checks first and only works on what is missing or out of date."
disable-model-invocation: true
---

# Pre-Setup

Set up what the other arkan skills assume. A script checks; you ask the person and write.

- [scripts/setup.sh](./scripts/setup.sh) `check [repo-root]` prints one line per item: `ok`, `missing`, `out-of-date`, `hint` or `skip`. It changes nothing.
- `setup.sh apply <item> [repo-root]` installs an item that needs no choice, then prints the item's new state. `apply arkan` prints the names it linked and removed instead.
- [scripts/board.sh](./scripts/board.sh) `build|check|fields [repo-root]` writes and checks `TODO.md` for a local tracker; `fields` checks only the ticket fields and needs no `TODO.md`. Repos run it from this skill; they get no copy.
- [harnesses.md](./harnesses.md) records where each harness reads skills and instructions. Read it before you set up or remove a harness. It cites each fact's source, or marks it `unverified`.
- The seeds are in [references/](./references/).

## Process

### 1. Check

Run `setup.sh check` from the repo root. Copy the result into your todo list, one entry per line that is not `ok` or `skip`. Do nothing for an `ok` item, and do not ask about it.

On a re-run, this list is the whole job. When every line is `ok`, `skip` or `hint`, say so and stop: a re-run with nothing to fix changes nothing.

### 2. Work the items in order

For each item, lead with your recommendation so the person can accept it in one word. Ask only where the table says so. Install a no-choice item with `setup.sh apply <item>` without asking.

#### Machine

These four items are about this machine, not the repo. They print from any directory, before the repo items. Only `harnesses` asks which harnesses; `names` asks only when it reports a clash.

| item | what to do | ask? |
|---|---|---|
| `arkan` | `apply arkan` links every `skills/<name>` of this arkan checkout into `~/.agents/skills/<name>` and records it as `name<TAB>absolute target` in `~/.agents/skills/.arkan-links`. Only names in that file are arkan's links. It links a missing skill and relinks a recorded link that points to another arkan copy or a moved checkout. A recorded current-skill link that points anywhere else is a clash: the link and marker line stay and `apply` exits 1. It removes a recorded link whose skill is gone only when its live target equals the recorded target; a repointed stale link is left alone, its marker line is dropped, and it is reported. A real directory or a missing link at a stale name is left alone, reported, and its marker line is dropped. A user's own link that is not recorded is never touched. `check` reads `ok  version <v>; <n> skills linked`, where `<v>` is `git describe --tags --always --dirty` when this checkout is its own git root, else the `version` in `.claude-plugin/plugin.json` marked `(plugin)`, else `unknown`. `missing` names the skills not linked and how many links point to another arkan copy. `out-of-date` names a stale link, a link to another copy, a link that points elsewhere, or a clash. `apply arkan` prints the names it linked and removed, counts clashes and marker changes, links the rest, and exits 1 on a clash | no |
| `claude-plugin` | `ok` when the install record has an `arkan@arkan` entry, with its version when it carries one, else `installed`; the record is `claude plugin list --json` when `claude` is on PATH, else `~/.claude/plugins/installed_plugins.json`. `missing` when `claude` is on PATH but the record has no arkan entry; `skip claude is not installed` when there is no `claude` and no entry. The cache is read only when no record file exists. `apply claude-plugin` runs `claude plugin marketplace add <path to arkan>` and `claude plugin install arkan@arkan`, then prints the new state; without `claude` it skips | no |
| `harnesses` | detects each harness home or command: `claude` on PATH or an installed plugin, `${CODEX_HOME:-~/.codex}`, `${DSH_HOME:-~/.dsh}`, `~/.pi`, `~/.cursor`, `~/.config/opencode` or `opencode` on PATH, `omp` on PATH, `~/.hermes`. A harness that reads `~/.agents/skills/` needs nothing; claude code needs the plugin; hermes with no `skills.external_dirs` entry, or dsh with `DSH_AGENTS_HOME` set to another root, reads `hint` with what to change. `ok` names the detected harnesses when all are covered, `missing` when claude code has no plugin, `skip` when none is detected. It reads the install record and the cache only, never runs `claude`; it has no apply | yes, which harnesses |
| `names` | inventories candidate names for Claude code, Codex and Omp only, per the owner's ticket 17 scope change. Run `scripts/name-scan.sh <harness>...` with the labels `harnesses` prints. Unsupported labels print `hint unverified` and do not hide supported results. It groups `(harness, namespace, effective name, canonical source, discovery root)` and reports different sources with one name, or a Claude plain skill shadowing `simplify`, `code-review` or `security-review`. Aliases of one canonical source dedupe. Plugins are separate namespaces and are not scanned. See [harnesses.md](./harnesses.md) for roots, missing-name rules and limits. Plain `check` reads on-disk state only and changes no home files. Before its first write, `apply arkan` includes incoming skills for Codex and Omp and models owned links being replaced, including a `.claude` mirror through an owned `.agents` link. Foreign directories and unowned links stay independent. Harness setup and detection still cover the other harnesses, but their names are unverified | only when it reports a clash: show the sources and ask how to resolve it |

The `arkan` check line is the version print. A second `apply arkan` with nothing to fix prints `setup: nothing changed; version <v>`.

For claude code, `apply claude-plugin` installs arkan as a plugin: it runs `claude plugin marketplace add <path to arkan>`, then `claude plugin install arkan@arkan`. Or start claude with `claude --plugin-dir <path to arkan>`. Claude code names each skill `arkan:<skill>`, so arkan's `code-review` and the built-in `/code-review` both stay. A plain skill in `~/.claude/skills/` is not how arkan installs there; `symlink-first` skips arkan's skills for claude while this plugin is installed. A plain skill there with a built-in's name replaces that command; `names` reports the shadow.

Ask the person which harnesses they use as a multi-select, with the detected ones pre-selected. A harness that reads `~/.agents/skills/` needs no change. Claude code gets the plugin, with no link in `~/.claude/skills/`. For a harness that does not read `~/.agents/skills/`, link each arkan skill where that harness reads skills, and only after a yes. Remove a harness's links only after a yes. [harnesses.md](./harnesses.md) gives each harness's paths, instruction file, frontmatter and manual-only mark.

`harnesses` reads the install record and the cache, so it never runs `claude`. A plugin installed through the CLI alone can read `ok` on `claude-plugin` and `missing` on `harnesses`: trust `claude-plugin`, and run it again if the person wants the record updated.

#### Repo

Any change on the host (github, gitlab) asks first, even when there is no choice: show the exact change (the command, or the setting and its new value), then wait for a yes.

| item | what to do | ask? |
|---|---|---|
| `git` | `apply git` (runs `git init`) | yes |
| `tracker` | GitHub if a remote points at github, GitLab if at gitlab, else local markdown; "other" gets a one-paragraph description. Write `docs/agents/issue-tracker.md` from `references/issue-tracker-<kind>.md`. For "other", write it from the description and copy the `## Board` section from the github seed. With a local tracker, the check also runs `board.sh fields`: a ticket that breaks the field contract reads `out-of-date` | yes, which kind |
| `labels` | write `docs/agents/triage-labels.md` from `references/triage-labels.md`, as it is. With a github or gitlab tracker, also create the five labels on the host | only before creating labels on the host |
| `domain` | single-context: write `docs/agents/domain.md` from `references/domain.md`. Offer multi-context only when the repo has monorepo signals (`pnpm-workspace.yaml`, `workspaces` in `package.json`, a populated `packages/*`) | only with monorepo signals |
| `gitattributes` | `apply gitattributes` (adds `GLOSSARY.md merge=union`) | no |
| `agents-block` | write the block below into `AGENTS.md`. With a local tracker, the `### Board` line must name `board.sh build` and `board.sh check`; the check reads `out-of-date` when it does not | no |
| `claude-md` | with claude code detected and `AGENTS.md` in the repo, a missing `CLAUDE.md` is `missing`; `apply claude-md` creates the relative link `CLAUDE.md -> AGENTS.md`. An existing `CLAUDE.md` of any kind is `ok` and untouched. With no `AGENTS.md`, or no claude code, it is `skip` | no |
| `board` | `apply board` (seeds `TODO.md`, creates `.scratch/` for a local tracker, removes a `TODO.md` line from `.gitignore`). With a local tracker, the check runs `board.sh check` and reads `ok` only on `check-board: ok`; then run `board.sh build` and `board.sh check` until it passes. With github or gitlab, the board is written by hand, as that tracker's seed says | no |
| `sensitive-paths` | start from `references/sensitive-paths.md` and add what the repo has: installer scripts, auth, billing, release workflows. Show the list | yes, the person approves or edits the list |
| `approvals` | `apply approvals` (the fixed rule: `auto` and `manual`) | no |
| `review-md` | `apply review-md` (seeds `REVIEW.md`). Fill in the failure line from what the repo is, if it is plain | no |
| `ci-review`, `ci-check`, `ci-risk`, `ci-post-merge` | `apply <item>` copies arkan's file into `.github/workflows/`. `ci-review` and `ci-risk` also install `ci/opencode_agent.py`. Then follow that file's steps in arkan's `ci/README.md` (secrets, the `CHECK_COMMAND` setting) | before the push, and before each secret or setting |
| `ci-runner` | `apply ci-runner` copies arkan's `ci/opencode_agent.py`. A repo with an older `arkan-review` lands this in its own pull request before `apply ci-review`, because the new workflow runs the base branch's runner | before the push |
| `ci-merge` | ask gate or broker. Record the answer as the exact line in `docs/agents/approvals.md`: broker installs no gate; gate does. See [Merge path](#merge-path) | yes, which path |
| `codeowners` | write `.github/CODEOWNERS`: each sensitive path, owned by the repo owner. With the gate path, then offer the branch rule from `ci/README.md` (`arkan-merge`): require a pull request, require `check` and `arkan-review`, dismiss stale approvals, empty bypass list | before the branch rule |
| `verify`, `hooks` (`hint`, `out-of-date`) | tell the person once: "no verify skill: run `create-verification`"; for hooks, "no commit hook for <languages>: run `setup-pre-commit`", or show the hooks path git uses and say the repo hook will not run. Change nothing | no |

A `hint` on `ci-check` means the repo already runs its own ci: keep it, and copy `check.yml` only if the person wants arkan's `check` job beside it.

Offer `ci-review` only when the person has added the `OPENCODE_API_KEY` secret and arkan's skills in `skills/` or `.claude/skills/` on the default branch. Without them `arkan-review` fails on every pull request, and the gate refuses every merge. Otherwise skip it and say why.

Offer `ci-post-merge` only when the person has added the `CLAUDE_CODE_OAUTH_TOKEN` secret (or `ANTHROPIC_API_KEY`) and arkan's skills in `.claude/skills/` on the default branch. It runs the `post-merge` skill when main's `check` fails or a revert lands, and once a day for slow signals. A repo that still has an older `arkan-post-merge-daily.yml` removes it after a yes, because the daily trigger is in the one file now. A repo whose own ci workflow has another name edits the copy's `workflows:` line before the push. The file takes `CHECK_COMMAND`, `MAIN`, and an optional `SIGNAL_COMMAND`. A github tracker needs no extra setting: the run creates the ticket as an issue, and a local tracker gets it committed on the branch. The run never merges the pull request it opens; the repo's merge path still lands it.

The pull request the run opens starts no `check`, `arkan-review` or `arkan-risk` run when it uses `github.token`. To get those runs, add the optional `POST_MERGE_TOKEN` secret as `ci/README.md` says: a fine-grained token, or an App installation token minted in a step, never a stored App token. A run that uses `github.token` also needs the setting "Allow GitHub Actions to create and approve pull requests" before it can open the pull request at all. On the gate path, a merge made with `github.token` starts no `check` run on main, so the event trigger never fires; the daily run still runs the check and catches a red main.

#### Merge path

`ci-merge` is a choice, not a default. Ask which path the repo merges through and record the answer as the exact line in `docs/agents/approvals.md`:

- broker: `**Merge path:** broker`. The broker on the person's machine merges. Install no gate; the check reads `ci-merge ok broker (docs/agents/approvals.md)`. If `.github/workflows/arkan-merge.yml` is present, the check reads `out-of-date`: show the conflict, and remove the file only after the person says yes. Broker availability is the person's call, not a probe: do not claim a broker loop runs unless they say it is deployed. Until it is, the agent calls `agent-merge <pr> <sha>` after the person's `PASS`.
- gate: `**Merge path:** gate`. Run `apply ci-merge`, then follow its steps in `ci/README.md`. The check compares the copy as before.

`apply ci-merge` reads that record. Under broker it prints the broker state and copies nothing. With both lines it refuses and says which line to keep. With no record it refuses and asks for a line, because a copy would otherwise leave the path ambiguous. A gate that is already installed with no record counts as the gate: the check reports that copy, and shipping uses it, so an existing gate needs no record to keep working.

An `out-of-date` line is a ci file whose `# arkan-copy:` stamp does not match arkan's current copy, or a gate installed where `docs/agents/approvals.md` records broker. A copy that differs from arkan's file but keeps the `# arkan-copy:` stamp that `apply` wrote reads `ok customized`: the person changed a setting (`CHECK_COMMAND`, the `env:` lines) and arkan's file did not change since. For `hooks`, it means git's effective hooks path shadows the repo hook: show both paths and change nothing. Show the diff or conflict and ask before you change an `out-of-date` file: keep the person's settings in the new copy.

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
