# 01: check that every card has a ticket

**What to build:** a small script that reads `TODO.md` and the `.scratch/` folders and fails when the board and the tickets disagree, so a card with no ticket (like the old "reconstruct skills" card) cannot creep in again.

**Blocked by:** None (can start immediately).

the script fails when:

- a card does not match the card format in the `## Board` section of `docs/agents/issue-tracker.md` (number, title, `#<feature-slug>`, note line)
- a card's path points at no file, or a ticket file has no card
- a card's `blocked by` differs from the `**Blocked by:**` line in its ticket file
- a card is in the wrong lane by the lane rule

- [ ] the script exists in the repo and runs with no tool beyond bash and git
- [ ] it passes on the board as it is now
- [ ] proof: a planted card with no ticket makes it fail, with a message that names the card
- [ ] `AGENTS.md` or `pre-setup` says when to run it (before each commit that touches `TODO.md`, or in ci when there is ci)
