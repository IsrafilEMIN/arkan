# 03: card shows only open blockers

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 4

**What to build:** the card's note line lists only the blockers that are still open, so a reader does not think a card is blocked by a ticket that is done. today, when a ticket closes, the cards it blocked still say `blocked by: 03`, though 03 is in `Done` (`arkan-flow` 08 lists 03; `completion-loop` 02 lists `arkan-flow` 01). the lane is right; only the note is stale.

**Blocked by:** None (can start immediately).

the ticket's own `**Blocked by:**` line is history: it keeps every blocker it ever had and is never rewritten. only the card note drops the closed ones.

- [x] `scripts/build-board.sh` writes the note with only the open blockers, in the ticket's order; when all are closed, the note says `none`
- [x] `scripts/check-board.sh` expects the same: the ticket's blockers minus those whose card is in `Done`
- [x] `docs/agents/issue-tracker.md` `## Board` says the note shows only open blockers, and that the ticket's line is not rewritten
- [x] the cards of `arkan-flow` 08 and `completion-loop` 02 say `blocked by: none`; a second run changes nothing; `scripts/check-board.sh` prints `ok`
- [x] proof: in a throwaway clone, a ticket with one open and one closed blocker shows only the open one

## Comments

2026-10-18: done. `scripts/build-board.sh` now writes the card note with only the blockers that are still open, in the ticket's order, and `none` when all are closed. the ticket's `**Blocked by:**` line is left as it is. a blocker that is not a ticket still stops the script.

- `scripts/check-board.sh` reads the ticket's blockers, drops each one whose card is in `Done`, and compares the rest to the note. a note that still lists a closed blocker fails.
- `docs/agents/issue-tracker.md` `## Board`: the card note shows `<open refs, or none>`, the ticket's line is history, and **Resolve** drops the closed ticket from the notes of the cards it blocked.
- first run: the cards of `arkan-flow` 08 (was `blocked by: 03`) and `completion-loop` 02 (was `blocked by: arkan-flow 01`) now say `blocked by: none`; no lane changed. a second run: `scripts/build-board.sh && git diff --exit-code` exits 0. `scripts/check-board.sh` prints `ok (27 cards)`.
- proof, in a throwaway copy of this branch (the files copied, without `.git`): a ticket `board/issues/04-proof-mixed.md` with `**Blocked by:** 02, arkan-flow 06` (board 02 closed, `arkan-flow` 06 open) gets the note `blocked by: arkan-flow 06`, in `Backlog`, and `scripts/check-board.sh` prints `ok (28 cards)`. writing the stale note `blocked by: 02, arkan-flow 06` by hand makes `scripts/check-board.sh` fail with one problem. after `arkan-flow` 06 is closed, one run gives `blocked by: none`, the card moves to `Todo`, the ticket's line is unchanged, and the check prints `ok (28 cards)`.
