# Log

## 2026-10-16

- Pre-setup: ran `git init`, kept the existing `TODO.md` (Tern board), added `.gitignore`, `AGENTS.md`, `docs/agents/` and this change log.
- Added a `## Purpose` section to `AGENTS.md`: this repo enhances agent skills and ships them as one bundle named "arkan".
- Installed `poteto-mode` + 24 `principle-*` skills from cursor/plugins @ `182f2ce` into `~/.agents/skills/` (byte-identical upstream copies, content unmodified), linked them into `~/.claude/skills/` with `link-agents.sh`, and added their `agents/openai.yaml` per `symlink-first`.
- Created ticket 01 "Port poteto-mode to all agents" in `.scratch/completion-loop/issues/`; added its card to `TODO.md` (Todo).
- Created ticket 02 "Install the remaining pstack skills (on demand)"; card in `TODO.md` (Backlog, blocked by 01).
- Revised ticket 02 per review: covers the full remaining pstack set; name conflicts reported to the maintainer, not skipped.

## 2026-10-18

- Copied all 63 skills (216 files) from `~/.agents/skills/` into `skills/` in this repo; verified byte-identical with `diff -r`. Not pushed yet: the repo has no git remote and `gh` is not logged in.
- Board rule change (user decision): `TODO.md` is now tracked, and the copy on `main` is the only board. A card change goes in the same branch and PR as its work and reaches `main` only after the PR checks pass and the merge is verified. Claim no longer moves a card; the `Doing` lane is removed. Removed `TODO.md` from `.gitignore`; updated `AGENTS.md`, `docs/agents/issue-tracker.md`, `TODO.md`, and the `pre-setup`, `implement`, `implement-spec` and `wayfinder` skills in both `~/.agents/skills/` and `skills/` (verified identical with `diff -rq`).
- First commit on `main` with all local files; remote `origin` is `git@github.com:IsrafilEMIN/arkan.git`. The cloud branch `claude/project-thread-5b5zxa` (unrelated history, wip `arkan-mode` draft) is left as it is.
- Added `docs/review-gaps.md` (arkan against the claude code team's review article) and `docs/flow.md` (the flow node by node, risk-tiered merge, 16 openings with where each fix belongs). Updated `docs/core-skills.md`: `review`, `ship` and `learn` changed; `security-review` and `post-merge` added (`post-merge`, because `skills/triage` is matt's issue triage). Routed `arkan-mode` to the two new skills. Decision: reviewer eval cases live per repo in `.arkan/evals/review/`.
- Rebuilt the cloud branch `claude/lucid-sagan-xac36a` on `main`: it had started from the unrelated cloud history, so a pr from it would have deleted 230 files.
