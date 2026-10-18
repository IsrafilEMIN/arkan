# 37: rebuild the scenario sandbox from arkan

**Role:** ready-for-agent
**Closed:** no
**Priority:** 21

**What to build:** `eval/scenarios/` can rebuild `IsrafilEMIN/arkan-sandbox` (or a fresh sandbox repo) from scratch: the `stock` project, its pre-setup files, the planted scenarios and history, `pre-break`, the two sandbox workflows, and a fresh copy of arkan's skills in `.claude/skills/`. today the sandbox exists only as built by hand in one session, and its skills go stale as arkan changes.

**Blocked by:** 04 (the install command gives the sandbox its skills).

**Touches:** `eval/scenarios/`.

- [ ] one script builds the sandbox repo from `eval/scenarios/` and arkan's `skills/`, and leaves `ANSWERS.md` out of it
- [ ] a refresh mode updates only the sandbox's `.claude/skills/` from arkan, through a pr
- [ ] proof: a rebuilt sandbox passes `check` on `pre-break` and fails it on `main`, and one scenario run scores the same as on the hand-built one
