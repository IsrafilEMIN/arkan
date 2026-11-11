---
name: reflect
description: Spawn three parallel review subagents over the active transcript, surface learnings, and route each to a concrete edit on an existing skill. Use when the user says reflect.
---

# Reflect

Mine the current conversation for durable learnings, then route them into skill edits.

Invoke when the user says "reflect" or "/reflect". Skip when the conversation is trivial, off-topic, or already covered by an existing skill the parent followed correctly. One-offs are not learnings.

## 1. Locate the active transcript

Before fanning out, find this conversation's transcript: `recall` has the table of where each harness keeps them. Read only the active workspace's folder; never glob across other projects. That crosses workspace boundaries and reads private chats from unrelated projects. List the newest transcript files, read the first JSONL line of each, and take the file whose `message.content[0].text` contains the conversation's opening user prompt. If none matches, or the folder is unreadable (a sandbox may deny it), pass a tight digest of the session instead.

## 2. Spawn three reviewers in parallel

One message, three subagent calls, in a mode that keeps MCP access: reviewers look up the tickets, chat threads, and observability traces the transcript references.

Match each model to the job, per the Subagents section of the `arkan-mode` skill: judgment, divergent and the synthesizer on your strongest model, tooling on a fast model, a different family where possible. If the harness refuses a model, use the closest one it accepts and say so. Where the harness lets you pick a reasoning level and a fast or standard speed, pick them for the job.

| Lens | Model, where the harness lets you pick | Prompt template |
|---|---|---|
| Judgment | your strongest model | [`references/judgment-reviewer.md`](references/judgment-reviewer.md) |
| Tooling | a fast model, a different family where possible | [`references/tooling-reviewer.md`](references/tooling-reviewer.md) |
| Divergent | your strongest model | [`references/divergent-reviewer.md`](references/divergent-reviewer.md) |

Pass each template verbatim, substituting the transcript path or digest where marked. Reviewers return findings in their reply.

## 3. Synthesize

One more subagent call, on the same model as judgment and divergent, in a mode that keeps MCP access: it spot-verifies citations through MCP. Pass `references/synthesizer.md` verbatim, with each reviewer's full output inlined where marked. It returns an Accepted / Rejected / Backlog list.

## 4. Structural enforcement check

Move any Accepted item that a lint rule, script, metadata flag, or runtime check would enforce more reliably to Backlog, per **encode lessons in structure** (`principle-encode-lessons-in-structure`).

## 5. Apply

Present the synthesizer's full Accepted / Rejected / Backlog output and wait for explicit approval before applying any Accepted edit. The user picks the subset and may redirect routings. Skill changes affect every future agent. Do not auto-apply.

File each Backlog item to your team's devex or backlog tracker without waiting. Only the Accepted list waits for approval.

Skill edits stay proposals: show the person which skill file each edit lands in, apply the edit only after they approve it, and never edit a skill without approval. Never open a PR or push.

Follow each approved row's Routing exactly:

- Trivial existing-skill edit (a one-line bullet, a tightened sentence, a stale fact corrected): the parent does it directly.
- Substantive existing-skill edit (a new section, a new pattern table, more than ~10 lines): draft it, test it, and iterate before applying.
- `tune description: <skill path>` (the skill exists but didn't trigger when it should have): rework the description until a fresh agent picks the skill up on the prompts that should have fired it.
- `new skill: <kebab-name>`: create the skill, following the shape of the existing skills. Do not invent the shape ad hoc.

If your environment ships a SKILL.md validator, run it on every touched skill before declaring done.

## 6. Summarize for the user

Short list, no preamble:

- Edits applied: `<skill path>`. What changed, one line each.
- New skills created: `<skill path>`. One line each (rare).
- Backlog filed to the devex tracker: `<issue title>` (`<tags>`). One line each.
- Dropped: one line per rejected finding + reason from the synthesizer.
