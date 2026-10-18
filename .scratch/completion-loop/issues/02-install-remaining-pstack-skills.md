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
