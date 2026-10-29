### Spec

**You own the integration branch. Run each ready ticket as its own task loop, merge it, and land the spec as one PR.**

The tickets are not a list of steps. They are a **task graph**: each ticket lists the tickets that block it, so there is always a **frontier** of tickets ready to start. You gate the spec once, at step 1: each ticket's role must be `ready-for-agent` (step 0 of `SKILL.md`). After that, your task graph decides the frontier, not the board on `main`: a ticket joins it when every ticket that blocks it is merged to the integration branch. Its blockers close on `main` only when the spec PR merges, so the board would hold it back forever. Tickets tagged `ready-for-human` or `needs-info` wait, and so does everything they block.

Talk to subagents through context pointers: the spec, the ticket paths, the notes files, the commits. Do not paste what a pointer already holds. Run implementer subagents in the background where the harness supports it, for the most work at once.

1. Read the spec and its tickets, and write down the task graph: each ticket, its blockers, its role. Name the first frontier, and each ticket that waits and why.
2. (optional) Send an **exploration subagent** to read what the tickets need: codebase files, external docs. It saves its notes as markdown in a folder outside the repo that every later subagent can read, so the implementers build instead of explore.
3. Create the integration branch from the main branch. Name it `agent/<spec-slug>` and each implementer branch `agent/<spec-slug>-<ticket>`, per **the forge** in `SKILL.md`.
4. Start one **implementer subagent** per frontier ticket, each in its own worktree on its own branch, placed by step 6 in `SKILL.md`, all at once. Do not build a ticket in this chat, however small: this chat runs the playbook. Each implementer:
   - confirms its worktree is based on the integration branch tip, and resets onto it if not;
   - reads `SKILL.md` and runs the task loop on its one ticket: **claim** it (the [tickets playbook](tickets.md)), match a playbook, build with `tdd`, prove it. It skips the step 0 readiness check (you gated the spec and own the frontier), the code review, the close and the PR: the spec has one of each, in steps 7 and 8;
   - merges the integration branch tip into its own branch, and proves it again, before it reports done.
5. When an implementer reports done, read its diff yourself, then merge its branch into the integration branch with a **merger subagent**. An implementer that reports a missing blocker (step 0 of `SKILL.md`) gets no merge: its ticket leaves the frontier until that blocker merges.
6. A merge can unblock tickets. Each ticket whose blockers are now all merged joins the frontier: start an implementer for it at once (step 4). Repeat steps 4 to 6 until the frontier is empty.
7. Once every ticket is merged, run the `code-review` skill on the integration branch in a fresh context. Fix every issue it raises in a single implementer subagent, then run the full test suite.
8. Always open one PR for the spec, from the integration branch, with **Opening a PR**. Before you open it, run **close done** on each ticket and **close spec**, on the integration branch, so every close and the rebuilt board land on `main` with the merge.
9. Keep every implementer branch and worktree until the spec PR merges into `main` and the merge is verified: they are the checkpoints. Then, per **the forge** in `SKILL.md`, run `broker delete-branch` for each implementer branch and remove its worktree. If a step fails or its result is unknown, keep that worktree and report it.

**Reply:** the task graph, which tickets ran in parallel, which waited and why, what the review found and how it was fixed, and the PR link.
