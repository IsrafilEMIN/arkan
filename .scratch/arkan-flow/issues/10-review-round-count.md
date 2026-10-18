# 10: store the review round count in the pr

**What to build:** the reviewer knows which round it is on, which commit it last reviewed, and which findings it already posted, even in a fresh session. on round 4 it stops and asks the author to step back.

**Blocked by:** 09

proposal: one review comment per pr that the reviewer edits in place (a "sticky" comment). it holds a hidden marker, for example:

`<!-- arkan-review round=2 head=<sha> findings=<id>:<state>,... -->`

- **round** goes up by one only when the head commit changed since the last review.
- **head** is the last reviewed commit; the next round reviews only `git diff <head>..<new head>`.
- **findings** holds an id per finding (from the bug class, the file and the symbol, not the line number, so a moved line keeps its id) and its state (open, fixed, dismissed). a finding whose id is already there is never posted again.
- on round 4: post the "step back and rethink the approach" message, add a label such as `arkan:rethink`, and stop reviewing until a person removes the label.

the same marker feeds the noise log (ticket 18). the pr is the only place that every session can read, so no extra store is needed.

- [ ] the reviewer reads and writes the marker on each run
- [ ] re-review covers only the new diff
- [ ] a finding is never posted twice
- [ ] proof: a fourth round on a test pr gets the "step back" message and the label
