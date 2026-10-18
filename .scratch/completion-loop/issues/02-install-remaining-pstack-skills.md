# 02: Install the remaining pstack skills (later)

**What to build:** install the rest of the pstack skills from `pstack/skills/` into `~/.agents/skills/`, cursor parts ported like ticket 01. The remaining set:

`poteto-help`, `setup-pstack`, `figure-it-out`, `automate-me`, `reflect`, `correct`, `teach`, `sharpen`, `in-your-own-words`, `how`, `why`, `recall`, `ketchup`, `bro`, `blast-radius`, `architect`, `arena`, `swarm`, `interrogate`, `tdd`, `benchmark-checklist`, `no-comments`, `unslop`, `technical-writing`, `typescript-best-practices`, `show-me-your-work`, `create-verification-skill`, `maintain-verification-skill`, `make-bot-ui`.

**Blocked by:** `arkan-flow` 01 (was `completion-loop` 01, now superseded) — the port approach there defines how cursor-only parts are neutralized. the skill list may shrink after `arkan-flow` 03 (for example pstack `tdd`, see `arkan-flow` 17).

- [ ] every skill in the set is installed; any exclusion (for example a name conflict like `tdd`) is a maintainer decision recorded in the comments, nothing is silently skipped
- [ ] copies come from a pinned cursor/plugins commit; the sha is recorded in `LOGS.md`
- [ ] cursor-only references ported per ticket 01's approach
- [ ] `link-agents.sh --check` prints `ok`; `agents/openai.yaml` present with matching policy flags
- [ ] board + `LOGS.md` updated per change
