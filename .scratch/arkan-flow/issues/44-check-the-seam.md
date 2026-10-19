# 44: check the seam in ci

**Role:** ready-for-agent
**Closed:** no
**Priority:** 23

**What to build:** `scripts/check-seam.sh`, run by `scripts/check.sh`, fails when arkan drifts from `docs/seam.md`: a skill or workflow names a broker verb that row 2 does not list, a shared string (row 6's agent mark or risk marker) differs between `docs/seam.md`, `ci/github/arkan-merge.yml` and `ci/github/arkan-risk.yml`, or a file outside `.scratch/` names a path inside underground. underground's adr 0002 promised this check on arkan's side.

**Blocked by:** None (can start immediately).

- [ ] each kind of drift above fails `scripts/check.sh` with the file and the line
- [ ] the check reads only arkan's own files
- [ ] proof: one planted drift of each kind fails, and the clean tree prints `ok`

## Comments

- 2026-10-19, owner: agreed to keep the two repos on one seam (underground adr 0002, now six rows). this ticket is arkan's drift check for it.
