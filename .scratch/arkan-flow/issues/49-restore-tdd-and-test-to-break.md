# 49: restore tdd and test-to-break, keep the test principle skill

**Role:** ready-for-agent
**Closed:** no
**Priority:** 33
**Blocked by:** None — can start immediately.

**What to build:** recover the two skills that the test-principle change removed, and keep the new principle skill as the quality layer. The owner approved this shape on 2026-10-19.

- `skills/tdd/`: restore from `main`. Add pstack's guardrails: choose the narrowest executable check; run the new test before the fix and confirm it fails for the intended reason; prefer no new test over a bad test; skip when the path is expensive. It reads `test-to-break` as its policy, as before.
- `skills/test-to-break/`: restore from `main` unchanged. It is arkan's own seam policy: seam agreement, one positive end-to-end test per workflow, negative tests per decision node, delete overlap, restraint.
- `skills/principle-test-behavior-not-implementation/`: keep it as the quality rule. It is the source that `test-to-break`'s "each assertion" and `arkan-mode/principles/verification.md` point at.
- Rewire the workflow cites back to `tdd` in `arkan-mode/SKILL.md`, the bug-fix and spec playbooks, `architect`, `post-merge`, `README.md` and `eval/scenarios/ANSWERS.md`. Quality cites stay on the principle skill. Test-first ordering cites stay on `principles/verification.md`.

**Touches:** `skills/tdd/`, `skills/test-to-break/`, `skills/arkan-mode/`, `skills/architect/SKILL.md`, `skills/post-merge/SKILL.md`, `README.md`, `eval/scenarios/ANSWERS.md`, `.scratch/arkan-flow/issues/03-decide-core-skill-merges.md`.

- [ ] `tdd` and `test-to-break` exist again, and `tdd` names `test-to-break` as its policy.
- [ ] every workflow cite names `tdd`; every quality cite names `principle-test-behavior-not-implementation`.
- [ ] `bash scripts/check.sh` prints `check: ok`.
- [ ] the board is rebuilt and checked.

## Comments

- 2026-10-19, owner: approved the recovery proposal in session. two pull requests: this one restores the test area; ticket 50 makes the principles skills.
