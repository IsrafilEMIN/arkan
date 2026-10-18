# 20: security-review skill

**What to build:** an arkan `security-review` skill, separate from `code-review` (owner's decision in ticket 03). it runs in a fresh-context subagent on a diff that touches input, auth, secrets, ci or installers, and reports findings the way `code-review` does. `arkan-mode` section 2 then calls it in place of "the harness's own security review if it has one".

**Blocked by:** 17 (its name clashes with the harness's built-in `security-review` command)

- [ ] `skills/security-review/` exists and `README.md` lists it
- [ ] `arkan-mode` section 2 calls it, with no bracketed ticket left on that line
- [ ] proof: on a diff with a planted secret or an unchecked input, the skill reports it
