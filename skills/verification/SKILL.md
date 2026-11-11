---
name: verification
description: "Create or maintain a repo's own verify skill: a scripted way to launch the real app, drive it the way a user does, and capture proof, plus a feature map kept true as the app changes. Any language or platform. Create mode generates and proves the skill; maintain mode runs one read-only source reader per feature, one live session driving every feature, and at most one pull request of proven fixes. Use when a person says /verification, /create-verification, /maintain-verification, \"make a verify skill for this repo\", \"audit the verify skill\", or when arkan-mode reports that the repo has no verify skill."
disable-model-invocation: true
---

# Verification

A repo needs a scripted way to drive the real app and prove behavior: launch it, use a feature the way a user would, and capture evidence. arkan-mode's `shipping`, bug-fix and refactoring playbooks all reach for it as "the repo's verify skill". This skill writes that skill, tailored to the repo, and keeps it true afterwards. Write it for the next agent, not for a person: an agent reads it cold, mid-task, with no picture of the app.

A person starts this skill (arkan-mode tells them when a repo has none); an agent never starts it on its own.

## Mode

- **create**: the repo has no verify skill: no `verify-*` folder, and no other repo-local skill with launch and drive sections and a feature map. Generate one and prove it.
- **maintain**: such a skill exists. Bring it and its map back in line with the app. If there are several, ask which one.

Say which mode you are in before you start.

## Where the verify skill lives

`.agents/skills/verify-<app>/` in the repo, with `.claude/skills/verify-<app>` as a symlink to it, so every harness finds it.

If the sandbox refuses the write (some sandboxes deny writes under a project's `.agents/` and `.claude/`, so a session cannot plant a skill that later sessions load), write the files to `${TMPDIR:-/tmp}/<repo>-verify-<app>-draft/`, outside the repo, and give the person the exact `mv` and `ln -s` commands to run in a plain terminal. Prove the skill from the draft path; the move changes no content.

App behavior that is really broken is a product gap, in either mode: record it for the person and keep it out of the verify skill's pull request.

## Create

### 1. Interview the repo, not the person

Answer these from the code. Ask the person only what you cannot observe.

- **Surface:** what does a user touch? A web ui, a cli or tui, a desktop app, an api, a mobile app, a library? A repo can have several; pick the main one and note the rest.
- **Run:** how does the app start locally? Prefer the repo's own documented dev command (package scripts, Makefile, readme quickstart). Note ports, env vars, seed data, auth.
- **Drive:** how can an agent use it from a script? Existing harnesses first: Playwright or Cypress specs, expect scripts, pty helpers, curl-able endpoints, a debug port. Only then pick a generic recipe: a browser driven over cdp for web and Electron, a tmux or pty harness for cli and tui, plain http for services.
- **Observe:** what evidence can be captured? Screenshots, terminal transcripts, response bodies, logs, exit codes, database state.
- **Isolate:** can two instances run side by side (ports, data dirs, profiles)? If not, say so in the generated skill: refusing to drive a shared instance beats corrupting the person's session.

If the checkout does not build or start as it is, fix that first or report it exactly, before you generate anything: a skill written against a broken base teaches wrong steps. When an unrelated missing asset blocks startup (a static dir the api never serves, a sample config), the generated skill may create it, marked as verification scaffolding, and remove it in cleanup.

### 2. Generate the skill

Write `verify-<app>/SKILL.md` with front matter (`name: verify-<app>`, and a `description` that names the app, the surface, and when to reach for it; without front matter the skill never registers) and these sections, each grounded in what the interview found, with no placeholders left:

- **Launch:** the exact command that starts the app for verification, and how to tell it is ready (a log line, a prompt). Launch reaches a usable state from an empty data dir, migrations and seed data included. Ready means usable, not only that a process answers: a database health check can pass while its init scripts still run. Include teardown. A short-lived cli or tui has no server to keep alive: launch means build the binary (or install deps) once, then start each drive in its own isolated pty or tmux session.
- **Doctor:** one read-only check that answers "is this instance worth driving?": process up, right version, port owned by us, auth valid. An agent runs it first whenever anything looks off.
- **Drive:** the harness recipe with this repo's real selectors and commands, not examples. Prefer stable handles (aria labels, data attributes, prompt strings, route paths) over coordinates and tab order.
- **Evidence:** what to capture for a proof, and where it goes. Proof standards: use the real user path, not internal setters or test-only endpoints; capture the action and the state it leads to, not only the final screen; check side effects (files written, rows inserted, messages sent) beside what is visible; mock only where a production boundary already isolates the outside system. When the safe path is a dry run or test mode, observe what it really skips (files, network, git refs) instead of trusting its name.
- **Cleanup:** how to tear down what the run created. Never kill by process name; kill what you started. Cleanup removes instances and scratch state, never the evidence: proof survives the teardown, in a place the skill names.
- **Helpers:** any script the skill ships is executable, and the skill body shows how to call it. A helper the reader has to reverse-engineer is not a helper.

### 3. Seed the feature map

Create `verify-<app>/features/README.md` plus one file per user-facing feature you can find (start with the top 3 to 5, from routes, commands, menus or docs). Follow the shape in [`references/feature-map-example/`](references/feature-map-example/): a readme index and one file per feature. Each file answers, from the user's side: what the feature is, how to reach it, how to drive it with the harness, and what end state proves it works. The four `##` headings are `Sub-features`, `How to get to it (user POV)`, `Driving it with <harness>`, and `Gotchas`. If the seed data lacks something a journey needs, the journey reports a failure and the reason goes in that feature's `Gotchas`. Never weaken a journey to make it pass. The map is the repo's maintained verification source: a proof that drives one convenient entry point is incomplete when the map lists others.

### 4. Prove the generated skill before handing it over

Run its own instructions end to end once: launch, doctor, drive one mapped feature (one is enough; the map lets later runs cover the rest), capture evidence, clean up. After cleanup, check that the evidence still exists where the skill says: a cleanup that eats the proof fails this step. Fix what fails, and run the generated cleanup after every failed try too, so broken attempts leave no processes or ports behind. A generated skill that never ran is a draft, not a deliverable. If you proved it in a stand-in for the real target (a container instead of a fresh machine, a local stack instead of a remote one), list every setup step the stand-in did that the target will not; those stay unproven until a run on the real target covers them.

### 5. Ship it and hand over the upkeep

Commit the skill on a work branch and open a pull request the way `arkan-mode`'s `opening-a-pr` playbook says; the person decides when it merges. Then tell the person to run this skill again in maintain mode to keep the map true as the app changes. Suggest a cadence only if they ask.

## Maintain

A feature map rots as soon as the app changes. Maintain mode is the upkeep loop for the verify skill. The unit of rigor is the feature, not the sentence: cover every feature file from source and drive every feature live, without proving every bullet.

### Outcomes

Pick one, and say which:

- **clean**: every feature got source and live coverage; nothing worth shipping. No branch, no pull request.
- **changed**: one pull request ships proven doc, harness or map fixes.
- **blocked**: coverage could not finish, or a proven fix could not ship safely. Say exactly what blocked it.

### Edit scope

Edit only the verify skill's own folder (its `SKILL.md`, `features/`, and the harness scripts it owns). Never edit product code in a run: a behavior the map describes that the app no longer has is either doc drift (fix the map) or a product regression (report it; do not paper over it in docs).

### Pass

0. **Find the target.** The repo-local skill whose body has launch and drive sections and a feature map: usually `.agents/skills/verify-*/` (with a `.claude/skills/` link). Several → ask which; none → switch to create mode instead of inventing a target.

1. **Index hygiene.** Read the feature map's readme and list its sibling files. Fix missing, extra, duplicate or dead entries. Keep it light; no generated inventory.

2. **Source wave.** One read-only subagent per feature file, in a fresh context, run at the same time where the harness allows it. Each explains "how does this user-facing feature work?" from source, flags likely doc drift with `file:line` citations, and returns one short live-verification recipe. Subagents never drive the app and never edit files. Return shape: feature summary / source entry points / likely drift or none / one recipe.

3. **Reconcile.** Every feature file has a returned summary. Merge overlapping recipes into as few app states as you can. Spot-check cited drift; do not re-prove clean claims. Sweep recent changes (`git log` since the map's last update) for user-facing surfaces missing from the map: call one missing only with a concrete source path.

4. **Live pass.** Required even when the source looks clean. You alone drive, following the verify skill's own launch model: one long-lived instance driven one step at a time for servers and uis, or a fresh isolated session per drive for short-lived clis (the skill's Launch section decides). Drive every feature at least once, and keep three rules the whole pass, whatever fails:
   1. Never drive an instance you have not health-checked since it last did something surprising: doctor before the first drive, on each fresh session, and again after any failed drive. Where doctor cannot see the failure (a stuck ui on a healthy process), reset to a known state or relaunch.
   2. Evidence captured so far survives every cleanup; check it at its named place, do not assume.
   3. Nothing a drive started outlives its use. Clean the leftovers of a failed try whether the session is stuck, exited or shared (for a shared instance, clean the leftovers, not the instance).

   A doctor failure caused by skill drift is drift: fix it within the edit scope and retry once (restart only what the fix invalidated) before calling the pass `blocked`. A feature that cannot be reached is `verified-unreachable` only with the concrete prerequisite (auth, entitlement, os, outside state) and the route you tried; if the map omits that prerequisite, that is drift. Any harness fix gets driven live again before it ships. Final teardown comes after the last drive of the run, re-proofs included; evidence stays.

5. **Triage.** Wrong or missing user-side description → doc drift, fix it. Working behavior the harness cannot drive → harness gap, fix it (scripts executable, how to call them written in the skill body). App behavior that is really broken → product gap: record it as above.

6. **Ship or stop.** For **changed**: one pull request of proven fixes, every changed file re-read first, opened per `arkan-mode`'s `opening-a-pr` playbook; the person decides when it merges. For **clean** or **blocked**: no pull request; report the outcome and the coverage honestly.

Keep short run notes (features covered, unreachable prerequisites, confirmed drift, outcome) in a scratch place; do not commit them.
