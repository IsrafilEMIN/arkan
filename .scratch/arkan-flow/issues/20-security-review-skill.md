# 20: security-review skill

**What to build:** an arkan `security-review` skill, copied from the prompt claude code publishes for its own `/security-review` (`.claude/commands/security-review.md` in <https://github.com/anthropics/claude-code-security-review>, mit license), so every harness gets the same security pass, not only claude code. it stays separate from `code-review` (owner's decision in ticket 03). in claude code the plugin install (ticket 04) keeps it from replacing the built-in.

**Blocked by:** None (can start immediately).

- [x] `skills/security-review/SKILL.md` is the prompt copied from a pinned commit of that repo; the sha is in the commit message and `NOTICE` holds its license
- [x] the claude-code-only parts are ported: the `!` lines that fill in git output become steps that run the same git commands, and `allowed-tools` becomes plain read-only rules
- [x] `README.md` lists it, and `arkan-mode` section 2 calls it in place of "the harness's own security review", with no bracketed ticket left on that line
- [x] proof: on a diff with a planted secret or an unchecked input, the skill reports it; on a clean diff it reports nothing

## Comments

- 2026-10-18, owner: copy claude code's published security-review prompt instead of writing one; no rename (ticket 17).
- 2026-10-18: resolved on branch `claude/security-review-20`. `skills/security-review/SKILL.md` is the prompt from upstream commit `0c6a49f1fa56a1d472575da86a94dbc1edb78eda`. the text from "Review the complete diff above" to the end is unchanged. the four `!` lines are now four steps that run the same git commands, with a note to use the merge branch when `origin/HEAD` is not set. `allowed-tools` is now three read-only rules: run only the five git commands it named, read and search but write nothing, and do each sub-task yourself when the harness has no subagents. `NOTICE` holds the mit license and its copyright line. `README.md` lists it. `arkan-mode` section 2 calls `security-review`, and the bracketed ticket ref on that line is gone.
- 2026-10-18, proof: a throwaway repo with a bare origin, so `origin/HEAD` is set, and two branches off `main`. on each, i ran the skill's four git steps and followed its phases by hand. that run had no subagents, so i did each sub-task in turn.
  - planted branch (`app.py` adds `STRIPE_SECRET_KEY = "sk_live_..."` and a `/user` route that adds `request.args["name"]` into sql with `+`): it reported two findings. vuln 1: sql injection at `app.py:21`, high, confidence 9. `name=' OR '1'='1` returns every row. fix: a `?` parameter. vuln 2: hardcoded secret at `app.py:6`, high, confidence 8. a live stripe key sits in source and in git history. fix: read it from the environment and rotate it.
  - clean branch (the same route with a `?` parameter, and the key read from `os.environ`): it reported no findings. one candidate was dropped at confidence 5: the route returns emails with no auth, but the app has no auth model, so there is no bypass to point at.
  - limit: the same agent planted the bugs and ran the review, so it knew what to look for. a run in a fresh context is still worth doing.
