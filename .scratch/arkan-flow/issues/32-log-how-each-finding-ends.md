# 32: log how each review finding ends

**Role:** ready-for-agent
**Closed:** no
**Priority:** 6

**What to build:** for each finding the ci reviewer posts, the repo keeps how it ended: fixed, wrong, intended, or did not matter. the owner can see the noise rate per tag, and a change to the reviewer is judged against it. this was section 18 of `.scratch/review-ci/spec.md`.

**Blocked by:** 31

**Touches:** the workflow from ticket 30 in `ci/`, `skills/retro/`.

- [ ] each finding's end state is recorded in the marker from ticket 31
- [ ] a short report gives the noise rate per tag (`important`, `nit`, `pre-existing`)
- [ ] `retro` reads the report when it proposes a change to the reviewer
