---
name: no-comments
description: "Spawn a comment-hating reviewer over a diff, delete the comments it convicts, fix the code it flags, and offer to encode the constraints a comment claims. Use for /no-comments or \"strip the comments from this\"."
disable-model-invocation: true
---

# No comments

arkan-mode's rule is that a comment stays only for a "why" the code cannot show. This skill enforces it on a diff: a fresh reviewer (Comment Sicko) hunts comments, you judge its report, and you fix what it convicts. Defer to its fresh view; overrule it only on the grounds in step 2.

A person starts this skill: it edits code.

## Scope

The files or diff the person names. Otherwise the current diff against the base branch (default `main`), including the working tree.

## Steps

1. **Spawn the reviewer.** One subagent in a fresh context, with [`references/comment-sicko.md`](references/comment-sicko.md) as its whole prompt, plus the scope. Do not restate its rules. It deletes comments in scope and reports; it writes no application code.
2. **Judge its report and its diff.** Reject application-code edits, edits outside the scope, deletions its own exceptions protect, `MUST KILL` reasons that misstate the code, and flags that treat intentional code we keep as guilty. Reshape flags on surprises in our own code stay actionable; do not restore those comments. A keep survives only with proof it is about something we cannot change. Audit lint and type-check suppressions in scope that it missed: suppressions guarding correctness or safety stay actionable `MUST KILL`s. Restore a deletion only with its exact exception and scoped proof. Before you accept a thin `IMPORTANT` or `do not remove` kill or keep, run `how` or `why` on its symbol. An ambiguous kill stays killed; a refuted or still-ambiguous keep is deleted. Revert and re-run one rejected report with the failure named. Reject a second, report it open, and stop.
3. **Fix the trivial flags** directly: delete a dead path, drop a parameter, use the real api. If any fix needs a new shape, run `architect` once for the accepted set and the code around it, and stop at the sketch; step 4 implements.
4. **Fix root causes in scope.** Make the smallest root-cause fix, and remove every named workaround. If the root cause is out of scope, land the smallest in-scope fix and report the rest open (or file it with the **create** operation in the [tickets playbook](../arkan-mode/playbooks/tickets.md), role `needs-triage`). **fix root causes** (`principle-fix-root-causes`) and **redesign from first principles** (`principle-redesign-from-first-principles`) guide intent only: neither lets you widen the scope or fix instances outside it. Never bolt on symptom guards. Run the repo's tests after the fixes.
5. **Constraint comments** ("do not remove", "do not change wording", "talk to X before changing"): leave keeps about things we cannot change. For the rest, offer the cheapest in-scope encoding (a type, a runtime check, a test, a ci lint), per **encode lessons in structure** (`principle-encode-lessons-in-structure`), and wait for the person's yes. In an unattended run, encode only what the person approved up front. If approved, encode, then delete the comment. Otherwise delete it, report the constraint open, and sketch the out-of-scope work.
6. **Report** the deletion count, restored comments, re-runs, the architect sketch, fixes, encoding offers, encodings made, constraints left unenforced, and other open work. Ship through the normal pull request flow.
