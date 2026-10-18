# 27: review that converges

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 3

**What to build:** the review loop before the pr (the article's layer 1) cannot run forever or drown in noise. `code-review` finds, then verifies each finding (a separate pass tries to prove it wrong), tags each one `important` (blocks the pr), `nit` (optional) or `pre-existing` (was there before this diff; a ticket, not a block), with a `file:line`. given earlier findings, it reviews only the new diff and never repeats one. `arkan-mode` section 2 owns the round count: after round 3 it stops and asks the person to rethink the approach (and may start `retro`, ticket 22).

**Blocked by:** None (can start immediately).

- [x] `skills/code-review/SKILL.md` has find-then-verify, the three tags with `file:line`, and new-diff-only re-review
- [x] `arkan-mode` section 2 counts rounds and stops after 3
- [x] proof: a planted false finding is dropped by the verify pass; a fourth round does not start

## Comments

- 2026-10-18: resolved on branch `claude/ticket-27-review-converges`. `code-review` step 1 has a re-review rule: given an earlier report, it diffs from the commit that report names to `HEAD`, passes the earlier findings to each sub-agent, and never reports one again. both sub-agent briefs ask for a `file:line` on each finding. a new step 5 spawns one fresh sub-agent that tries to prove each finding wrong, drops the ones it disproves and the ones with no `file:line`, and tags the rest `important`, `nit` or `pre-existing` (checked against `git show <fixed-point>:<file>`). step 6 (was 5) prints one line per finding as `` `<tag>` `<file:line>`: <finding> ``, lists the dropped ones with a reason, counts each tag per axis, and names the reviewed commit for the next round. `arkan-mode` section 2: the `code-review` line counts rounds, ends the loop on a round with no `important` finding, and after round 3 stops, names the findings that keep coming back, asks the person to rethink the approach, and may start `retro` (or suggest it while `retro` is person-only; ticket 23).
- 2026-10-18, proof: a throwaway repo, `main` with `lists.py` (`avg` divides by `len(xs)`) and a spec ticket ("add `clamp` and `last`; `last([])` returns `None`"), and a `feature` branch. i followed the skill by hand, one round per commit, and checked each finding by running `python3`.
  - round 1, `git diff main...HEAD` at `6ca40a8` (adds `clamp` and `last` as `xs[len(xs)]`). find: three findings, one planted false: "`lists.py:6` `clamp` returns `lo` when `x > hi`". verify: `clamp(15,0,10)` = `10`, so it was dropped with that evidence. kept: `important` `lists.py:10` (`last([1,2])` raises `IndexError`; spec wants the last item, and `None` for `[]`), `pre-existing` `lists.py:2` (`avg([])` raises `ZeroDivisionError`; the line is the same in `git show main:lists.py`, so a ticket, not a block).
  - round 2, `git diff 6ca40a8..HEAD` at `70ec02a` (`last` now `xs[-1] if xs else 0`). the diff holds only `lists.py:10`, so `avg` was not seen and no earlier finding was repeated. kept: `important` `lists.py:10` (`last([])` returns `0`, spec says `None`).
  - round 3, `git diff 70ec02a..HEAD` at `aaf3ff8` (`last` now `xs[-1] if len(xs) > 1 else None`). kept: `important` `lists.py:10` (`last([7])` returns `None`).
  - round 3 still had an `important` finding, so by section 2 no fourth round started: the run stopped and named the repeat (`last` at `lists.py:10` in all three rounds) for the person to rethink.
  - limit: the same agent wrote the skill text, planted the false finding and the bugs, and ran both the find and the verify pass in one context, with no subagents. so the verify pass was not fresh and knew which finding was false; it rests only on running the code. a run in a fresh context is still worth doing.
