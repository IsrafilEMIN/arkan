# 02: build the board from the tickets

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 4

**What to build:** a script that writes `TODO.md` from the ticket files under `.scratch/`, so a merge conflict in `TODO.md` is fixed by running it again, never by hand. the ticket files are already the source of truth; the card only mirrors them.

**Blocked by:** None (can start immediately).

for this, each ticket file must hold what its card shows today: title, `#<role>`, any `#<type>` or `📅` date, and whether it is closed (lane `Done`). the role and the closed state move from the card into the ticket file, for example a `Role:` line and a `Closed:` line near the top.

- [x] every ticket file holds its role and closed state; `docs/agents/issue-tracker.md` `## Board` says so, and that the board is generated
- [x] the script writes `TODO.md` from the tickets: lanes by the lane rule, blockers above the cards they block, cards in a stable order
- [x] running it on an unchanged tree changes nothing, and `scripts/check-board.sh` passes on its output
- [x] proof: two branches that each add a ticket conflict in `TODO.md`; after the merge, one run of the script gives a board with both cards
- [x] `AGENTS.md` says to run it (instead of editing `TODO.md` by hand) before each commit that touches `.scratch/`

## Comments

2026-10-18: done. `scripts/build-board.sh` writes `TODO.md` from the tickets. run it from anywhere in the repo, or pass the repo root: `scripts/build-board.sh [repo-root]`. it stops and writes nothing when a ticket lacks a field.

- each ticket now has `**Role:**`, `**Closed:**` (`yes` or `no`) and `**Priority:**` lines under its heading. the spec has no role. `**Type:**` and `**Due:**` are read when a ticket has them; none has them today.
- order: in a lane, by priority (lowest first), then feature slug, then number. a blocker in the same lane goes above the cards it blocks. a blocker in another lane cannot be above: lanes come in a fixed order (`Done` is last), so "blockers above" holds inside a lane only. the todo priorities 1 to 11 keep today's hand order (20, 19, 27, board 02, 24, 26, 23, 22, 08, 05, 04). backlog got 12 to 19 and done 20 to 26, in today's order.
- the first run gave today's board with one change: `arkan-flow` 01's card title is now "Arkan-mode replaces poteto-mode". the card title is the heading with a capital first letter, and that heading starts lowercase. the spec heading became "review and ci, parked (was 09, 10, 11, 12, 13, 14, 16, 18)" so its card title stays the same.
- a second run on the unchanged tree: `scripts/build-board.sh && git diff --exit-code` exits 0. `scripts/check-board.sh` prints `ok (26 cards)`.
- proof, in a throwaway clone of this branch: from one commit, branch `a` adds `board/issues/03-proof-a.md` and branch `b` adds `board/issues/04-proof-b.md`, each with priority 3, and each runs the script and commits. `git merge a` on `b` gives `CONFLICT (content): Merge conflict in TODO.md`. one run of `scripts/build-board.sh` writes a board with 28 cards, both proof cards in `Todo`, no conflict markers, and `scripts/check-board.sh` prints `ok (28 cards)`.
- stale blockers, left as they are: `arkan-flow` 08 lists 03, and `completion-loop` 02 lists `arkan-flow` 01. both blockers are closed, so they do not hold the cards back.
