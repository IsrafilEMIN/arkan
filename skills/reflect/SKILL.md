---
name: reflect
description: "Run three parallel reviewers over this conversation's transcript, surface durable learnings, and route each to a concrete edit on an existing skill, for the person to approve. Use when the person says reflect or /reflect."
disable-model-invocation: true
---

# Reflect

Mine the current conversation for durable learnings, then route them into skill edits. `retro` does the same for findings that repeat across code reviews; reflect looks at one conversation.

Run it when the person says "reflect" or "/reflect". Skip it when the conversation is trivial, off topic, or already covered by a skill the agent followed correctly. One-offs are not learnings.

## 1. Locate the transcript

Find this conversation's own transcript file (where each harness keeps them: the table in `recall`). Read only the active workspace's folder; never glob across other projects, which holds unrelated private chats. List the newest files, read each one's first line, and take the file whose opening user message matches this conversation's. If none matches, or the folder is unreadable (underground's sandbox may deny it), pass a tight digest of the session instead, and say so.

## 2. Spawn three reviewers in parallel

Three subagents at once, in fresh contexts. They may use the run's connectors to look up tickets, chat threads and traces the transcript references, but they never write.

| lens | model, where the harness lets you pick | prompt |
|---|---|---|
| judgment | your strongest model | [`references/judgment-reviewer.md`](references/judgment-reviewer.md) |
| tooling | a fast model, a different family where possible | [`references/tooling-reviewer.md`](references/tooling-reviewer.md) |
| divergent | your strongest model | [`references/divergent-reviewer.md`](references/divergent-reviewer.md) |

Pass each prompt as written, with the transcript path or digest where marked. Reviewers return findings in their reply.

## 3. Synthesize

One subagent, your strongest model, with [`references/synthesizer.md`](references/synthesizer.md) as written and each reviewer's full output inlined where marked. It spot-checks citations and returns an accepted / rejected / backlog list.

## 4. Structural enforcement check

Move any accepted item that a lint rule, script, metadata flag or runtime check would enforce more reliably to backlog, per **encode lessons in structure** (`principle-encode-lessons-in-structure`). `correct` is the skill for building that enforcement.

## 5. Apply

Show the synthesizer's full accepted / rejected / backlog output and wait for the person's explicit approval before applying any accepted edit. The person picks the subset and may redirect routings. Skill changes affect every future agent; never apply them on your own.

File each backlog item as a ticket on the repo's tracker without waiting (in arkan, under `.scratch/`, then rebuild the board). Only the accepted list waits for approval.

Follow each approved row's routing exactly:

- a trivial existing-skill edit (one bullet, a tightened sentence, a stale fact): make it directly;
- a substantive existing-skill edit (a new section, a new table, more than ~10 lines): write it per `writing-for-agents`;
- `tune description: <skill path>` (the skill exists but didn't trigger when it should have): rework its `description` and trigger phrases per `writing-for-agents`;
- `new skill via writing-for-agents: <kebab-name>`: create it per `writing-for-agents`; don't invent the shape ad hoc.

Ship the edits as one pull request through arkan's normal flow; `scripts/check.sh` must pass (it checks each skill's front matter).

## 6. Summarize for the person

A short list, no preamble:

- edits applied: `<skill path>`, what changed, one line each;
- new skills created: `<skill path>`, one line each (rare);
- backlog filed: `<ticket>`, one line each;
- dropped: one line per rejected finding, with the synthesizer's reason.
