# 24: catch a hidden dependency before the work is wasted

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 5

**What to build:** two guards against work done twice or failing because a dependency was never written down. (1) `to-tickets` writes a `touches:` line on each ticket (the folders or modules it will change), and a check asks the person about any two tickets that touch the same area with no blocking edge between them. (2) `arkan-mode` rule: a missing piece is a blocker, not a bug. when the code a task needs belongs to another open ticket, the agent stops, adds the blocker to its ticket, drops its claim and reports, instead of debugging.

**Blocked by:** None (can start immediately).

- [x] `to-tickets` writes `touches:` and runs the overlap check before it publishes
- [x] `arkan-mode` step 0 and the build step carry the missing-piece rule
- [x] proof: two planted tickets that touch one module with no edge make the check ask; a task whose needed function is another open ticket's work stops and reports within one round

## Comments

- 2026-10-18, agent: built. `to-tickets` gives each ticket a `**Touches:**` line (folders or modules, not files) and shows it in the quiz. step 5 runs the overlap check: each pair of tickets that share an area and have no edge, direct or through a chain, among the new tickets and the open tickets that already have a touches line. for each pair, it asks the user to add an edge, merge them, or keep them apart. the user approves only once every overlap is answered, and publishing is step 6. `arkan-mode` step 0 carries the rule "a missing piece is a blocker, not a bug", and section 1 step 4 (build) points back to it. `playbooks/spec.md` step 5 says a ticket that reports a missing blocker gets no merge and waits.
- 2026-10-18, agent: proof 1, the overlap check. a headless agent session in a throwaway repo, with the arkan skills as project skills, got `/to-tickets plan for the greet module (lib/): ticket A adds a shout function ...; ticket B adds a whisper function ... I see no order between them.` it drafted two tickets, both `Touches: the greet module (lib/) and the test runner`, with no blockers. then its `## Overlap check` said "Tickets 1 and 2 share an area ... Neither blocks the other", and noted that both add a line to one `case` block in `test.sh`. it asked "For the pair 1 and 2, which do you want?" with the three options, and stopped without writing a ticket file (`.scratch/greet/` stayed empty).
- 2026-10-18, agent: proof 2, the missing piece. a throwaway repo with two open `ready-for-agent` tickets and no edge between them. 01 adds `hello`, and its branch `ticket/01-hello` already exists, so another agent has claimed it. 02 adds `greet`, which "calls `hello NAME` and adds `!`". prompt: `/arkan-mode do the ticket .scratch/greet/issues/02-greet.md`, unattended. after 3 tool calls (read the ticket and tracker docs, look at the repo and the 01 branch, edit), it stopped. it set 02 to `**Blocked by:** 01`, ran `build-board.sh` (02 moved to `Backlog`) and `check-board.sh` (`ok (2 cards)`), wrote no code (`lib/` still holds only `bye.sh`), and reported "I did not build `greet`: ticket 02 (Add greet) depends on `hello`, which doesn't exist yet. `hello` belongs to ticket 01, which is still open."
  - limits: it saw the gap before it claimed 02, so "drop the claim" was not exercised. it left the ticket edit uncommitted on `main`, because the board rules forbid committing `TODO.md` to `main` and it had no branch for a board change alone. a first try of this proof did not count: its ticket did not say `greet` must use `hello`, so the agent wrote `greet` on its own, which was correct.
