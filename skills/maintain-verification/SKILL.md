---
name: maintain-verification
description: "Periodic pass that keeps a repo's verify skill and its feature map true: one read-only source reader per feature, one live session driving every feature, at most one pull request of proven fixes. Use when a person says /maintain-verification or \"audit the verify skill\"."
disable-model-invocation: true
---

# Maintain a verification skill

A feature map rots as soon as the app changes. This skill is the upkeep loop for a verify skill made by `create-verification` (or any repo-local verify skill with a feature map). The unit of rigor is the feature, not the sentence: cover every feature file from source and drive every feature live, without proving every bullet.

A person starts this skill; an agent never starts it on its own.

## Outcomes

Pick one, and say which:

- **clean**: every feature got source and live coverage; nothing worth shipping. No branch, no pull request.
- **changed**: one pull request ships proven doc, harness or map fixes.
- **blocked**: coverage could not finish, or a proven fix could not ship safely. Say exactly what blocked it.

## Edit scope

Edit only the verify skill's own folder (its `SKILL.md`, `features/`, and the harness scripts it owns). Never edit product code in a run: a behavior the map describes that the app no longer has is either doc drift (fix the map) or a product regression (report it; do not paper over it in docs).

## Pass

0. **Find the target.** The repo-local skill whose body has launch and drive sections and a feature map: usually `.agents/skills/verify-*/` (with a `.claude/skills/` link). Several → ask which; none → stop and point at `create-verification` instead of inventing a target.

1. **Index hygiene.** Read the feature map's readme and list its sibling files. Fix missing, extra, duplicate or dead entries. Keep it light; no generated inventory.

2. **Source wave.** One read-only subagent per feature file, in a fresh context, run at the same time where the harness allows it. Each explains "how does this user-facing feature work?" from source, flags likely doc drift with `file:line` citations, and returns one short live-verification recipe. Subagents never drive the app and never edit files. Return shape: feature summary / source entry points / likely drift or none / one recipe.

3. **Reconcile.** Every feature file has a returned summary. Merge overlapping recipes into as few app states as you can. Spot-check cited drift; do not re-prove clean claims. Sweep recent changes (`git log` since the map's last update) for user-facing surfaces missing from the map: call one missing only with a concrete source path.

4. **Live pass.** Required even when the source looks clean. You alone drive, following the verify skill's own launch model: one long-lived instance driven one step at a time for servers and uis, or a fresh isolated session per drive for short-lived clis (the skill's Launch section decides). Drive every feature at least once, and keep three rules the whole pass, whatever fails:
   1. Never drive an instance you have not health-checked since it last did something surprising: doctor before the first drive, on each fresh session, and again after any failed drive. Where doctor cannot see the failure (a stuck ui on a healthy process), reset to a known state or relaunch.
   2. Evidence captured so far survives every cleanup; check it at its named place, do not assume.
   3. Nothing a drive started outlives its use. Clean the leftovers of a failed try whether the session is stuck, exited or shared (for a shared instance, clean the leftovers, not the instance).

   A doctor failure caused by skill drift is drift: fix it within the edit scope and retry once (restart only what the fix invalidated) before calling the pass `blocked`. A feature that cannot be reached is `verified-unreachable` only with the concrete prerequisite (auth, entitlement, os, outside state) and the route you tried; if the map omits that prerequisite, that is drift. Any harness fix gets driven live again before it ships. Final teardown comes after the last drive of the run, re-proofs included; evidence stays.

5. **Triage.** Wrong or missing user-side description → doc drift, fix it. Working behavior the harness cannot drive → harness gap, fix it (scripts executable, how to call them written in the skill body). App behavior that is really broken → product gap: record it for the person as a ticket on the repo's tracker (`docs/agents/issue-tracker.md`), and keep it out of this pull request.

6. **Ship or stop.** For **changed**: one pull request of proven fixes, every changed file re-read first, opened per `arkan-mode`'s `opening-a-pr` playbook; the person decides when it merges. For **clean** or **blocked**: no pull request; report the outcome and the coverage honestly.

Keep short run notes (features covered, unreachable prerequisites, confirmed drift, outcome) in a scratch place; do not commit them.
