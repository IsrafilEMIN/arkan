# 01: reconstruct skills for the tern board

**What to build:** every skill that creates or changes a ticket writes a useful card on the `TODO.md` board, with proper details in the card's note line, and follows the `## Board` section of `docs/agents/issue-tracker.md`.

**Blocked by:** None (can start immediately). needs the owner's answers below first.

origin: a card the owner wrote by hand in `TODO.md` before the first commit (`c30da87`): "reconstruct skills according to tern board TODO.md. even refine skills to add proper details in notes section of TODO tasks". it had no ticket file until now.

already done (2026-10-18, see `LOGS.md`): the board rule was added to `pre-setup`, `implement`, `implement-spec`, `wayfinder`, `to-spec` and `triage`.

questions for the owner:

1. which skills does "reconstruct" cover: only the ones that touch tickets, or all skills in `skills/`?
2. "proper details in the notes section": today a card has one note line (`<path> · blocked by: <refs>`). what more should it hold? for example a one-line goal, the type, a due date.

- [ ] the owner answers both questions; the answers are recorded here
- [ ] each skill in scope writes cards in the agreed shape
- [ ] the card format in `docs/agents/issue-tracker.md` and `skills/pre-setup/issue-tracker-local.md` matches

## Answer

owner, 2026-10-18:

1. no skill carries the board rule. it lives only in the `## Board` section of `docs/agents/issue-tracker.md` and the `pre-setup` seeds it comes from. the copies in `to-spec`, `to-tickets`, `wayfinder`, `implement`, `implement-spec` and `triage` are removed.
2. `TODO.md` is only the cards: one card per ticket, as a picture of the tickets. every detail stays in the ticket file, so the note line stays as it is (`<path> · blocked by: <refs>`).
