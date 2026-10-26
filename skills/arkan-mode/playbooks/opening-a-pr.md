### Opening a PR

Invoked at the end of every other playbook.

**Worktree.** Work from a git worktree off main, placed by step 6 in `SKILL.md`. Subagents inherit it. Several subagents on the same branch each get their own worktree, or `git fetch && git reset --hard origin/<branch>` between them. Dirty branch with unrelated work: patch out, fresh worktree, apply. Snarled worktree: reset from main, redo minimally.

**Commits.** Commit liberally. Rebase into small, ordered commits before opening PRs. The sequence is a future PR: landable as a whole, ordered to tell the story. Amend when the fix belongs in a just-made commit. New commit when separable. Commit bodies don't restate the subject.

**Tickets.** If the work is a ticket, close it the way the issue tracker closes work, in the work's own branch, so the close reaches main with the merge (see `docs/agents/issue-tracker.md`).

**PRs.** Before commit, read the whole diff and remove slop: dead code, debug output, needless churn, and comments that break **Comments** in `SKILL.md`. Write every PR title, description, and commit body per **The reply** in `SKILL.md`, with the STE vocabulary rules: one word per action, keep articles, a plain verb over `-ing` where one works.

**Titles.** Conventional Commits `type(scope): subject`, no trailing period. Type such as `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, or `perf`. Scope is the area, such as `arkan-mode`. Subject is short, imperative, and names a real symbol when one carries the change, for example `fix(arkan-mode): retarget opening-a-pr babysit trigger`.

**Descriptions.** The PR body is a one-minute briefing, not a lab notebook, for a reviewer who has the diff. It says why the change exists, what it leaves out, what it could break, and how you proved it works. Write short, simple sentences with few identifiers, no walls of text. The body becomes the squash commit body, so keep that commit under about 40 lines. Use `##` headings, not bold lead-ins, in this order, and drop a section with nothing to say:

- `## Why`: the problem and approach, 1–3 short sentences. No SHAs, rebase genealogy, or "based on main" preamble.
- `## What changed`: 1–3 short bullets. Name a real symbol or path only when it carries the change. Name both sides of a rename or retarget.
- `## Scope`: always. 1–3 short items on what it covers and what it deliberately leaves out (a follow-up, a known gap). No symbols, paths, or file-by-file essay.
- `## Tradeoffs`: only rejected alternatives a reviewer would otherwise ask about. Skip when there was no real choice.
- `## Blast Radius`: 1–2 sentences on who or what it touches and why that is safe or risky. If main is red, state the cost of leaving it red.
- `## Verification`: 1–3 bullets, each a real run path and its outcome. Perf: one primary number with its unit, `before → after`, and a link to the full results. No sample-size methodology or metric tables.

After the sections, attach videos or screenshots when they prove a claim. Full SHAs, lever-correction essays, file-by-file checklists, and "CLEAN" verdicts go in a linked artifact, not the body.

**Forge.** GitHub CLI (`gh`) is the forge. When the run provides GitHub tools or a built-in PR tool, create, edit, retarget, and mark ready through them, never through `gh`, because a CLI-made PR misses what the tool tracks. Use `gh` for everything the tools do not cover. Keep one choice for create, edit, view, and watch. On the broker route (see **the forge** in `SKILL.md`) its clients replace `gh` for each step here.

**Forge without GraphQL.** `gh pr` runs on GitHub's GraphQL API. Try it first. If it fails with HTTP 403 or a GraphQL error, GraphQL is blocked: make each call over REST with `gh api`, and keep REST for the rest of the run. Paths start at `repos/<owner>/<repo>`. Pass PR text from a file (`-F body=@<file>`), never inline.

- create: `gh api -X POST .../pulls -f title=<title> -f head=<branch> -f base=<base> -F body=@<file>`. Omit `draft`, so the PR opens ready.
- view: `gh api .../pulls/<n>`, fields `state`, `merged`, `merged_at`, `mergeable`, `mergeable_state`, `base.ref`, `head.sha`. `mergeable` is `null` while GitHub computes it, so read again. Reviews: `gh api .../pulls/<n>/reviews`.
- checks: `gh api .../commits/<head-sha>/check-runs` and `gh api .../commits/<head-sha>/status`. A status with `total_count` 0 reads `pending` but has no statuses. In place of `--watch`, `gh run watch <run-id> --exit-status`, with the run ids from `gh run list --commit <head-sha>`.
- comment: `gh api -X POST .../issues/<n>/comments -F body=@<file>`.
- review or verdict: `gh api -X POST .../pulls/<n>/reviews -f event=COMMENT -f commit_id=<head-sha> -F body=@<file>`.
- edit base: `gh api -X PATCH .../pulls/<n> -f base=<branch>`.
- merge: no raw merge call. No session calls `gh pr merge` or another raw merge api; the repo's merge path lands the PR: its `arkan-merge` gate or the broker (`agent-merge <pr> <head-sha>` after green checks and the person's `PASS` on a `manual` PR; see `playbooks/shipping.md` step 4). Read a landed PR back with the view call: `merged` is `true` and `base.ref` is the base you expect.

REST cannot mark a PR ready (`gh pr ready`); a PR created over REST without `draft` is already ready. Auto-merge stays unarmed: `gh pr merge --auto` is a merge api call, and no session calls it.

**Size and stacks.** Prefer five narrow PRs to one large PR. A stack is a base-branch chain. The root PR targets trunk. Each child branch starts at its parent's exact tip and its PR targets the parent branch; once the child is pushed, catch it up by merging its parent, because the broker push is fast-forward only. As a parent merges, move its child onto trunk per `playbooks/shipping.md` step 4. Create a child with `gh pr create --base <parent-branch>`, and retarget one with `gh pr edit <pr> --base <parent-branch>` (or the run's PR tool); on the broker route, `agent-gh pr-create` opens the child, and a merge that deletes the parent branch moves it onto the merged base, so read `baseRefName` back with `agent-gh pr-status <owner/repo> <pr>` (**the forge** in `SKILL.md`). Branch from trunk only for independent work. Rebase on trunk before substantial stack work.

**Readiness.** Open every PR ready, never as a draft. A built-in PR tool can default to draft, so set `draft: false` on every creation call through it. With `gh`, omit `--draft`. If a PR still opens as a draft, mark it ready through the PR tool or with `gh pr ready <number>`. Run `gh pr view <number>` (or the PR tool's read) before you refer to PR status.

**Babysit.** Opening a PR does not start a babysit. Post the URL and keep building. Finish the phase or stack first. Run a separate babysit pass only when the user asks for one after the whole stack exists. A babysit for each new PR stalls the build and spends checks on commits later waves restart. Push back when feedback drifts from intent.

A subagent that opens a PR runs the `code-review` skill on its diff, removes slop and narrating comments, and posts the URL. It returns to the parent without babysitting.
