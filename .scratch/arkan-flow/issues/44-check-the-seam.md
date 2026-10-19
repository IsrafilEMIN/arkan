# 44: check the seam in ci

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 23

**What to build:** `scripts/check-seam.sh`, run by `scripts/check.sh`, fails when arkan drifts from `docs/seam.md`: a skill or workflow names a broker verb that row 2 does not list, a shared string (row 6's agent mark or risk marker) differs between `docs/seam.md`, `ci/github/arkan-merge.yml` and `ci/github/arkan-risk.yml`, or a file outside `.scratch/` names a path inside underground. underground's adr 0002 promised this check on arkan's side.

**Blocked by:** None (can start immediately).

- [x] each kind of drift above fails `scripts/check.sh` with the file and the line
- [x] the check reads only arkan's own files
- [x] proof: one planted drift of each kind fails, and the clean tree prints `ok`

## Comments

- 2026-10-19, owner: agreed to keep the two repos on one seam (underground adr 0002, now six rows). this ticket is arkan's drift check for it.
- 2026-10-19, agent: `scripts/check-seam.sh`, run by `scripts/check.sh`. it checks that every `agent-gh <verb>` a tracked file names is in row 2's verb list (now written out in `docs/seam.md`), that both copies of `arkan-merge.yml` carry row 6's agent mark and read row 6's risk marker, that both copies of `arkan-risk.yml` write it, and that no tracked file outside `.scratch/` and `docs/seam.md` names a path inside underground. `docs/seam.md` gains `## Drift check`.
- 2026-10-19, proof: on the clean tree `check-seam: ok`. planted, one at a time, each failed with exit 1 and the file and line: `agent-gh pr-approve` in `skills/pr/SKILL.md` (`:172: agent-gh pr-approve is not a row 2 verb`); `AGENT_MARK` changed in `.github/workflows/arkan-merge.yml`; `head=` renamed in `ci/github/arkan-risk.yml`'s marker; `parts/gh-broker` in `ci/README.md` (`:137`). closed.
- 2026-10-19: pr 41's first `check` run failed: the check flagged its own patterns in `scripts/check-seam.sh` (`:12`, `:38`). the local proof missed it because the script was not yet tracked when it ran. the script now skips itself; run again with every file tracked: `check-seam: ok`, and a planted verb and path in `skills/pr/SKILL.md` still fail.
