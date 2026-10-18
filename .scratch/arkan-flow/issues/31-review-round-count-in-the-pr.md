# 31: keep the review round count in the pull request

**Role:** ready-for-agent
**Closed:** no
**Priority:** 5

**What to build:** the ci reviewer knows which round it is on, which commit it last reviewed, and which findings it already posted, even in a fresh run. it keeps one review comment per pr and edits it in place; the comment holds a hidden marker, for example `<!-- arkan:code-review round=2 head=<sha> findings=<id>:<state>,... -->`. the round goes up only when the head commit changed. the next round reviews only `git diff <head>..<new head>`. a finding id comes from the bug class, the file and the symbol, not the line number, and a finding already in the marker is never posted again. on round 4 it posts "step back and rethink the approach", adds the label `arkan:rethink`, and stops reviewing until a person removes the label. this was section 10 of `.scratch/review-ci/spec.md`.

**Blocked by:** 30

**Touches:** the workflow from ticket 30 in `ci/`, `skills/code-review/`.

- [ ] the reviewer reads and writes the marker on each run
- [ ] re-review covers only the new diff, and a finding is never posted twice
- [ ] proof: a fourth push to a sandbox pr gets the "step back" message and the label
