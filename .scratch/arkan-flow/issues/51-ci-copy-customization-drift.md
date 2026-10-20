# 51: A customized ci copy should not always read out of date

**Role:** ready-for-agent
**Closed:** no
**Priority:** 60

**Blocked by:** None (can start immediately).

**What to build:** `pre-setup`'s `check` compares each copied ci workflow file with arkan's copy using `cmp -s`. A repo that must customize a copy, such as the post-merge workflow (its check command and signal), then reads `out-of-date` on every re-run, and `apply` would overwrite the customization.

- [ ] `check` tells a file that differs only where the repo must customize it from a file that missed an arkan update
- [ ] a re-run on a repo with the documented customization prints `ok`, not `out-of-date`
- [ ] a copy that really missed an arkan update still prints `out-of-date`, and `apply` updates it
- [ ] proof: a scratch repo with the documented post-merge customization re-runs `ok`; a copy from an older arkan reads `out-of-date`

## Comments

- 2026-10-19, filed from ticket 21 review round 2. `skills/pre-setup/scripts/setup.sh:72` uses `cmp -s`, and the ticket 21 docs now ask a repo to set `CHECK_COMMAND` and `POST_MERGE_MODEL` in its copy, so this clashes.
