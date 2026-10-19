# 48: pre-setup checks what a file says, not only that it exists

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 32

**What to build:** `skills/pre-setup/scripts/setup.sh check` reads the content of the `tracker`, `board` and `agents-block` items, not only whether the file or heading is there. A repo whose files exist but break the tracker contract (seam row 5) reads `out of date`, with the reason and the step that fixes it, and not `ok`.

Found in underground on 2026-10-19. All three items read `ok` there. But `board.sh check` run against underground reports 234 problems: its tickets use plain `Blocked by:` lines with no `**Role:**`, `**Closed:**` or `**Priority:**`; its board cards carry extra notes; and its `AGENTS.md` board line says to edit `TODO.md` by hand. Underground fixes its side in its own ticket (`repo-seam` 02).

**Blocked by:** None (can start immediately).

- [x] `tracker`: with a local tracker, each `.scratch/*/issues/*.md` has the fields `board.sh` reads. If not: `out of date`, the number of tickets and the first few paths and missing fields
- [x] `board`: with a local tracker, it runs `board.sh check` and reads `ok` only when that prints `ok`. Otherwise: `out of date`, the problem count, and `run board.sh build` (or, when the tickets are the cause, "fix the tickets first")
- [x] `agents-block`: `ok` only when the `## Agent skills` block carries the board line that names `board.sh build` and `board.sh check`. An older block reads `out of date`, and the skill shows the line to add
- [x] with a github or gitlab tracker, `board` keeps today's check (the board is hand-kept there, as that tracker's seed says)
- [x] `out of date` is a state the skill already knows (ticket 05's answer); `apply` never rewrites tickets on its own. Moving tickets to the contract is the repo's own change, with the person's yes
- [x] how the repo's ci runs `board.sh check` when the repo has no copy of the script (seam row 5 says repos get none): decide, and record it in `docs/seam.md` row 5. Options: ci fetches arkan at a pinned commit; or the check stays local only
- [x] proof: `setup.sh check` in arkan reads `ok` for all three; against underground's `main` (before its `repo-seam` 02) it reads `out of date` for `tracker`, `board` and `agents-block`, with the reasons; after a scratch fix of one ticket, the count drops by that ticket's problems

## Comments

- 2026-10-19, owner: capture this in a ticket for each repo. arkan fixes the check; underground moves its tickets to the contract.
- 2026-10-19: closed. `setup.sh check` in arkan reads `tracker ok`, `board ok`, `agents-block ok`; against underground `main` all three read `out-of-date` (tracker 60 of 60 tickets, 238 problems; board 238 problems with `fields` also failing; agents-block missing the `board.sh build`/`board.sh check` line). Adding `**Role:**`, `**Closed:**` and `**Priority:**` to one ticket dropped the field problem count 238 to 235. Seam row 5 records that a local tracker's checks stay local.
