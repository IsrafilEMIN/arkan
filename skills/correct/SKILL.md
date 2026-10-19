---
name: correct
description: "Find the mistakes agents keep repeating in this repo and make each one impossible. Try architecture first, then types, then a lint whose error names the fix, then a test, and write docs last. Prove each check fails on a real past mistake. Use for /correct, or each time the person corrects an agent for something it did before."
disable-model-invocation: true
---

# Correct

The person keeps correcting agents in this repo for the same mistakes. Change the repo so the next agent can't make them. This is arkan-mode's rule "the user corrected you → make the mistake hard to repeat", run as a whole pass; `retro` covers the review-finding side of the same loop.

Assume every contributor is an agent that sees only the files it opened, copies the nearest example, and takes the shortest path that compiles. Design the repo so a change that looks right from one file is right for the whole repo.

## Find the mistake classes

Read recent commits, reverts, review comments (the ci reviewer's finding log, `ci/finding-report.sh`, where the repo runs it), closed tickets and their comments, the agent instruction files (`AGENTS.md`, `CLAUDE.md`), and comments that explain workarounds. Group the mistakes into classes. A class counts once it has happened twice.

## Fix each class at the highest level that works

1. **Eliminate it with architecture.** Give each piece of state one owner and each task one supported way. Hide internals so the wrong import fails. Replace hand-synced lists with one source of truth. Delete old ways and dead code an agent would copy.
2. **Enforce it with types,** so the bad state can't be written. If bad code still compiles, add a lint or ci check whose error names the file, type or function to use instead. If the pattern is already common, fail only when a change adds more.
3. **Test the behavior.** Fix or delete any test that still passes when the behavior it checks breaks, or that fails when only the internals change (`test-to-break`).
4. **Write docs or agent rules last,** only for judgment calls. Nothing fails when an agent skips them.

## Fix and prove

Fix the most frequent classes now, one commit each. Prove each new check fails on a real past mistake: plant it, show the failure, remove it. Run the same command locally and in ci (in arkan, add it to `scripts/check.sh`). Exceptions go on the offending line, with a reason, an expiry date, and the person's approval.

## Keep the rule table

Keep a table in the repo's agent instruction file that pairs each rule with what enforces it. When the person corrects you, fix the mistake and add the rule. If the rule was already there and nothing enforces it, that is a repeat: fix it at the highest level in the same change. Drop a rule once its mistake can't happen.

Ship it through the normal pull request flow; a change to `AGENTS.md` is on the sensitive-path list, so the person reviews it.

**Reply:** each class with its evidence, the level you picked, and why a higher level didn't work.
