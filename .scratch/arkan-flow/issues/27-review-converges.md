# 27: review that converges

**What to build:** the review loop before the pr (the article's layer 1) cannot run forever or drown in noise. `code-review` finds, then verifies each finding (a separate pass tries to prove it wrong), tags each one `important` (blocks the pr), `nit` (optional) or `pre-existing` (was there before this diff; a ticket, not a block), with a `file:line`. given earlier findings, it reviews only the new diff and never repeats one. `arkan-mode` section 2 owns the round count: after round 3 it stops and asks the person to rethink the approach (and may start `retro`, ticket 22).

**Blocked by:** None (can start immediately).

- [ ] `skills/code-review/SKILL.md` has find-then-verify, the three tags with `file:line`, and new-diff-only re-review
- [ ] `arkan-mode` section 2 counts rounds and stops after 3
- [ ] proof: a planted false finding is dropped by the verify pass; a fourth round does not start
