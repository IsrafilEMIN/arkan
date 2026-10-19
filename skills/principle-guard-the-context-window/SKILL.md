---
name: principle-guard-the-context-window
description: "Apply when context is filling up: large outputs, long files, repeated reads, fan-out planning. Route bulk to subagents; keep summaries in the main thread, not raw payloads."
disable-model-invocation: true
---

# Guard the Context Window

**Why:** Context overflow degrades reasoning quality, creates compression artifacts, and halts progress.

**Pattern:**
- **Size phases and cap scope.** Limit files per phase, set turn budgets, account for mechanism costs.
- **Send bulk work to subagents.** Wide searches, long logs, large files, and long transcripts go to a subagent; keep only its summary in your own context.
- **Read the part of a file you need,** not the whole file, when you know where to look.
- **Do not read the same large output twice.** Save it to a file and search the file.
