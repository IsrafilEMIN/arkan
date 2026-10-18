# 36: red-first commits clash with "checks green before each commit"

**Role:** needs-triage
**Closed:** no
**Priority:** 20

**What to build:** a decision, then one line in the right place. the bug-fix playbook wants the failing test committed before the fix, as proof the test was red. many repos' `AGENTS.md` (the sandbox's among them) say the check must pass before each commit. a run meets both only by putting test and fix in one commit and quoting the red output instead. decide which wins, and say so where both rules meet (the playbook, or `pre-setup`'s `AGENTS.md` block).

**Blocked by:** None (can start immediately).

**Touches:** `skills/arkan-mode/playbooks/bug-fix.md`, `skills/tdd/`, `skills/pre-setup/`.

- [ ] the owner picks: the repo's rule wins (one commit, red output quoted in the pr), or the playbook's (a red commit is allowed on a work branch)
- [ ] the chosen rule is written where an agent meets the clash

## Comments

- 2026-10-18: found in ticket 19's bug run (sandbox pr #9): the run put test and fix in one commit because `AGENTS.md` wants `check.sh` green before each commit, and said so in its report.
