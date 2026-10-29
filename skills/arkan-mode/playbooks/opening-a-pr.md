### Opening a PR

Invoked at the end of every other playbook.

**Worktree.** Work from a git worktree off main, placed by step 6 in `SKILL.md`. Subagents inherit it. Several subagents never share a branch: each gets its own branch and worktree, and the owner merges them. Dirty branch with unrelated work: patch out, fresh worktree, apply. Snarled worktree: start a fresh branch and worktree from main and redo minimally; never reset a branch that holds pushed work.

**Commits.** Commit each verified step, small and in order, and checkpoint it with `broker push`. The sequence is a future PR: landable as a whole, ordered to tell the story. Never rebase, amend or force-push pushed commits: the broker pushes fast-forward only. A fix to an earlier step is a new commit. Commit bodies don't restate the subject.

**Tickets.** If the work is a ticket, run **close done** from the [tickets playbook](tickets.md) in the work's own branch, so the close reaches main with the merge.

**PRs.** Before commit, read the whole diff and remove slop: dead code, debug output, needless churn, and comments that break **Comments** in `SKILL.md`. Write every PR title, description, and commit body per **The reply** in `SKILL.md`, with the STE vocabulary rules: one word per action, keep articles, a plain verb over `-ing` where one works.

**Titles.** Conventional Commits `type(scope): subject`, no trailing period. Type such as `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, or `perf`. Scope is the area, such as `arkan-mode`. Subject is short, imperative, and names a real symbol when one carries the change, for example `fix(arkan-mode): retarget opening-a-pr babysit trigger`.

**Descriptions.** The PR body is a one-minute briefing, not a lab notebook, for a reviewer who has the diff. It says why the change exists, what it leaves out, what it could break, and how you proved it works. Write short, simple sentences with few identifiers, no walls of text. The body becomes the squash commit body, so keep that commit under about 40 lines. Use `##` headings, not bold lead-ins, in this order, and drop a section with nothing to say:

- `## Why`: open with the person's goal in your own words, then the problem and approach, 1–3 short sentences. No SHAs, rebase genealogy, or "based on main" preamble.
- `## What changed`: 1–3 short bullets. Name a real symbol or path only when it carries the change. Name both sides of a rename or retarget.
- `## Scope`: always. 1–3 short items on what it covers and what it deliberately leaves out (a follow-up, a known gap). No symbols, paths, or file-by-file essay.
- `## Tradeoffs`: only rejected alternatives a reviewer would otherwise ask about. Skip when there was no real choice.
- `## Blast Radius`: 1–2 sentences on who or what it touches and why that is safe or risky. If main is red, state the cost of leaving it red.
- `## Risk`: always. The `auto` or `manual` grade from the last `code-review` round, with its one-line reason.
- `## Revert`: always. 1–2 sentences on how to undo it: revert the merge commit, or turn off the flag. Name any effect a revert alone does not undo, such as a data migration, a published release or outside state.
- `## Verification`: 1–3 bullets, each a real run path and its outcome. Perf: one primary number with its unit, `before → after`, and a link to the full results. No sample-size methodology or metric tables.

After the sections, attach videos or screenshots when they prove a claim. Full SHAs, lever-correction essays, file-by-file checklists, and "CLEAN" verdicts go in a linked artifact, not the body.

**Forge.** The broker makes every write: `broker pr-create`, `broker pr-comment`, `broker merge` (see **the forge** in `SKILL.md`). If it is missing or refuses, stop and report its exact error; never write through `gh`, REST or a built-in PR tool instead. `gh` is for reads only.

**Forge without GraphQL.** `gh pr` reads run on GitHub's GraphQL API. Try them first. If one fails with HTTP 403 or a GraphQL error, GraphQL is blocked: make each read over REST with `gh api`, and keep REST for the rest of the run. Paths start at `repos/<owner>/<repo>`.

- view: `gh api .../pulls/<n>`, fields `state`, `merged`, `merged_at`, `mergeable`, `mergeable_state`, `base.ref`, `head.sha`. `mergeable` is `null` while GitHub computes it, so read again. Reviews: `gh api .../pulls/<n>/reviews`.
- checks: `gh api .../commits/<head-sha>/check-runs` and `gh api .../commits/<head-sha>/status`. A status with `total_count` 0 reads `pending` but has no statuses. In place of `--watch`, `gh run watch <run-id> --exit-status`, with the run ids from `gh run list --commit <head-sha>`.
- a landed PR: the view call reads `merged` `true` and `base.ref` the base you expect.

Auto-merge is a merge, and the broker has no verb for it: do not arm it.

**Size.** Prefer five narrow PRs to one large PR. `broker pr-create` takes no base, so every PR targets trunk: no stacks. Split work into narrow PRs that each land on trunk alone.

**Readiness.** `broker pr-create` opens the PR. Read it with `broker pr-status <owner/repo> <n>` or `gh pr view <number>` before you refer to PR status. If it opened as a draft, report it; do not mark it ready through another tool.

**Babysit.** Opening a PR does not start a babysit. Post the URL and keep building. Finish the stack first. Run a separate babysit pass only when the user asks for one after the whole stack exists. A babysit for each new PR stalls the build and spends checks on commits later waves restart. Push back when feedback drifts from intent.

A subagent that opens a PR runs the `code-review` skill on its diff, removes slop and narrating comments, and posts the URL. It returns to the parent without babysitting.
