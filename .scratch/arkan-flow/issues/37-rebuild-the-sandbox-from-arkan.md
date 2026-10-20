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

2026-10-19: `eval/scenarios/build.sh` is the one build/refresh entry point. `build <destination>` imports `sandbox/history.bundle` (216,957 bytes; `main` 294acb1, `pre-break` af4922b), adds one rebuild commit to each branch, replaces `.claude/skills/` and the two old board scripts, updates the board paragraph in `AGENTS.md` and the tracker doc, regenerates `TODO.md` on both tips, and copies the two sandbox workflows plus the current `ci/github/arkan-review.yml` with `REVIEW_MODEL: claude-sonnet-5-5`. It builds in a staging repo under the destination parent and moves it to `<destination>` only after the last gate passes, so a failed gate leaves no sandbox. It refuses a nonempty destination, one inside the arkan checkout, or a dirty `skills/`.

Skills come from `git archive HEAD skills`, not the working tree. Both build and refresh refuse a dirty `skills/`, so the arkan sha a refresh names is exactly the tree that ships. `scripts/board.sh` is a symlink to `../.claude/skills/pre-setup/scripts/board.sh`; `scripts/check.sh`, `AGENTS.md`, and `scripts/board.sh build|check` all work through it, and refresh keeps the target current because the symlink follows the skill tree.

The bundle is the chosen seed. A `git fast-export` filtered to omit the stale `.claude/skills` trees is smaller (110,744 bytes raw, 28,097 gzip, against 216,957 for the bundle), but filtering changes every commit SHA. The post-merge scenario names `c4cf22f`, `2e31b63`, `3bee254`, `294acb1` and `6a31064`; the bundle keeps those exact, so it stays.

Proof on two fresh destinations: `main` 6d869274b2972680a4fb344d1addbd093fa342ec (tree 3e3d24360bc8a5cd800a1497bf0e119dcfd51073), `pre-break` fa35f8e726a14f42ae7cca46c440aba86ec35d90 (tree a16059d1006ef2265c95ff95538a217e767cbecc), identical on both runs, clean worktrees. `pre-break` printed `ok` from `scripts/check.sh`; `main` exited 1 on `test_parses_one_decimal_place_as_tens_of_cents` (`5 != 50`). `scripts/board.sh check` printed `ok (14 cards)` on both tips; `scripts/board.sh build` then `check` on the destination printed `ok (14 cards)` and left `git status` clean. `diff -r <arkan HEAD:skills> <tip>/.claude/skills` is empty on both tips. `git log --all --format= --name-only | grep -x ANSWERS.md` is empty. `scripts/` at each tip holds only the `board.sh` symlink, `check.sh` and `style.py`.

A dirty `skills/` test: touching `skills/.dirty-proof` made `build` exit 2 with `skills/ has uncommitted changes; commit them first` and left the destination absent.

`refresh <checkout> [base]` fetches only `origin/<base>`, bases the branch on `refs/remotes/origin/<base>`, and makes one `agent/refresh-skills-<arkan-sha>` branch in a temporary worktree. It commits with the same pinned author/committer date as the build, replaces only `.claude/skills/`, refuses any changed path outside that subtree, and calls `agent-gh push` then `agent-gh pr-create`. A trap removes the temporary worktree, local branch and temp root until the push succeeds, so a retry starts clean; with the pinned date the retry makes the same commit.

Retry proof with a recording `agent-gh` stub whose first `push` refuses and whose second succeeds, on a clone of the hand-built `pre-break`: first run exit 2 with `refused: simulated push failure`, zero `agent/refresh-*` branches, one worktree (the target), zero temp refresh roots; second run created branch `agent/refresh-skills-3c315899b03f` at `4d77a6c78cd38a15b6cc0ae0410587200a1ca64a`, the same head SHA as the failed attempt's push, 177 changed files and zero outside `.claude/skills/`, then called `pr-create` for base `pre-break` and removed its worktree. A separate no-op run on a current-skills clone printed `refresh: skills already current at arkan 3c315899b03f4902e24fac1617f44e0d7aa33b7d` and left zero branches and one worktree. This is mechanics proof only; no live PR was opened.

Live gap: `IsrafilEMIN/arkan-sandbox` is not in the broker allow-list. Both parity runs stopped at `agent-gh push` with `refused: repo not in the broker allow-list: IsrafilEMIN/arkan-sandbox`; there is also no `GH_TOKEN` and `gh auth status` reports no login, so the note's REST route cannot open a PR either. The exact prerequisite for the two open boxes: add `IsrafilEMIN/arkan-sandbox` to the broker's `repos` allow-list (and its path/worktree roots if the broker needs them) or run unguarded with a GitHub write token, push a built sandbox to the public repo, then re-run one scenario against the public hand-built sandbox and the rebuilt one and score both against `ANSWERS.md`.

Parity run, `value-report 01`, headless omp `claude-sonnet-5-5`, local bare remotes, same note and prompt (/skill:arkan-mode do ticket value-report 01), on the rebuild before this revision (`pre-break` 3606b4a):
- hand-built `pre-break` (af4922b): commits 30d92ca test, a438939 fix, fc12214 close; `format_money` one-line `:02d` fix; `scripts/check.sh` ok (34 tests); old board scripts build/check ok; no push, no PR, broker refusal reported.
- rebuilt `pre-break` (3606b4a): commits 5b90508 failing test, c22c484 fix + CLI test + close; same one-line fix; `scripts/check.sh` ok (34 tests); `scripts/board.sh check` ok (14 cards); fresh-context review reported; no push, no PR, broker refusal reported.
- Same scenario-1 gates on both: repro `$3.5`, root cause `format_money` padding, failing test commit before the fix, minimal no-float fix, list/add/tablet named, failing-then-passing output. The push/claim, PR, CI and verifier gates did not run on either sandbox, so the full common sheet is not scored. This revision changes the board entry from a copy to a symlink and the build/refresh mechanics, not the stock code or skills; the new tips above re-pass the check and board gates. Evidence: `/private/tmp/arkan-ticket37-evidence.*` (`original-final.log`, `rebuilt-final.log`, and the two branch bundles).
