# 55: fix the docs that no longer match the code

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 64
**Blocked by:** None (can start immediately).

**What to build:** the full review of both repos found docs in arkan that say something the code does not do. fix each doc so it matches the code. change no behavior here; a behavior fix gets its own ticket. underground's side is filed in underground (`docs-drift` 01).

- [x] `docs/agents/issue-tracker.md:26-27` and `skills/pre-setup/references/issue-tracker-local.md:26-27` write the wayfinding fields as plain `Type:` and `Blocked by:`. `board.sh` reads only the bold `**Type:**` and `**Blocked by:**`, so a ticket that follows the example has no fields. show the bold form
- [x] `eval/scenarios/README.md:30` says `sandbox/auto-merge.yml` counts a `PASS` from someone with write access. the fixture checks only the review's author association. say what the fixture checks
- [x] `ci/README.md:57` says a tool call to an unknown tool stops the job. `ci/opencode_agent.py:1145-1153` returns an error to opencode go and lets it try again; only the codex and claude code paths stop. say what each path does
- [x] `skills/freeze/SKILL.md:47` says the claude code adapter covers the shell as best effort. the shipped matcher is `Write|Edit`, and `adapters/README.md:45` says the shell is covered only when `Bash` is added. say the same in both files
- [x] `skills/freeze/SKILL.md:48-49` says `/freeze <dir>` arms in omp and pi. `adapters/freeze.ts:67-75` needs `/freeze arm <dir>`. show the real command
- [x] `skills/arkan-mode/agents/openai.yaml:3` says "from shaping to merge". `skills/arkan-mode/SKILL.md:21` says arkan-mode runs tasks only and a person starts shaping. make the short description match
- [x] `bash scripts/check.sh` prints `check: ok`

## Comments

- 2026-10-21, owner: asked for one ticket per repo for the docs drift the review found.
- 2026-10-21, agent: `README.md:7` (it still says there is no install command) is left to ticket 07, which rewrites that section. the freeze adapter behavior itself (reads blocked in omp and pi, patch payloads unchecked, a file symlink not resolved) is a code fix, not docs, and is not in this ticket.
- 2026-10-25, agent: fixed on `agent/ticket-55-docs-drift`; docs only, no behavior change. each box, before → after:
  - issue-tracker (both files, 26-27): before "A `Type:` line records the ticket type" and "a `Blocked by: NN, NN` line near the top." → after "A `**Type:**` line records the ticket type" and "a `**Blocked by:** NN, NN` line near the top. ... `board.sh` reads only the bold field names, so a plain `Type:` or `Blocked by:` line is not a field." proof, temp repo with one ticket each way, `board.sh build`: plain form → "needs a **Role:** line ... or a **Type:** line" and "needs a **Blocked by:** line", exit 1; bold form → "build-board: wrote TODO.md (1 cards)", exit 0.
  - `eval/scenarios/README.md:30`: before "a review on that same commit, from someone with write access, begins with `PASS`." → after "from an author association of `OWNER`, `MEMBER` or `COLLABORATOR`, begins with `PASS`. the fixture checks only that author association, not the reviewer's repo permission, so it does not prove write access." matches the `if:` of `sandbox/auto-merge.yml` (no permission api call in the file).
  - `ci/README.md:57`: before "..., a tool call to an unknown tool, ... stops the job" → after line 57 drops it, and a new line 58 says "from opencode go, the runner returns an `unknown tool` error to the model as the tool result and lets it try again in the next turn. from codex or claude code, the runner rejects the whole message as an invalid tool call and stops the job". proof, in memory with a fake chat: `_conversation` → tool message `{"error": "unknown tool"}`, then the next turn's answer `{'ok': 1}` is returned; `_native_message` → `RunnerError the native model returned an invalid tool call`.
  - `skills/freeze/SKILL.md:47`: before "the frontmatter `hooks` block in this file. ... | best-effort |" → after "the frontmatter `hooks` block in this file, matcher `Write\|Edit`. ... | no. only if you add `Bash` to the matcher; then best-effort |", the same as `adapters/README.md:45` ("only if you add `Bash` to the matcher; then best-effort") and the frontmatter `matcher: "Write|Edit"`.
  - `skills/freeze/SKILL.md:48-49`: before "`/freeze <dir>` in the session" → after "`/freeze arm <dir>` in the session", as `freeze.ts` parses `arm` then the dir ("usage: /freeze arm <dir>").
  - `skills/arkan-mode/agents/openai.yaml:3`: before "Do one engineering task properly, from shaping to merge" → after "Do one engineering task properly, through to merge".
  - `bash scripts/check.sh` → "check: ok".
