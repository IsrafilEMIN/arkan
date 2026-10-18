# 17: no two skills or commands share a name

**What to build:** across all the harnesses a user has, no arkan skill shares a name with another skill or a built-in command, so the agent never picks the wrong one.

**Blocked by:** 03

proposal:

- most clashes go away with ticket 03: `code-review` and `security-review` become one `arkan-review`; pstack's `tdd` is not installed; `triage` stays matt's, and the after-merge skill is `post-merge`.
- add the `arkan-` prefix only where a clash with a harness's built-in command is left. no blanket prefix.
- `pre-setup` (machine scope) scans each chosen harness's skill folders and built-in commands, and reports each clash before it links anything.

- [ ] the owner accepts or changes the proposal
- [ ] after ticket 03, no name in `skills/` equals a built-in command of a supported harness
- [ ] pre-setup reports a planted clash in a test setup
