---
name: recall
description: "Tell the person where things stand, in one of two scopes. Across recent chats: rebuild working context from your own chat history, live state, and the shared record (tickets, prior fixes, incidents) into a tight current-state brief. For this chat: catch them up on what changed since their last message, in plain words and small visuals, and list every item waiting on them. Use for 'recall my work on X', 'where do things stand', 'what have I been working on', 'where did I leave off', 'catch me up', 'ketchup', 'what changed', before starting or resuming work."
disable-model-invocation: true
---

# Recall

**Tell the person where things stand: across recent chats, a tight capsule of where the work stands and what to do next; for this chat, what changed since their last message and every call waiting on them.**

Keep it tight and on topic. Read only what the in-scope threads need, then stop.

Context lives in two records. Your own chat history holds what you did and decided. The shared record holds everything that happened around the same code under other names: the tickets and their comments (`docs/agents/issue-tracker.md`; for a local tracker, `.scratch/` and the board in `TODO.md`), the fixes that shipped and got reverted, the errors still firing. That second record is what the `why` skill searches. A feature with a long bug tail keeps most of its story there, so don't rebuild it from transcripts alone.

**Where transcripts live** (read only the active workspace's; never another project's without being asked):

| harness | transcripts |
|---|---|
| claude code | `~/.claude/projects/<slug>/<session-id>.jsonl`, where `<slug>` is the workspace path with each character that is not a letter or a digit turned into `-` (`/home/user` → `-home-user`, `/Users/me/.agents` → `-Users-me--agents`); one json message per line |
| codex | `~/.codex/sessions/<yyyy>/<mm>/<dd>/*.jsonl` (check it exists) |
| omp | `~/.omp/agent/sessions/<slug>/<timestamp>_<uuid>.jsonl`, one file per chat, with a same-named folder beside it holding extra files; `<slug>` drops the home folder from a path inside home and turns each `/` into `-` (`/Users/me/dev/app` → `-dev-app`), and wraps a path outside home in `--` (`/private/tmp` → `--private-tmp--`) |
| other harnesses | ask the person, or skip the chat history and say so |

Under a sandbox these folders may be unreadable; then say so and work from the shared record and live state.

1. **Classify, then route.** Resuming one specific prior chat is the `session-pickup` playbook, not this. Turning habits into a lasting skill is `automate-me`. A person-readable summary of your work is a different task. "What changed", "catch me up" on the work in front of you, or "ketchup" asks about this chat: follow [This chat](#this-chat) and skip the steps below. Otherwise recall loads working context across recent chats before you act. If the person already gave you a full state capsule (paths, branch, the change), use it and skip the mining.
2. **Lock the scope before searching.** Pin the window ("recent" is a real range: default the last 7 days), the topic if named, and the workspace (default the active one). State the scope back. Never quietly turn "all" into "recent N".
3. **Fan out across your chat history.** Spawn parallel subagents on a fast model, each taking a slice. Tell each to order candidates by real modification time (`ls -t`), never by file name; to grep the topic first and read only the matching chats and only their relevant parts; and to skip the current chat plus obvious noise (subagent, eval and test chats). Each returns one block per chat: topic, the person's goal, decisions, open threads, struggles and corrections, and artifacts (pull requests, tickets, branches), each citing the session id. For one or two chats, skip the fan-out and search directly. The raw transcripts stay in the subagents; you get only their findings.
4. **Sweep the shared record** whenever the topic names a feature, file, subsystem, area or bug. This is the default, and "my work on X" does not exempt it. Hand it to `why`'s source investigators, but steer their question from "why was this built this way" to "what is the current state, what has been tried and did not hold, and what is still reported". Run them in parallel with the chat mining, and keep `why`'s posture: one investigator per source, null results are findings, skip an unavailable source and say so. Skip this step only for pure activity recall with no named target ("what did I do this week").
5. **Verify against live state.** Check the pull requests, branches and tickets the mining and the sweep surfaced with `git`, `gh`, and the tracker. When the answer hinges on what an agent really did (the tools it ran, files it read, errors it hit), read the full transcript, not a trimmed copy.
6. **Write the brief** to the contract below. Group by thread. Stay on the named topic.

## Output contract

Lead with the capsule, then the thread status, then the problems, then the next move.

- **Capsule.** At most 5 bullets: what this work is and where it stands.
- **Threads.** One line each, with exactly one status tag: `[merged #N]`, `[open PR #N]`, `[in flight <branch>]`, `[verified, uncommitted]`, `[reverted #N]`, or `[planned, not started]` (a ticket on the board). A thread with no tag is not done, so tag it.
- **Problems.** At most 5, the recurring ones. Include the symptoms users keep reporting and any fix that shipped and was reverted, so the next attempt starts where the last one failed.
- **Next move.** The single most useful next action, concrete.

An adjacent feature or ticket stays out unless it blocks this one. When the brief outgrows a screen, cut detail before you cut threads. Write it per `unslop`, cite chat findings by session id and shared-record findings by source (pull request, ticket, error-tracker issue), and strip private context before any public output.

**Reply:** across recent chats, the brief, to the contract above; for this chat, the reply that [This chat](#this-chat) describes.

## This chat

Catch the person up on what changed in this chat since the last message they wrote before asking, and help them understand each change, not only where it stands. Then lay out every call waiting on them so they can make it from your reply alone. Notifications, github events and subagent results are not their messages. Assume they remember their last message and nothing after it.

Use `bro`'s voice, not its task: plain words, short sentences, no jargon, like one person catching up another. Say what changed for the person, not how you did it: "the tests pass", not "CI is green". Leave out hashes, file paths, commands, build numbers and test counts unless they need one to act. Call each pull request, branch or agent by a name they would know, not a label you invented. If a fact needs context to make sense, give the context or leave the fact out. The person's own style rules (for example all lowercase) win.

### Gather what changed

Keep this turn read-only. Make visuals only from what you already have: don't change code, start an app or a job, or post anything. Collect your own work since that message, subagent reports, and messages from anyone else in this chat. Check the current state of each pull request, ci run or agent this chat touched, and the board. Check each number you will show against the facts it comes from, and say so when you correct one.

An action item is a call or step only the person can take: a product choice, a merge, an approval, an irreversible action, access you lack, or a step on their machine (an install only they can run). Include any still waiting on them, even one raised before their last message. Work you can still do yourself is not an action item. Never invent a call to fill the reply. A step they did not ask for and the work does not need is not an action item, unless it is irreversible and waiting on them: give it one line and no visual.

One call can cover many items, such as each pull request waiting for a merge. For each item, collect its link, what it changes for users, the evidence behind your pick, its risk, and your pick. Write "unknown" for a fact the call needs that you do not know. Leave out a link you do not have.

### Write the reply

Spend words on the calls, not on the story. Keep what happened under 100 words, not counting pictures, and shorter when less happened. Leave out work that changed nothing for the person. Give each item about 30 words. The reply grows with the number of items: two items need well under 150 words in all, not counting pictures, and thirty need far more. Never cut items or shrink them to fit a word count, and never put a count or a link in place of an item. A link can add depth, but the reply alone must be enough to decide.

Open with one short sentence that names what waits on the person, or says nothing does. If nothing happened and nothing waits, say so and stop.

Then show what happened, pictures first: embed inline the screenshots and videos the work produced, then any diagram that explains a change. Then one short bullet per thing the person asked for: what came of it, and whether it is done, still running, failed, or not checked. Write each line the way you would say it out loud: "Search was slow from a missing index", not "Search review: done". Name any bug found and fixed on the way. Each line must stay true when read alone. Never mark something done that still waits on the person, and leave out anything the action items say. Under the summary, at most three short lines that change what the person knows or must do. Then one line naming work left that you can do yourself.

Then the action items. Ask the call the person owns (merge, approve, pick) and give your pick. A step you would take first goes in your pick; so does anything that must happen first, and anything that cannot be undone. Give the number or link of each pull request, ticket or agent a call is about.

Fit the shape to the call. A call about one item is one bullet: the call, your pick, what it changes for users, the evidence, and its risk. When items share a call, write the call and your pick once, then one bullet per item, riskiest first: its link and name, what it changes for users, the evidence, and its risk. Name an item's pick only where it differs from the call's. Give each item's risk even when low ("Low risk: only the colors change."). Say what waiting costs only when it is more than a delay (a deadline, lost data).

For a call between options, give every option the work weighed, each with what it gets the person and what it costs, and the current state when there is one. Those costs are the call's risk; add no separate risk line. When the screenshots above show the options, write each option's gain and cost under its screenshot.

### Visuals

A visual is a picture: a screenshot, a video, a mermaid diagram (or a small plain-text box chart where mermaid does not render), a chart, or a generated image. A markdown table is not a visual.

Draw when something is easier to grasp as a picture than as sentences: how a design or system works, a pull request stack with each one's state, a before and after of a fix, options side by side. Never draw a status list, a list of action items, or boxes with nothing connecting them. Never give a fact twice.

Keep each visual readable at a glance: at most six boxes, at most eight words in each, in plain words a person would say. A fact that needs a sentence belongs in the text, or nowhere.

Embed screenshots and videos inline when the change is visible, not only as links. If a visible change has none, mark its line "no screenshot yet" and say what changed on screen. Draw diagrams and charts only from facts you have. Never invent a number, and never draw a screen you did not capture. Link only artifacts that exist.
