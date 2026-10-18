---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Implement the work described by the user in the spec or tickets.

The issue tracker should have been provided to you. If not, tell the user to run `/pre-setup`.

If the user passes a ticket reference, fetch it from the issue tracker and state its title before starting. If the reference is ambiguous, ask. Claim it before any work (see **Claimed** in the `## Board` section of the issue tracker doc). Make every change to `TODO.md` in the ticket's branch, so it reaches `main` with the work.

Call the Skill tool with `tdd` where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, call the Skill tool with `code-review` to review the work. Fix all issues raised by the code review, then run the full test suite again.

Commit your work to the current branch.

Resolve each ticket the way the issue tracker closes work, then apply the board **Resolve** operation to its card.
