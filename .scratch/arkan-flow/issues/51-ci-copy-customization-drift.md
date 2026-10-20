# 51: A customized ci copy should not always read out of date

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 60

**Blocked by:** None (can start immediately).

**What to build:** `pre-setup`'s `check` compares each copied ci workflow file with arkan's copy using `cmp -s`. A repo that must customize a copy, such as the post-merge workflow (its check command and signal), then reads `out-of-date` on every re-run, and `apply` would overwrite the customization.

- [x] `check` tells a file that differs only where the repo must customize it from a file that missed an arkan update
- [x] a re-run on a repo with the documented customization prints `ok`, not `out-of-date`
- [x] a copy that really missed an arkan update still prints `out-of-date`, and `apply` updates it
- [x] proof: a scratch repo with the documented post-merge customization re-runs `ok`; a copy from an older arkan reads `out-of-date`

## Comments

- 2026-10-19, filed from ticket 21 review round 2. `skills/pre-setup/scripts/setup.sh:72` uses `cmp -s`, and the ticket 21 docs now ask a repo to set `CHECK_COMMAND` and `POST_MERGE_MODEL` in its copy, so this clashes.
- 2026-10-19, agent: `apply` now ends each copied ci file with a `# arkan-copy: <sha256>` line, and `check` compares three states. The body without the stamp equals arkan's file: `ok`. The body differs and the stamp equals arkan's current file: `ok ... customized`. The stamp does not match: `out-of-date`, so arkan's copy moved since the repo took it. An older copy with no stamp that differs stays `out-of-date`. `skills/pre-setup/SKILL.md` names the `ok customized` state.
- 2026-10-19, proof in a scratch arkan tree and repo: `apply ci-post-merge` printed `ok`; a second apply left the file byte-identical; editing `CHECK_COMMAND: make check` printed `ok ... customized`; appending a line to arkan's copy printed `out-of-date`; `apply` then printed `ok`; a copied file with a local edit and no stamp printed `out-of-date`. `scripts/check.sh` passes.
- 2026-10-20, review round 1 fix: the stamp line is found anywhere in the file, not only at the end. `body_hash` removes every `# arkan-copy:` line before hashing, and `stamp_of` reads the first one. A line or a blank line appended after the stamp now reads `ok customized`; before the fix both read `out-of-date`. `file_hash` falls back from `sha256sum` to `shasum` to `cksum`, and fails with a message when none exists, instead of returning an empty hash that read `ok`.
- 2026-10-20, proof after the fix: a fresh apply `ok`; a note appended after the stamp and a trailing blank line both `ok customized`; an arkan change `out-of-date`; `apply` then `ok`; a no-stamp copy of arkan's current file `ok`; the same file with a local edit `out-of-date`.
- 2026-10-20, review round 2: the `cksum` fallback printed `<crc> <bytes> <path>`, so its stamp never matched. It now prints the crc field only (`cksum "$1" | cut -d' ' -f1`), which matches the stamp pattern and keeps the path out of the file. `apply` captures the hash first and exits when it is empty, so a host with no hash tool no longer writes an empty stamp and reports `ok`.
