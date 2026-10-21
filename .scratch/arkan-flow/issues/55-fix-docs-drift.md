# 55: fix the docs that no longer match the code

**Role:** ready-for-agent
**Closed:** no
**Priority:** 64
**Blocked by:** None (can start immediately).

**What to build:** the full review of both repos found docs in arkan that say something the code does not do. fix each doc so it matches the code. change no behavior here; a behavior fix gets its own ticket. underground's side is filed in underground (`docs-drift` 01).

- [ ] `docs/agents/issue-tracker.md:26-27` and `skills/pre-setup/references/issue-tracker-local.md:26-27` write the wayfinding fields as plain `Type:` and `Blocked by:`. `board.sh` reads only the bold `**Type:**` and `**Blocked by:**`, so a ticket that follows the example has no fields. show the bold form
- [ ] `eval/scenarios/README.md:30` says `sandbox/auto-merge.yml` counts a `PASS` from someone with write access. the fixture checks only the review's author association. say what the fixture checks
- [ ] `ci/README.md:57` says a tool call to an unknown tool stops the job. `ci/opencode_agent.py:1145-1153` returns an error to opencode go and lets it try again; only the codex and claude code paths stop. say what each path does
- [ ] `skills/freeze/SKILL.md:47` says the claude code adapter covers the shell as best effort. the shipped matcher is `Write|Edit`, and `adapters/README.md:45` says the shell is covered only when `Bash` is added. say the same in both files
- [ ] `skills/freeze/SKILL.md:48-49` says `/freeze <dir>` arms in omp and pi. `adapters/freeze.ts:67-75` needs `/freeze arm <dir>`. show the real command
- [ ] `skills/arkan-mode/agents/openai.yaml:3` says "from shaping to merge". `skills/arkan-mode/SKILL.md:21` says arkan-mode runs tasks only and a person starts shaping. make the short description match
- [ ] `bash scripts/check.sh` prints `check: ok`

## Comments

- 2026-10-21, owner: asked for one ticket per repo for the docs drift the review found.
- 2026-10-21, agent: `README.md:7` (it still says there is no install command) is left to ticket 07, which rewrites that section. the freeze adapter behavior itself (reads blocked in omp and pi, patch payloads unchecked, a file symlink not resolved) is a code fix, not docs, and is not in this ticket.
