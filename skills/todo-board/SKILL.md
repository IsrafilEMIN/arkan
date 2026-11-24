---
name: todo-board
description: "Create or update a repo's TODO.md in the format Tern's board block shows as a kanban. Use for /skill:todo-board, \"make a todo list for this repo\", \"set up the board\", or when you plan or track work in a repo that has a TODO.md."
---

# TODO board

One `TODO.md` per repo, at the repo root (`git rev-parse --show-toplevel`). Tern's board block (`⌥⌘K`) shows it as a kanban, and every board edit (drag, check, rename, new card) autosaves back to the file. The file is the only state: what you write, the user sees; what the user moves, you read.

## Format

```markdown
# <repo name>

## Ready for Dev

- [ ] Card title #tag due:2026-12-01
  A note line, indented two spaces.
  - [ ] Subtask
  - [x] Done subtask
- [ ] Another card

## Dev

## Ready for Test

## Test

## Blocked

## Done

- [x] Finished card
```

- Each `##` heading is a lane, in file order. An optional `#` title above the lanes stays in place.
- Each top-level `- [ ]` / `- [x]` line is a card. Keep titles short; put detail in notes.
- `#word` in the title is a tag. `due:YYYY-MM-DD` is a due date (the board also reads `📅 YYYY-MM-DD` and `@{YYYY-MM-DD}`; use `due:`).
- Lines indented two spaces under a card are its notes; indented checkboxes are its subtasks.
- The lane titled `Done` is the done lane: moving a card in checks it, moving it out unchecks it. The board marks any other done lane with a `**Complete**` line under its heading; keep that line.

## Create

1. If `TODO.md` exists at the root, do not replace it. Read it and add to it. If its lanes differ from the six below, ask the user before you change them.
2. Otherwise write the file above with the lanes `Ready for Dev`, `Dev`, `Ready for Test`, `Test`, `Blocked` and `Done`, in that order, and one card per task the user named, or per task you plan. Leave the example cards out.
3. Do not commit, stage or gitignore it unless the user asks.

## Update

- Read `TODO.md` again before each edit. The user may have dragged cards or added lanes since your last read; keep their order, lanes and cards.
- Change only the lines for your cards. Move a card by moving its line with its indented notes and subtasks.
- Move cards as work moves. Do not batch moves to the end.

| Lane | A card goes here when |
| --- | --- |
| `Ready for Dev` | it is planned and nothing blocks it |
| `Dev` | you start to implement it |
| `Ready for Test` | the implementation is complete and committed |
| `Test` | you start to run its checks |
| `Blocked` | it cannot go on until someone or something else acts |
| `Done` | its checks pass; set `[x]` |

- When a check fails in `Test`, move the card back to `Dev` and add a note that gives the failure.
- When you move a card to `Blocked`, add a note that gives the blocker and the lane it came from. When the blocker is gone, move it back to that lane.
