# 32: log how each review finding ends

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 6

**What to build:** for each finding the ci reviewer posts, the repo keeps how it ended: fixed, wrong, intended, or did not matter. the owner can see the noise rate per tag, and a change to the reviewer is judged against it. this was section 18 of `.scratch/review-ci/spec.md`.

**Blocked by:** 31

**Touches:** the workflow from ticket 30 in `ci/`, `skills/retro/`.

- [x] each finding's end state is recorded in the marker from ticket 31
- [x] a short report gives the noise rate per tag (`important`, `nit`, `pre-existing`)
- [x] `retro` reads the report when it proposes a change to the reviewer

## Comments

- 2026-10-18: built in `ci/github/arkan-review.yml`, `ci/finding-report.sh`, `ci/README.md` and one line in `skills/retro/SKILL.md`. the marker is now `findings=<id>:<tag>:<state>,...`; an old `<id>:<state>` marker is still read, with each tag taken from its finding line in the comment, and rewritten in the new form. end states: `fixed` (the model checked it is gone, as before), `wrong`, `intended`, `did-not-matter`. a person sets the last three with a comment line `arkan: <id> <state>`, in a pr comment or a reply to the finding's inline comment; it counts only from a non-bot whose repo permission is `write`, `maintain` or `admin` (`gh api repos/<repo>/collaborators/<login>/permission`), the latest command per id wins, and the model never changes a state a person set. a finding that is not `open` stops blocking. every run reads every comment, so a command applies on its own comment run or on any later run. the workflow now also runs on `issue_comment` (only on an open pr, only when the comment has `arkan:`) and on `pull_request_review_comment` (every one, since a skipped job would pass the check); a comment run calls no model, never starts a round, waits for the run in progress, and decides the check from the marker. an `issue_comment` run uses the default branch's copy of the file and its own check lands there, so it posts the `arkan-review` check run on the pr head (`checks: write`). only `github-actions[bot]` writes the marker, as before. `ci/finding-report.sh <owner/repo> [<since YYYY-MM-DD>]` reads the sticky comment of every pr, open and closed, through the rest api and prints per tag the count of each state, `closed-out` (not `open`) and `noise` = (`wrong` + `did-not-matter`) / `closed-out`. an earlier attempt's local commit was reused; that attempt's sandbox pr 22 had been merged into `ci-r32-base` at 2026-10-18T23:53:49Z by the owner account, not by this session, so the base was rebuilt (force-pushed) from `pre-break`.
- 2026-10-18, proof in `IsrafilEMIN/arkan-sandbox` on the sandbox's lighter model: pr https://github.com/IsrafilEMIN/arkan-sandbox/pull/23 from `ci-r32-proof` to `ci-r32-base` (`pre-break` plus this workflow, `auto-merge.yml` deleted). sticky comment https://github.com/IsrafilEMIN/arkan-sandbox/pull/23#issuecomment-6256773024.
  - round 1, `efe1603` (planted bug: `value_by_prefix_cents` sums `price_cents`; and `write_off` skips unknown skus, which the author meant): check run 117826580932 `failure`. marker `findings=3b1b8d32:important:open,8390537e:important:open blocking=3b1b8d32,8390537e`.
  - round 2, `dcc9645` (fixes the bug): check run 117826877040 `failure`, "0 new, 1 fixed". marker `findings=3b1b8d32:important:fixed,8390537e:important:open`.
  - the owner replied to the `8390537e` inline comment with `arkan: 8390537e intended` (https://github.com/IsrafilEMIN/arkan-sandbox/pull/23#discussion_r4310096271). that started run https://github.com/IsrafilEMIN/arkan-sandbox/actions/runs/39195161859 (`pull_request_review_comment`, review step skipped, no model call): check run 117876257203 `success` on `dcc9645`. the sticky comment now says "round 2 on `dcc9645`: pass: no blocking finding open" and the marker `findings=3b1b8d32:important:fixed,8390537e:important:intended`; the round did not change.
  - `ci/finding-report.sh IsrafilEMIN/arkan-sandbox` afterwards (pr 18 with ticket 31's old markers, pr 22, pr 23):

    ```
    arkan-review findings in IsrafilEMIN/arkan-sandbox: 3 prs with a review marker
    tag           open  fixed  wrong  intended  did-not-matter  closed-out  noise
    important        2      5      0         1               0           6     0%
    nit              0      0      0         0               0           0      -
    pre-existing     0      0      0         0               0           0      -
    all              2      5      0         1               0           6     0%
    ```
  - not run in ci: a top-level pr comment (`issue_comment`). github runs that event from the default branch's copy of the workflow, and the sandbox `main` has no `arkan-review.yml` and is protected, so the proof used an inline reply, which runs the pr's copy. the issue_comment path (its own check run posted on the head) was only syntax-checked, and the refusal of a command from someone without write access was not exercised: only the owner account was at hand. pr 23 is closed, unmerged; the owner can delete the branches `ci-r32-base` and `ci-r32-proof`.
