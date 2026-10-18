# 02: build the board from the tickets

**What to build:** a script that writes `TODO.md` from the ticket files under `.scratch/`, so a merge conflict in `TODO.md` is fixed by running it again, never by hand. the ticket files are already the source of truth; the card only mirrors them.

**Blocked by:** None (can start immediately).

for this, each ticket file must hold what its card shows today: title, `#<role>`, any `#<type>` or `📅` date, and whether it is closed (lane `Done`). the role and the closed state move from the card into the ticket file, for example a `Role:` line and a `Closed:` line near the top.

- [ ] every ticket file holds its role and closed state; `docs/agents/issue-tracker.md` `## Board` says so, and that the board is generated
- [ ] the script writes `TODO.md` from the tickets: lanes by the lane rule, blockers above the cards they block, cards in a stable order
- [ ] running it on an unchanged tree changes nothing, and `scripts/check-board.sh` passes on its output
- [ ] proof: two branches that each add a ticket conflict in `TODO.md`; after the merge, one run of the script gives a board with both cards
- [ ] `AGENTS.md` says to run it (instead of editing `TODO.md` by hand) before each commit that touches `.scratch/`
