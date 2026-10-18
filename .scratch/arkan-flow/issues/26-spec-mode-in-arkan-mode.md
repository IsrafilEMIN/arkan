# 26: spec mode in arkan-mode

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 6

**What to build:** `implement-spec` folds into `arkan-mode` as a spec playbook. given one ticket, `arkan-mode` runs one task loop; given a spec with tickets, it runs the spec playbook: integration branch, one subagent per ready ticket running the task loop, merge each, start the next ready ones, one review, one pr. gate: the agent may pick up any todo card tagged `#ready-for-agent` on its own, and for a spec it may run every such card in parallel; `#ready-for-human` and `#needs-info` cards wait. the person sets the tag (`triage`), so the tag is the person's go.

**Blocked by:** None (can start immediately).

- [x] `skills/arkan-mode/playbooks/spec.md` holds the 9 steps of `implement-spec`, with each ticket run through the task loop
- [x] `arkan-mode` step 0 picks the mode from what it was given, and carries the `#ready-for-agent` gate
- [x] `skills/implement-spec/` is removed, and `README.md` matches
- [x] proof: a small spec with two independent ready tickets and one blocked one: two run in parallel, the third starts after its blocker merges

## Comments

- 2026-10-18, agent: built. `playbooks/spec.md` holds the 9 steps. in step 4, each implementer runs the task loop from `SKILL.md` and skips the review and the pr, because the spec does each of them once (steps 7 and 8). step 0 picks one task loop or the spec playbook, and carries the `#ready-for-agent` gate. `skills/implement-spec/` is gone. `README.md` credits the playbook to `implement-spec` and shows spec mode in the flow. ticket 23's table no longer lists `implement-spec`.
- 2026-10-18, agent: proof setup. a throwaway repo with a spec and four tickets. 01 (`hello`) and 02 (`bye`) are `ready-for-agent` with no blockers. 03 (`greet`, which calls `hello`) is `ready-for-agent` and blocked by 01. 04 is `ready-for-human`. `scripts/build-board.sh` put 01, 02 and 04 in `Todo`, and 03 in `Backlog`. a control showed that 03's code on the base without 01 fails its proof (`hello: command not found`, `FAIL greet`, exit 1), so 03 really has to wait.
- 2026-10-18, agent: proof run 1, a script. the implementers were background shell jobs, each with its own worktree and branch, and a script followed steps 3 to 9. log: 01 and 02 started 3 ms apart on the same base. 03 started only after 01 merged, on the merge commit. 04 never started. `check-board.sh` printed `ok (5 cards)`. finding: when all three functions went in one file, 01 and 02 conflicted on merge although no edge joined them. that is the case ticket 24's `touches:` check is for.
- 2026-10-18, agent: proof run 2, a real agent. a headless agent session got the arkan skills as project skills and the prompt `/arkan-mode run the spec at .scratch/greet/spec.md ...`. it read `spec.md`, but it built all three tickets itself, one after another, "because each one is a one-line function". so step 4 now says to start the implementers all at once and never build a ticket in the orchestrating chat, however small.
- 2026-10-18, agent: proof run 3, a real agent with that fix. the orchestrator started the implementers for 01 and 02 as two background subagents in one message, and their file writes interleaved. it said 03 waits on 01 and 04 is `ready-for-human`. it merged 01 and 02, ran `./test.sh hello bye` (`ok hello bye`), and only then started the implementer for 03. then it ran a code-review subagent and removed the worktrees. history of `integration/greet`: `add hello (ticket 01)` and `add bye (ticket 02)` side by side, the merge, then `add greet (ticket 03)` on top. the final `./test.sh hello bye greet` printed `ok hello bye greet`, `check-board.sh` printed `ok (5 cards)`, and 04 stayed in `Todo`, never started.
  - limits of run 3: the harness denied every shell command to the background subagents, even `ls`, so they wrote files with Write and Edit, and the orchestrator ran the tests, commits and merges. the orchestrator also did the merges itself, with no merger subagent. so the order and the parallel start are proven by a real agent, but a subagent running the full task loop on its own shell is not.
