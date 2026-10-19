# 04: one bash-3.2-safe entry point for the board

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 4

**What to build:** one script, `scripts/board.sh`, with `build` and `check` verbs over one shared ticket parse, safe on macOS `/bin/bash` 3.2.57. `scripts/build-board.sh` and `scripts/check-board.sh` go away in the same change.

origin: owner decision, 2026-10-18: replace the two board scripts with one bash-3.2-safe entry point.

**Blocked by:** None (can start immediately).

**Touches:** `scripts/`, `AGENTS.md`, `docs/agents/issue-tracker.md`, `eval/scenarios/`.

today `scripts/check-board.sh` fails at line 18 with `declare: -A: invalid option` and exit 2, and `scripts/build-board.sh` fails the same way: the owner's machine has no bash 4.

- keep the output strings `build-board: wrote TODO.md (N cards)` and `check-board: ok (N cards)`, and the exit codes: 2 for a missing `.scratch/` or `TODO.md`, 1 for problems.
- remove `declare -A`, `mapfile`, `${x,,}` and `${x^}`; every array expands safely under `set -u` on bash 3.2.
- the check may compare a card against the ticket fields (**Role:**, **Closed:**, **Due:** and the **Priority:** order) from the shared parse instead of re-deriving them; keep that minimal or note it as a follow-up.
- move every caller in the same change: `AGENTS.md` line 25, `docs/agents/issue-tracker.md` line 38, `eval/scenarios/run-one.sh` lines 29-30, the `eval/scenarios/ANSWERS.md` gates, and the arkan-sandbox copies via `arkan-flow` 37.
- re-earn the proofs of tickets 02 and 03: an unchanged tree writes no diff; two branches that each add a ticket, one run clears the `TODO.md` merge conflict; a ticket with one open and one closed blocker shows only the open one.
- do not gate this on `arkan-flow` 05; 05 later points the three pre-setup seeds at the one command.

- [x] `bash scripts/board.sh check` prints `ok` under `/bin/bash` 3.2.57
- [x] the three proofs pass
- [x] the board is rebuilt and checked

## Comments

2026-10-18: done. `scripts/board.sh build|check` replaces `scripts/build-board.sh` and `scripts/check-board.sh`; both old files are gone and every caller moved in the same change.

- one parse: the ticket fields (`**Role:**`, `**Closed:**`, `**Due:**`, `**Priority:**`, `**Blocked by:**`) are read once, and both verbs work from that list. `check` regenerates the board from the tickets and compares it byte for byte with `TODO.md`, so the card's title, tags, tick, due date, note, lane and order are all compared against the ticket fields instead of being re-derived by a second parser. no follow-up is needed for that item.
- bash 3.2: no `declare -A`, no `mapfile`, no `${x,,}` or `${x^}`; arrays are only read where they are known to be non-empty, and every run below is `/bin/bash` (3.2.57), the only bash on the machine. `scripts/board.sh check` prints `check-board: ok (38 cards)`.
- strings and codes stay as promised: `build-board: wrote TODO.md (N cards)`, `check-board: ok (N cards)`, exit 2 for a missing `.scratch/` or `TODO.md`, exit 1 for problems. `check` reports ticket problems the way `build` does (path-prefixed, stderr), then `check-board: N problem(s)`.
- `check` is stricter than the old one on purpose: `TODO.md` is generated, so any byte difference fails, not only what the old parser's rules could see.
- proof 1, no diff: on a clone of the branch head with no changes, `scripts/board.sh build` leaves no diff and no leftovers (`git status --porcelain` is empty), and `scripts/board.sh check` prints `ok (38 cards)`. the first run also showed byte parity with the board the two old scripts had written.
- proof 2, the merge conflict: two branches from one base, each adding one ticket and running `build`, give `CONFLICT (content): Merge conflict in TODO.md` on `git merge`; one run of `build` then writes 40 cards, both new cards in `Todo`, no conflict markers, and `check` prints `ok (40 cards)`.
- proof 3, open and closed blockers: a ticket with `**Blocked by:** 02, arkan-flow 06` (02 closed, 06 open) gets the note `blocked by: arkan-flow 06` and sits in `Backlog`; putting the closed 02 back in the note by hand makes `check` exit 1; after 06 closes, one run gives `blocked by: none`, the card moves to `Todo`, and the ticket's own `**Blocked by:**` line is unchanged.
- other negatives: a card with no ticket fails `check` (exit 1); a missing `TODO.md` fails `check` (exit 2); a missing `.scratch/` fails `build` (exit 2); no verb prints the usage line (exit 2); a ticket without `**Priority:**` fails `build` (exit 1) and writes nothing.
- one resolution change: a duplicate `<feature> <NN>` now resolves to the first ticket in file order; the old map kept the last. no feature has a duplicate number today.
- migration: `AGENTS.md`, `docs/agents/issue-tracker.md`, `eval/scenarios/run-one.sh` (the tool allow-list), the `eval/scenarios/ANSWERS.md` gates, and `arkan-flow` 37, which now says the rebuilt sandbox carries `scripts/board.sh`. the hand-built sandbox keeps the two old copies until 37 lands, and `arkan-flow` 05 still owns the pre-setup seeds.
