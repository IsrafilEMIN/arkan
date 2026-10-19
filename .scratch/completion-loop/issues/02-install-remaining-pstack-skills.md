# 02: Install the remaining pstack skills (later)

**Role:** needs-triage
**Closed:** no
**Priority:** 12

**What to build:** install the rest of the pstack skills from `pstack/skills/` into `~/.agents/skills/`, cursor parts ported like ticket 01. The remaining set:

`poteto-help`, `setup-pstack`, `figure-it-out`, `automate-me`, `reflect`, `correct`, `teach`, `sharpen`, `in-your-own-words`, `how`, `why`, `recall`, `ketchup`, `bro`, `blast-radius`, `architect`, `arena`, `swarm`, `interrogate`, `benchmark-checklist`, `no-comments`, `unslop`, `technical-writing`, `typescript-best-practices`, `show-me-your-work`, `create-verification-skill`, `maintain-verification-skill`, `make-bot-ui`.

**Blocked by:** `arkan-flow` 01 (was `completion-loop` 01, now superseded) — the port approach there defines how cursor-only parts are neutralized. `arkan-flow` 03 is closed: pstack `tdd` is left out (it clashes with the `tdd` skill arkan keeps), so it is not in the set above.

- [ ] every skill in the set is installed; any exclusion (for example a name conflict like `tdd`) is a maintainer decision recorded in the comments, nothing is silently skipped
- [ ] copies come from a pinned cursor/plugins commit; the sha is recorded in the commit message
- [ ] cursor-only references ported per ticket 01's approach
- [ ] `link-agents.sh --check` prints `ok`; `agents/openai.yaml` present with matching policy flags
- [ ] board updated per change

## Comments

- 2026-10-18: proposal, not yet decided: install only what the flow calls. first `create-verification-skill` and `maintain-verification-skill` (step 2 of the flow has nothing behind it without them; both write to `.cursor/skills/`, so they need the port), then maybe `unslop`, `blast-radius`, `interrogate`; the rest on a real need.
- 2026-10-19, owner: port every remaining pstack skill, adapted to arkan (not pointers). source: `cursor/plugins` at `d457567` (182f2ce is not fetchable by its short sha; pstack also has two newer skills, `create-formal-verification-skill` and `maintain-formal-verification-skill`).
- 2026-10-19, agent: batch 1 ported: `create-verification` and `maintain-verification`. changes from pstack: names drop `-skill` (arkan-mode already called them that); the verify skill lives in `.agents/skills/verify-<app>/` with a `.claude/skills/` link, and falls back to a `.scratch/` draft plus the person's `mv`/`ln` commands when underground's sandbox denies the write; shipping goes through arkan's `opening-a-pr` playbook and the repo's merge path (seam row 6); product gaps become tickets on the repo's tracker; cursor's `subagent_type`/model names removed.
- 2026-10-19, owner: drop `setup-pstack` and `poteto-help` (they overlap `pre-setup` and `arkan-mode`); port `typescript-best-practices`, `make-bot-ui`, `bro` and `automate-me`.
- 2026-10-19, agent: batch 2 ported (review and thinking): `blast-radius`, `interrogate`, `architect`, `arena`, `swarm`, `figure-it-out`, `benchmark-checklist`. changes from pstack: `poteto-mode` and its principle skills point at `arkan-mode` and `arkan-mode/principles/*.md`; cursor's `pstack-models.mdc` model table and task-tool flags are replaced by one rule (different model families where the harness lets you pick, else fresh-context subagents on the current model, said in the report); output folders use `.scratch/`; results flow into arkan's pr playbooks and the repo's tracker; the perf-issue and hillclimb playbooks arkan lacks are not referenced. all seven are agent-and-person skills (ticket 23 rule: needed mid-task), so `disable-model-invocation` is dropped, and arkan-mode's routing names when to reach for each.
