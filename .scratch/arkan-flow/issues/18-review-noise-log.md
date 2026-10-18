# 18: log how each review finding ends

**What to build:** for each finding the reviewer posts, the repo keeps how it ended: fixed, wrong, intended, or did not matter. the owner can see the noise rate per repo and per tag, and a change to the reviewer is judged against it.

**Blocked by:** 03

- [ ] each finding's end state is recorded (the round marker from ticket 10 is the first place to try)
- [ ] a short report gives the noise rate per tag (`important`, `nit`, `pre-existing`)
- [ ] `learn` reads the report when it changes `REVIEW.md` or the reviewer prompt
