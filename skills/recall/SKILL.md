---
name: recall
description: "Rebuild your recent working context from your own chat history, live state, and the shared record (tickets, prior fixes, incidents), then hand back a tight current-state brief. Use for 'recall my work on X', 'catch me up', 'what have I been working on', 'where did I leave off', before starting or resuming work."
disable-model-invocation: true
---

# Recall

**Before you start or resume work, you rebuild the person's recent working context and hand back a tight capsule of where things stand now and what to do next.**

Keep it tight and on topic. Read only what the in-scope threads need, then stop.

Context lives in two records. Your own chat history holds what you did and decided. The shared record holds everything that happened around the same code under other names: the symptoms users keep reporting, the fixes that shipped and got reverted, the errors still firing. That second record is what the `why` skill searches, across source control, the issue tracker, chat and issue channels, long-form docs, and error tracking. A feature with a long bug tail keeps most of its story there, so don't rebuild it from transcripts alone.

**Where transcripts live** (read only the active workspace's; never another project's without being asked):

| harness | transcripts |
|---|---|
| claude code | `~/.claude/projects/<slug>/<session-id>.jsonl`, where `<slug>` is the workspace path with each character that is not a letter or a digit turned into `-` (`/home/user` → `-home-user`, `/Users/me/.agents` → `-Users-me--agents`); one json message per line |
| codex | `~/.codex/sessions/<yyyy>/<mm>/<dd>/*.jsonl` (check it exists) |
| omp | `~/.omp/agent/sessions/<slug>/<timestamp>_<uuid>.jsonl`, one file per chat, with a same-named folder beside it holding extra files; `<slug>` drops the home folder from a path inside home and turns each `/` into `-` (`/Users/me/dev/app` → `-dev-app`), and wraps a path outside home in `--` (`/private/tmp` → `--private-tmp--`) |
| other harnesses | ask the person, or skip the chat history and say so |

Under a sandbox these folders may be unreadable; then say so and work from the shared record and live state.

1. **Classify, then route.** Resuming one specific prior chat is the `session-pickup` playbook, not this. Turning habits into a lasting skill is `automate-me`. A person-readable summary of your work is a different task. What changed in this chat since the person's last message is the `ketchup` skill. Recall loads working context across recent chats before you act. If the person already gave you a full state capsule (paths, branch, the change), use it and skip the mining.
2. **Lock the scope before searching.** Pin the window ("recent" is a real range: default the last 7 days), the topic if named, and the workspace (default the active one). State the scope back. Never quietly turn "all" into "recent N".
3. **Fan out across your chat history.** Spawn parallel subagents on a fast model, each taking a slice. Tell each to order candidates by real modification time (`ls -t`), never by file name; to grep the topic first and read only the matching chats and only their relevant parts; and to skip the current chat plus obvious noise (subagent, eval and test chats). Each returns one block per chat: topic, the person's goal, decisions, open threads, struggles and corrections, and artifacts (pull requests, tickets, branches), each citing the session id. For one or two chats, skip the fan-out and search directly. The raw transcripts stay in the subagents; you get only their findings.
4. **Sweep the shared record** whenever the topic names a feature, file, subsystem, area or bug. This is the default, and "my work on X" does not exempt it. Hand it to `why`'s source investigators, but steer their question from "why was this built this way" to "what is the current state, what has been tried and did not hold, and what is still reported". Run them in parallel with the chat mining, and keep `why`'s posture: one investigator per source, null results are findings, skip an unavailable source and say so. Skip this step only for pure activity recall with no named target ("what did I do this week").
5. **Verify against live state.** Check the pull requests, branches and tickets the mining and the sweep surfaced with `git`, `gh`, and the tracker. When the answer hinges on what an agent really did (the tools it ran, files it read, errors it hit), read the full transcript, not a trimmed copy.
6. **Write the brief** to the contract below. Group by thread. Stay on the named topic.

## Output contract

Lead with the capsule, then the thread status, then the problems, then the next move.

- **Capsule.** At most 5 bullets: what this work is and where it stands.
- **Threads.** One line each, with exactly one status tag: `[merged #N]`, `[open PR #N]`, `[in flight <branch>]`, `[verified, uncommitted]`, `[reverted #N]`, or `[planned, not started]`. A thread with no tag is not done, so tag it.
- **Problems.** At most 5, the recurring ones. Include the symptoms users keep reporting and any fix that shipped and was reverted, so the next attempt starts where the last one failed.
- **Next move.** The single most useful next action, concrete.

An adjacent feature or ticket stays out unless it blocks this one. When the brief outgrows a screen, cut detail before you cut threads. Write it per `unslop`, cite chat findings by session id and shared-record findings by source (pull request, ticket, error-tracker issue), and strip private context before any public output.

**Reply:** the brief, to the contract above.
