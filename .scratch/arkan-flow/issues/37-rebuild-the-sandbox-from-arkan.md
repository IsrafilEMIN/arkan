# 37: rebuild the scenario sandbox from arkan

**Role:** ready-for-agent
**Closed:** no
**Priority:** 21

**What to build:** `eval/scenarios/` can rebuild `IsrafilEMIN/arkan-sandbox` (or a fresh sandbox repo) from scratch: the `stock` project, its pre-setup files, the planted scenarios and history, `pre-break`, the two sandbox workflows, a fresh copy of arkan's skills in `.claude/skills/`, and arkan's `scripts/board.sh` in place of the sandbox's two board-script copies. today the sandbox exists only as built by hand in one session, and its skills go stale as arkan changes.

**Blocked by:** 04 (the install command gives the sandbox its skills).

**Touches:** `eval/scenarios/`.

- [x] one script builds the sandbox repo from `eval/scenarios/` and arkan's `skills/`, and leaves `ANSWERS.md` out of it
- [ ] a refresh mode updates only the sandbox's `.claude/skills/` from arkan, through a pr
- [x] the rebuilt sandbox runs `scripts/board.sh build` and `scripts/board.sh check` (one entry point, no `build-board.sh` or `check-board.sh`), and its `AGENTS.md` names that command
- [ ] proof: a rebuilt sandbox passes `check` on `pre-break` and fails it on `main`, and one scenario run scores the same as on the hand-built one

## Comments

2026-10-18: ticket `board` 04 replaced the two board scripts with one entry point, `scripts/board.sh build|check`. the rebuilt sandbox carries that command and the `AGENTS.md` line that names it; the hand-built sandbox still has the two old copies until this ticket lands.

2026-10-19: `eval/scenarios/build.sh` is the one build/refresh entry point. `build <destination>` imports `sandbox/history.bundle` (216,957 bytes; `main` 294acb1, `pre-break` af4922b), adds one rebuild commit to each branch, replaces `.claude/skills/` and the two old board scripts, updates the board paragraph in `AGENTS.md` and the tracker doc, regenerates `TODO.md` on both tips, and copies the two sandbox workflows plus the current `ci/github/arkan-review.yml` with `REVIEW_MODEL: claude-sonnet-5-5`. It refuses a nonempty destination or one inside the arkan checkout.

The bundle is the chosen seed. A `git fast-export` filtered to omit the stale `.claude/skills` trees is smaller (110,744 bytes raw, 28,097 gzip, against 216,957 for the bundle), but filtering changes every commit SHA. The post-merge scenario names `c4cf22f`, `2e31b63`, `3bee254`, `294acb1` and `6a31064`; the bundle keeps those exact, so it stays.

Proof on two fresh destinations: `main` e6e9d0f538172517eeff7be41f146ad89f33c879 and `pre-break` 3606b4a41e45a059955b6c000ff31d8e898224e7 both times, identical trees, clean worktrees. `pre-break` printed `ok` from `scripts/check.sh`; `main` exited 1 on `test_parses_one_decimal_place_as_tens_of_cents` (`5 != 50`). `scripts/board.sh check` printed `ok (14 cards)` on both. `diff -r skills <tip>/.claude/skills` is empty on both tips. `git log --all --format= --name-only | grep -x ANSWERS.md` is empty. `scripts/` at each tip holds only `board.sh`, `check.sh` and `style.py`.

`refresh <checkout> [base]` makes one `agent/refresh-skills-<arkan-sha>` branch in a temporary worktree, replaces only `.claude/skills/`, refuses any changed path outside that subtree, commits, and calls `agent-gh push` then `agent-gh pr-create`. Tested on a clone of the hand-built `pre-break` with a recording `agent-gh` stub: 177 changed paths, all under `.claude/skills/`, and the two broker calls carried the branch, head SHA, base and a body naming arkan `3f3549ffe229`. A no-op second run prints `refresh: skills already current` and leaves no branch. This is mechanics proof only; no live PR was opened.

Live gap: `IsrafilEMIN/arkan-sandbox` is not in the broker allow-list. Both parity runs stopped at `agent-gh push` with `refused: repo not in the broker allow-list: IsrafilEMIN/arkan-sandbox`; there is also no `GH_TOKEN` and `gh auth status` reports no login, so the note's REST route cannot open a PR either. The exact prerequisite for the two open boxes: add `IsrafilEMIN/arkan-sandbox` to the broker's `repos` allow-list (and its path/worktree roots if the broker needs them) or run unguarded with a GitHub write token, push a built sandbox to the public repo, then re-run one scenario against the public hand-built sandbox and the rebuilt one and score both against `ANSWERS.md`.

Parity run, `value-report 01`, headless omp `claude-sonnet-5-5`, local bare remotes, same note and prompt (/skill:arkan-mode do ticket value-report 01):
- hand-built `pre-break` (af4922b): commits 30d92ca test, a438939 fix, fc12214 close; `format_money` one-line `:02d` fix; `scripts/check.sh` ok (34 tests); old board scripts build/check ok; no push, no PR, broker refusal reported.
- rebuilt `pre-break` (3606b4a): commits 5b90508 failing test, c22c484 fix + CLI test + close; same one-line fix; `scripts/check.sh` ok (34 tests); `scripts/board.sh check` ok (14 cards); fresh-context review reported; no push, no PR, broker refusal reported.
- Same scenario-1 gates on both: repro `$3.5`, root cause `format_money` padding, failing test commit before the fix, minimal no-float fix, list/add/tablet named, failing-then-passing output. The push/claim, PR, CI and verifier gates did not run on either sandbox, so the full common sheet is not scored. Evidence: `/private/tmp/arkan-ticket37-evidence.*` (`original-final.log`, `rebuilt-final.log`, and the two branch bundles).
