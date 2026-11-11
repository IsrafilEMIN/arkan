### Pause safely

**You own a clean stop. Leave a checkpoint a cold-start agent can resume from.** This is explicit only. On "keep going", "going to bed, keep going", or "don't stop", do not pause.

1. Stop at a safe boundary. Finish the current atomic step or back out of it. Start nothing new, and cancel any nested subagents.
2. Take no irreversible action to pause. Open no PR to pause.
3. Write the resume note first. Capture intent, what you were doing, progress and what's verified, current state, next steps, key files, and gotchas. Reference specs, commits and tickets by path or URL instead of copying them, and remove secrets. If a decision trail exists, point at it instead of duplicating it.
4. Make the work durable: a checkpoint is a commit plus its verified `gh-broker push`. Make one `wip:` commit on the current branch with the resume note as its body: it holds any uncommitted edits, and on a clean tree it is an empty commit (`git commit --allow-empty`), so the note is still saved. If the tree is broken, say so in the first line of the body. Then push it; the push output must name the commit's sha and the branch, then `Done`. Show the note in the reply. An unpushed commit or an untracked file is not safe.

**Reply:** where you are in the loop, what's on disk versus still in your head (paths, no diff dumps), the commits you made and whether the tree is clean, and the first action on resume. This is a pause, not a final report.
