# 04: one bash-3.2-safe entry point for the board

**Role:** ready-for-agent
**Closed:** no
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

- [ ] `bash scripts/board.sh check` prints `ok` under `/bin/bash` 3.2.57
- [ ] the three proofs pass
- [ ] the board is rebuilt and checked

## Comments
