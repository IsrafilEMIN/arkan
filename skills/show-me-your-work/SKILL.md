---
name: show-me-your-work
description: "Keep a reviewable decision trail for long-running or unattended work: a TSV log with one row per decision (what, why, evidence, result). Local by default; commit it when a reviewer needs the trail to trust the result. Use for /show-me-your-work, autonomous or multi-phase runs, or work a person reviews after stepping away."
---

# Show me your work

Keep one decision log per run of work. arkan-mode asks for a decision trail on long or unattended work, and `figure-it-out` routes its trail here; this skill owns the format. Other skills reference it by name and do not restate the columns.

## The format

One TSV file, one row per decision. Cells stay on one line. Evidence is a pointer, not prose.

Start a clean log from [`references/decision-log-template.tsv`](references/decision-log-template.tsv) (the header row). Columns:

- **ts.** ISO 8601 timestamp.
- **phase.** The phase or workstream.
- **decision.** What was chosen or done, one line.
- **why.** The reason in plain words. If a principle drove it, say it plainly, not as a tag.
- **evidence.** A pointer that proves it: a commit sha, a pull request number, a `file:line`, a ticket, or an artifact or screenshot path. Never a paragraph.
- **result.** The outcome or predicate state: `tests green`, `reverted`, `pixel-diff 0`, `INCONCLUSIVE`, `open`.

An example, plain enough for a reviewer to read at a glance:

```
ts	phase	decision	why	evidence	result
2026-05-24T09:02:00Z	frame	counted the work first, about 100 components and roughly 75 hours	wanted to know the size before starting a long run	commit 3a9f1c2	found 5 things to sort out before starting
2026-05-24T09:40:00Z	harness	took screenshots of the old version before changing anything	so we can compare old against new and catch any visual change	scripts/snapshot.sh, baseline/	saved 120 reference screenshots
2026-05-24T11:15:00Z	widget	moved the widget styles over without changing how it looks	keep the change small and the result identical	commit 7c21e0a, pixel-diff 0	looks identical, tests pass
2026-05-24T12:30:00Z	widget	threw out a helper's work because its screenshots were blank	checked the real files instead of trusting its summary	worktree reset	reverted, tightened the instructions for next time
```

## Logging a row

Write each entry the way you'd tell a teammate what you did: plain words, concrete actions, per `unslop`.

Use [`scripts/log.sh`](scripts/log.sh) `<logfile> <phase> <decision> <why> <evidence> <result>`. It stamps `ts`, writes the header on first use, strips stray tabs and newlines, and prefixes any cell starting with `=`, `+`, `-` or `@` with a single quote, so a spreadsheet never runs a cell as a formula. A bare `printf` works too, but then guard the same bytes yourself when cells come from generated or outside text.

Log decision points and checkpoints, not every action: a fork chosen, a unit done with its verification result, a pivot or revert with its trigger, a blocker found, a gate fixed. For loop runs, one row per iteration. Skip the trivial.

A run is one agent conversation, including its later turns and any summary of it. A pickup (the session-pickup playbook), a replacement agent or a new chat starts a new run. When a run adds to a log that already has rows, its first row has phase `start`, and so does its first row after another run's `start` row. So a run that comes back to a log in a later turn first reads the log's last rows to see whether another run wrote since. A `start` row names the `ts` range of the rows before it that this run did not write, and its evidence names this run (a session id or branch). Use phase `start` for nothing else.

## Where it lives

By default the log is a working file, not committed: `decisions.tsv` in the worktree, or `.audit/<task-slug>.tsv` when several efforts run at once. Do not `git add` it.

Commit it when the work is ambitious enough that a reviewer needs the trail to trust the result, and link it from the pull request body.

## Rules

- Append-only. A wrong call gets a new row that supersedes it. Never edit or delete history.
- Prefer evidence from committed scripts over one-off commands (**encode lessons in structure**, `arkan-mode/principles/agents.md`).

## Audit the log before you hand back

At the end of the run, check the log told the truth. Compare this run's rows with what really happened in this conversation: your own tool calls and their outputs. If the harness lets you read this run's own transcript file, use it; never read other sessions' transcripts. Each stretch of this run's rows begins at one of its `start` rows (or the first row, if this run made the log) and ends at the next `start` row of another run:

- every row maps to a real decision or action;
- each row's evidence resolves and shows what the row claims;
- a fork, pivot or abandoned approach that shaped the work but is not logged is a gap: add it.

Correct the log, not the story. The audit never edits or removes a row, even an invented one. When a row records neither a real decision nor a real action, or its claim or evidence is wrong, add a row that supersedes it with what really happened and a pointer that resolves. This audit does not check other runs' rows; if this run's work shows one is wrong, supersede it like any wrong call.

## Cross-model review of the trail

Before handing back, spawn a read-only subagent in a fresh context, on a different model family from the one that did the work where the harness allows (else the same model, and say so). Self-review is not a substitute. It reads the trail (and the transcript, if it can) and flags what the person should look at. It does not redo the work; it scans for what is weak or risky:

- decisions logged with weak or missing evidence;
- verification skipped, or claimed without proof;
- choices that look risky in hindsight (premature, scope creep, papering over a symptom);
- gaps the person would miss on a quick skim.

Every reply for a run that produced a trail ends with an "attention" section. Lead with the reviewer's model on its own line (`reviewed by <model>`, or `reviewed by the same model, fresh context`), then list each flag, pointing at specific rows or moments. "No flags" is a valid value.

## Reviewing the trail

Read it top to bottom, follow the evidence pointers, spot-check. GitHub renders a committed TSV as a table; `column -s$'\t' -t decisions.tsv` renders it in a terminal.
