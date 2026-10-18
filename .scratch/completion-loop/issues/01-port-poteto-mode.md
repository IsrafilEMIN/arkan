# 01: Port poteto-mode to all agents (drop cursor-only mechanics)

**What to build:** `~/.agents/skills/poteto-mode` works for every agent that reads `~/.agents/skills/` (claude code, codex, pi, omp). Replace the cursor-only mechanics with harness-neutral wording; keep the playbooks and the principles model intact. Nothing outside `~/.agents/skills/poteto-mode/` changes.

**Blocked by:** None (can start immediately).

- [ ] no cursor-only tokens remain: `grep -rEin 'subagent_type|run_in_background|grok|opus|xhigh|\.cursor' ~/.agents/skills/poteto-mode` returns no lines
- [ ] delegation is restated harness-neutral: "spawn a subagent", "run it in the background where the harness supports it" — the same wording style our other skills use
- [ ] model-routing lines are either generalized (role names, not vendor model ids) or dropped — one consistent choice, applied everywhere
- [ ] bundled scripts are ported, kept when already neutral, or dropped with a note naming each in the ticket comments
- [ ] every playbook still reads coherently after the replacement; no reference to a removed mechanic remains
- [ ] the skill stays user-invoked: `disable-model-invocation: true` and `allow_implicit_invocation: false` unchanged; `link-agents.sh --check` prints `ok`
- [ ] each behavior-changing adaptation is reported in this ticket's comments for maintainer confirmation before it lands
