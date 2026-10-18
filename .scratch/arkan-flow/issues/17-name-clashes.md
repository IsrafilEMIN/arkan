# 17: no two skills or commands share a name

**Role:** ready-for-agent
**Closed:** no
**Priority:** 15

**What to build:** across all the harnesses a user has, no arkan skill shares a name with another skill or a built-in command, so the agent never picks the wrong one.

**Blocked by:** 04

proposal:

- `code-review` and `security-review` stay two skills (owner decision, ticket 03), so their clash with claude code's built-in `/code-review` and `/security-review` stays. needs a decision: prefix them (`arkan-code-review`, `arkan-security-review`), or keep the names and make sure the harness loads the arkan skill (check how each harness resolves a skill and a built-in with one name).
- pstack's `tdd` is not installed; `triage` stays matt's, and the after-merge skill is `post-merge`.
- add the `arkan-` prefix only where a clash with a harness's built-in command is left. no blanket prefix.
- `pre-setup` (machine scope) scans each chosen harness's skill folders and built-in commands, and reports each clash before it links anything.

- [ ] the owner accepts or changes the proposal
- [ ] after ticket 03, no name in `skills/` equals a built-in command of a supported harness
- [ ] pre-setup reports a planted clash in a test setup

## Comments

- 2026-10-18, owner: no rename and no `arkan-` prefix. what each harness does:
  - claude code: a plain skill replaces a built-in command of the same name (not its aliases); a plugin skill is named `<plugin>:<skill>`, so both stay. fix: install as a plugin (ticket 04).
  - codex: skills are called with `$name`, built-in commands with `/`, so they never clash. two skills with one name both load; a plain `$name` runs only when the name is unique.
  - pi: skills are called with `/skill:name`, so no clash with built-ins. two skills with one name: the first found wins, with a warning.
  - omp: skills are called with `/skill:name`. two skills with one name: the higher-ranked keeps the plain name, the other becomes `<namespace>/<name>`.
  left for this ticket: the scan that reports a skill-against-skill clash (pi drops one), in the machine-scope setup built with 04.
  sources read 2026-10-18: claude code <https://code.claude.com/docs/en/skills>; codex source `codex-rs/skills/src/` in <https://github.com/openai/codex> (its docs page was blocked from the cloud session); pi <https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/skills.md>; omp <https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md>.
