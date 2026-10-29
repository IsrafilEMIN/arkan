### Pause safely

**You own a clean stop. Leave a checkpoint a cold-start agent can resume from.** This is explicit only. On "keep going", "going to bed, keep going", or "don't stop", do not pause.

1. Stop at a safe boundary. Finish the current atomic step or back out of it. Start nothing new, and cancel any nested subagents.
2. Take no irreversible action to pause. Open no PR to pause.
3. Make the work durable: a checkpoint is a commit plus its verified `broker push`. Commit uncommitted edits as one clear `wip:` commit on the current `agent/` branch and push it; the push must print `remote ref verified`. If the tree is broken, say so in the commit body in one line. An unpushed commit or an untracked file is not safe.
4. Write the resume note into that `wip:` commit's body, so it travels with the branch, and show it in the reply. Capture intent, what you were doing, progress and what's verified, current state, next steps, key files, and gotchas. Reference specs, commits and tickets by path or URL instead of copying them, and remove secrets. If a decision trail exists, point at it instead of duplicating it.

**Reply:** where you are in the loop, what's on disk versus still in your head (paths, no diff dumps), the commits you made and whether the tree is clean, and the first action on resume. This is a pause, not a final report.
