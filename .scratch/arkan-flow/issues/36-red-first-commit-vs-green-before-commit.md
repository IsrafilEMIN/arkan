# 36: red-first commits clash with "checks green before each commit"

**Role:** needs-triage
**Closed:** yes
**Priority:** 20

**What to build:** a decision, then one line in the right place. the bug-fix playbook wants the failing test committed before the fix, as proof the test was red. many repos' `AGENTS.md` (the sandbox's among them) say the check must pass before each commit. a run meets both only by putting test and fix in one commit and quoting the red output instead. decide which wins, and say so where both rules meet (the playbook, or `pre-setup`'s `AGENTS.md` block).

**Blocked by:** None (can start immediately).

**Touches:** `skills/arkan-mode/playbooks/bug-fix.md`, `skills/tdd/`, `skills/pre-setup/`.

- [x] the owner picks: the repo's rule wins (one commit, red output quoted in the pr), or the playbook's (a red commit is allowed on a work branch)
- [x] the chosen rule is written where an agent meets the clash

## Comments

- 2026-10-18: found in ticket 19's bug run (sandbox pr #9): the run put test and fix in one commit because `AGENTS.md` wants `check.sh` green before each commit, and said so in its report.
- 2026-10-19: decision: a work branch may carry one red-first commit as evidence; the pr head must be green; ci and the merge gate check the head, not each commit. written in `skills/arkan-mode/playbooks/bug-fix.md` step 5, which also says never push a red head. swept the other texts that could be met as green before every commit: `skills/arkan-mode/SKILL.md` (the principle index no longer ties unit state to commit order), `skills/arkan-mode/playbooks/feature.md` (checks each unit, does not commit it), `skills/arkan-mode/playbooks/opening-a-pr.md` (the ordered sequence is landable, not each commit), and the root `AGENTS.md` (the board check is scoped to a commit under `.scratch/`). `skills/arkan-mode/playbooks/refactoring.md` says a behavior-preserving slice stays green, not a commit, so it stays as is. the `pre-setup` `AGENTS.md` block template has no commit or check rule, so there was no text to align there; the sandbox's own `AGENTS.md` carries that rule and is outside this repo. `eval/scenarios/**` untouched.
