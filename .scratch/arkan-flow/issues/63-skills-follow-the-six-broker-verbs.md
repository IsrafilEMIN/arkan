# 63: skills and the seam follow the six broker verbs

**Role:** ready-for-agent
**Closed:** no
**Priority:** 71
**Blocked by:** None (can start immediately).

**What to build:** on 2026-10-26 underground cut the broker from ten verbs to six (underground PR 91, merge `fcbeba7`; ADR 0002 row 2). the verbs are now `push`, `pr-create`, `pr-status`, `pr-review`, `pr-merge`, `worktree-remove`. `pr-status` replaces `pr-view` and `pr-checks`: one json object with the pr fields, `reviewThreads`, `unresolvedReviewThreads`, and `checks` (`state`: `passed`, `pending`, `failed`, `unreadable` or `none`; `detail`), exit 0 when the pr was read. `pr-retarget`, `pr-reply`, `pr-diff` and the client's `raw` are gone; the broker answers them with `refused: unknown verb`. the installed broker already runs this build, so every arkan line that names a removed verb now fails on the broker route. arkan follows underground here (owner decision 2026-10-26), not the other way around.

replacements:
- read a pr: `agent-gh pr-status <owner/repo> <number>`; checks come from `checks.state`.
- read the diff: `git diff <baseRefOid>...<headRefOid>` in the working checkout, shas from `pr-status`. a sandboxed run cannot fetch, so when the base commit is not local, use `git diff <baseRefName>...<headRefOid>` against the local base branch (the three-dot form needs only the merge base). stop only when the head commit is not local.
- answer a review thread: in the next `pr-review` body, naming the thread's `path`, `line` and `commentId`.
- stacked prs: no retarget call. the broker merges with `--delete-branch`, and github moves each open child onto the merged pr's base ([pull request retargeting](https://github.blog/changelog/2020-05-19-pull-request-retargeting/)); read `baseRefName` back with `pr-status`.

omp only (owner decision 2026-10-26): underground drops the `claude` launcher and the broker's `claude/*` branches; it accepts `agent/*` heads only. seam row 1 names `omp-srt` alone.

- [ ] `docs/seam.md` row 2 says six verbs, and the `Row 2's verbs` line lists exactly `push`, `worktree-remove`, `pr-create`, `pr-status`, `pr-merge`, `pr-review`, with no `raw` transport
- [ ] `skills/arkan-mode/SKILL.md` **the forge**: the read, diff, thread and stack lines use the replacements above; the `refused: unknown verb` line names the removed calls
- [ ] `skills/arkan-mode/playbooks/shipping.md` steps 4 and 6 and `skills/arkan-mode/playbooks/opening-a-pr.md` **Size and stacks** name no removed verb
- [ ] `skills/recall/SKILL.md` step 5 names `agent-gh pr-status`
- [ ] `skills/why/SKILL.md` and `skills/arkan-mode/playbooks/babysit.md` step 8 name `agent-gh pr-status` and answer threads in a `pr-review` body
- [ ] `docs/seam.md` row 1 names `omp-srt` only, and no arkan file says the broker accepts `claude/*` branches
- [ ] `git grep -nE 'agent-gh (pr-view|pr-checks|pr-retarget|pr-reply|pr-diff|raw)'` outside `.scratch/` is empty
- [ ] `bash scripts/check-seam.sh` passes; `scripts/check.sh` prints `check: ok`
- [ ] after merge, `~/Developer/Projects/arkan-install` is updated to the merged `main`, and its local interim patch is gone

## Comments

- 2026-10-26, agent (underground session): the installed skills are symlinks: `~/.claude/skills/<name>` -> `~/.agents/skills/<name>` -> `~/Developer/Projects/arkan-install/skills/<name>`. `arkan-install` is a separate clone of this repo at `9c9917a`, 136 commits behind `main` at `eed7d53`, with one untracked file `skills/pre-setup/change-log.md`. the owner applied an interim local patch to the six skill files above in `arkan-install`, with the same text this ticket asks for. a `git pull` there conflicts with that patch: restore those files first (`git -C ~/Developer/Projects/arkan-install restore skills/`), then pull.
- 2026-10-26, agent (underground session): the broker's check read currently fails for every pr with `Resource not accessible by personal access token (HTTP 403)` on `commits/<sha>/check-runs`. fine-grained tokens cannot hold the Checks permission. `arkan-review` posts its verdict as a check run on the pr head (`ci/github/arkan-review.yml:309-313`), so a broker that reads only workflow runs would miss a red review. underground owns the fix; until it lands, `pr-status` reports `checks.state` `unreadable` and `pr-merge` refuses. this ticket does not depend on it.
- 2026-10-26, agent (underground session): this ticket was written from a local copy of `main` at `eed7d53`. if a ticket 63 already exists on the remote, renumber this one.
