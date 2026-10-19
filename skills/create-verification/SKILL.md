---
name: create-verification
description: "Generate a repo's own verify skill: a scripted way to launch the real app, drive it the way a user does, and capture proof. Any language or platform. Use when a person says /create-verification, \"make a verify skill for this repo\", or when pre-setup or arkan-mode reports that the repo has no verify skill."
disable-model-invocation: true
---

# Create a verification skill

A repo needs a scripted way to drive the real app and prove behavior: launch it, use a feature the way a user would, and capture evidence. arkan's verifier (the `shipping` playbook), the bug-fix and refactoring playbooks, and `maintain-verification` all reach for it as "the repo's verify skill". This skill writes that skill, tailored to the repo. Write it for the next agent, not for a person: an agent reads it cold, mid-task, with no picture of the app.

A person starts this skill (arkan-mode tells them when a repo has none); an agent never starts it on its own.

## Where the verify skill lives

`.agents/skills/verify-<app>/` in the repo, with `.claude/skills/verify-<app>` as a symlink to it (one copy, per `symlink-first`), so every harness finds it. `pre-setup`'s `verify` item looks for a `*verif*` folder in either place.

If the sandbox refuses the write (underground denies writes under a project's `.agents/` and `.claude/`, so a session cannot plant a skill that later sessions load), write the files to `.scratch/verify-<app>-draft/` instead and give the person the exact `mv` and `ln -s` commands to run in a plain terminal. Prove the skill from the draft path; the move changes no content.

## 1. Interview the repo, not the person

Answer these from the code. Ask the person only what you cannot observe.

- **Surface:** what does a user touch? A web ui, a cli or tui, a desktop app, an api, a mobile app, a library? A repo can have several; pick the main one and note the rest.
- **Run:** how does the app start locally? Prefer the repo's own documented dev command (package scripts, Makefile, readme quickstart). Note ports, env vars, seed data, auth.
- **Drive:** how can an agent use it from a script? Existing harnesses first: Playwright or Cypress specs, expect scripts, pty helpers, curl-able endpoints, a debug port. Only then pick a generic recipe: a browser driven over cdp for web and Electron, a tmux or pty harness for cli and tui, plain http for services.
- **Observe:** what evidence can be captured? Screenshots, terminal transcripts, response bodies, logs, exit codes, database state.
- **Isolate:** can two instances run side by side (ports, data dirs, profiles)? If not, say so in the generated skill: refusing to drive a shared instance beats corrupting the person's session.

If the checkout does not build or start as it is, fix that first or report it exactly, before you generate anything: a skill written against a broken base teaches wrong steps. When an unrelated missing asset blocks startup (a static dir the api never serves, a sample config), the generated skill may create it, marked as verification scaffolding, and remove it in cleanup.

## 2. Generate the skill

Write `verify-<app>/SKILL.md` with front matter (`name: verify-<app>`, and a `description` that names the app, the surface, and when to reach for it; without front matter the skill never registers) and these sections, each grounded in what the interview found, with no placeholders left:

- **Launch:** the exact command that starts the app for verification, and how to tell it is ready (a log line, a prompt). Launch reaches a usable state from an empty data dir, migrations and seed data included. Ready means usable, not only that a process answers: a database health check can pass while its init scripts still run. Include teardown. A short-lived cli or tui has no server to keep alive: launch means build the binary (or install deps) once, then start each drive in its own isolated pty or tmux session.
- **Doctor:** one read-only check that answers "is this instance worth driving?": process up, right version, port owned by us, auth valid. An agent runs it first whenever anything looks off.
- **Drive:** the harness recipe with this repo's real selectors and commands, not examples. Prefer stable handles (aria labels, data attributes, prompt strings, route paths) over coordinates and tab order.
- **Evidence:** what to capture for a proof, and where it goes. Proof standards: use the real user path, not internal setters or test-only endpoints; capture the action and the state it leads to, not only the final screen; check side effects (files written, rows inserted, messages sent) beside what is visible; mock only where a production boundary already isolates the outside system. When the safe path is a dry run or test mode, observe what it really skips (files, network, git refs) instead of trusting its name.
- **Cleanup:** how to tear down what the run created. Never kill by process name; kill what you started. Cleanup removes instances and scratch state, never the evidence: proof survives the teardown, in a place the skill names.
- **Helpers:** any script the skill ships is executable, and the skill body shows how to call it. A helper the reader has to reverse-engineer is not a helper.

## 3. Seed the feature map

Create `verify-<app>/features/README.md` plus one file per user-facing feature you can find (start with the top 3 to 5, from routes, commands, menus or docs). Follow the shape in [`references/feature-map-example/`](references/feature-map-example/): a readme index and one file per feature. Each file answers, from the user's side: what the feature is, how to reach it, how to drive it with the harness, and what end state proves it works. The four `##` headings are `Sub-features`, `How to get to it (user POV)`, `Driving it with <harness>`, and `Gotchas`. If the seed data lacks something a journey needs, the journey reports a failure and the reason goes in that feature's `Gotchas`. Never weaken a journey to make it pass. The map is the repo's maintained verification source: a proof that drives one convenient entry point is incomplete when the map lists others.

## 4. Prove the generated skill before handing it over

Run its own instructions end to end once: launch, doctor, drive one mapped feature (one is enough; the map lets later runs cover the rest), capture evidence, clean up. After cleanup, check that the evidence still exists where the skill says: a cleanup that eats the proof fails this step. Fix what fails, and run the generated cleanup after every failed try too, so broken attempts leave no processes or ports behind. A generated skill that never ran is a draft, not a deliverable. If you proved it in a stand-in for the real target (a container instead of a fresh machine, a local stack instead of a remote one), list every setup step the stand-in did that the target will not; those stay unproven until a run on the real target covers them.

## 5. Ship it and hand over the upkeep

Commit the skill on a work branch and open a pull request the way `arkan-mode`'s `opening-a-pr` playbook says; it lands through the repo's merge path (seam row 6: the gate on the person's `PASS`). Then point the person at `maintain-verification` for keeping the map true as the app changes. Suggest a cadence only if they ask.
