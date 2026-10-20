# 01: check-seam fails on its own patterns

**Bug:** `scripts/check-seam.sh` searches every tracked file for seam patterns, itself included, so its own pattern lines match and the check fails on a clean tree.
**Path:** `scripts/check-seam.sh`
**Lines:** 10
**Bad PR:** none; a direct commit shipped it.
**Fix PR:** none, fixed by commit `5563418` (check-seam: skip its own file, whose patterns name what they look for)
**Broke main:** commit `c59d6c7` (ticket 44: check the seam in ci; defer the vote in 42); the first `check` run after it failed.
