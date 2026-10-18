# 20: security-review skill

**Role:** ready-for-agent
**Closed:** no
**Priority:** 1

**What to build:** an arkan `security-review` skill, copied from the prompt claude code publishes for its own `/security-review` (`.claude/commands/security-review.md` in <https://github.com/anthropics/claude-code-security-review>, mit license), so every harness gets the same security pass, not only claude code. it stays separate from `code-review` (owner's decision in ticket 03). in claude code the plugin install (ticket 04) keeps it from replacing the built-in.

**Blocked by:** None (can start immediately).

- [ ] `skills/security-review/SKILL.md` is the prompt copied from a pinned commit of that repo; the sha is in the commit message and `NOTICE` holds its license
- [ ] the claude-code-only parts are ported: the `!` lines that fill in git output become steps that run the same git commands, and `allowed-tools` becomes plain read-only rules
- [ ] `README.md` lists it, and `arkan-mode` section 2 calls it in place of "the harness's own security review", with no bracketed ticket left on that line
- [ ] proof: on a diff with a planted secret or an unchecked input, the skill reports it; on a clean diff it reports nothing

## Comments

- 2026-10-18, owner: copy claude code's published security-review prompt instead of writing one; no rename (ticket 17).
