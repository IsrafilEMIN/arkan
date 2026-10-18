# the arkan flow

status: draft, 2026-10-18. this file says how work moves from an idea to a task, and from a task to a merged and watched change, node by node. it also lists every known opening (a place where the flow can break, or where it needs something arkan does not own). each opening links to its ticket in `.scratch/arkan-flow/issues/`.

## words used here

the terms **task**, **shaping**, **spec**, **ticket**, **task loop**, **playbook** and **principle** are defined in [`GLOSSARY.md`](../GLOSSARY.md). more words:

- **skill.** one job, in one `SKILL.md` file. the agent calls it when the situation fits. example: `tdd`.
- **playbook file.** pstack's 23 playbooks are in `skills/poteto-mode/playbooks/` (for example `bug-fix.md`, `feature.md`, `babysit.md`, `shipping.md`). `skills/arkan-mode/playbooks/` links there until ticket 01 ports them. a skill is a tool; a playbook is the order you use the tools in for one kind of task. the same set works in every repo. the per-repo part is the verify skill that `create-verification` makes.
- **principles.** there are 24. the upstream text is in the 24 `skills/principle-*` folders; `skills/arkan-mode/principles/` holds a shorter rewrite of them in 4 files.
- **gate.** a check that must pass before the change goes to the next node.
- **evidence.** output you can check: a command and what it printed, a `file:line`, a screenshot, a ci run link.

## the flow in one view

```
idea
 │
 │   shaping: a person starts each step
 s1  grill ──────── only if the idea or its words are fuzzy
 s2  plan ───────── only if the work is more than one task:
 │                  to-spec, then to-tickets (wayfinder if the goal is unclear)
 │
═══ task ═══════════ the smallest piece an agent can finish alone
 │
 │   task loop: arkan-mode drives it, no person needed until approval
 0  arkan-mode ──── checks it is a task, picks a playbook, applies the principles
 │
 1  build + tdd ─── (2 debug, when something is broken)
 │
 3  prove ───────── tests, build, lint, the repo's verify skill
 │
 4  review + security-review, before the pr (fresh context)
 │
 5  ship ────────── opens the pr, pr body, risk tier
 │
 6  pr review ───── the same review skills, run by ci on each push
 │
 7  approval ────── set by risk tier: auto, one person, two people
 │
 8  merge ───────── merge queue, then main
 │
 9  post-merge ──── watch, fix forward or revert
 │
10  learn ───────── turn the miss into a check; a new task, or new shaping
```

the line marked **task** is the hand-off between people and agents. above it, a person decides what to build. below it, an agent closes the loop by itself, and a person comes back only at node 7 (approval) and when something cannot be undone.

## shaping (before the task)

### s1. grill (optional)

- **in:** an idea with unclear words or scope.
- **does:** `grill-with-docs` (it calls `grilling` and `domain-modeling`). asks a few numbered questions per round, each with a recommended answer. looks up facts in the code by itself and asks the person only for decisions. writes terms into `GLOSSARY.md` and hard choices into a short decision record (adr).
- **gate:** no open question is left that changes what to build.
- **out:** a clear description of the change. if it fits one task, go to node 0. else s2.

### s2. plan (optional)

- **in:** work that is more than one task.
- **does:** `to-spec` writes a spec. `to-tickets` splits it into thin tickets that each work end to end, and each ticket lists the tickets it waits for. when the destination itself is unclear, `wayfinder` maps it first.
- **gate:** each ticket is a task: an agent can build, check and merge it alone.
- **out:** tickets in the repo's issue tracker (set by `pre-setup`), with cards on the `TODO.md` board. each ticket goes through nodes 0 to 10 on its own.

## the task loop

each node says what goes in, what the agent does, the gate, and what comes out.

### 0. arkan-mode (entry)

- **in:** a task: a ticket, or a small clear request.
- **does:** checks that the work is a task; if it is not, stops and names the shaping step to run. matches a playbook (investigation, bug fix, feature, refactor, prototype, authoring a skill, autonomous run, pause safely, session pickup, opening a pr, babysit, shipping). copies its steps into the todo list. reads the principles that apply.
- **gate:** a playbook is picked, or the task is a plain question.
- **out:** a todo list with every playbook step, and the next node.

### 1. build + tdd

- **in:** a task.
- **does:** names the data shape first. sketches types and signatures with empty bodies, then fills them in. where a cheap test path exists, writes one failing test, then just enough code to pass it, and repeats.
- **gate:** each small unit is green before the next one starts.
- **out:** a diff, and tests that would fail if the behavior broke.

### 2. debug (when something is broken)

- **in:** a failure, a flaky test, or slow code.
- **does:** builds one fast command that fails on this bug. shrinks the repro. writes 3 to 5 guesses and tests each one. writes a regression test, fixes the root cause, removes debug logs.
- **gate:** the failing command now passes, and the regression test fails on the old code.
- **out:** back to node 1 or 3.

### 3. prove

- **in:** a diff.
- **does:** runs the repo's tests, build and lint. runs the repo's verify skill (made by `create-verification`) to use the real app the way a person does.
- **gate:** all of it passes, and the output is saved.
- **out:** evidence for the pr body.

### 4. review + security-review (before the pr)

- **in:** a proved diff.
- **does:** a subagent that did not write the code reviews it. finders look for bugs in parallel, then a verifier tries to prove each finding wrong. survivors get a tag: `important`, `nit`, or `pre-existing`, each with a `file:line`. `security-review` does the same for security only. `review` also reads `REVIEW.md` and proposes the risk tier (see node 7).
- **gate:** no open `important` or security finding. at most 3 rounds, then step back and rethink the approach.
- **out:** a clean diff, a proposed risk tier, and a short list of findings with how each one ended.

### 5. ship

- **in:** a clean diff and its proposed risk tier.
- **does:** makes small ordered commits. opens the pr with a body that has: why, what changed, risk tier, how it was checked (with evidence), how to revert.
- **gate:** the pr exists and its body is complete.
- **out:** an open pr.

### 6. pr review (on every push)

- **in:** an open pr.
- **does:** ci runs the required checks (lint, types, tests, build) and the same `review` and `security-review` skills, outside the author's session. ci also sets the final risk tier. after the first round, review looks only at the new diff and never repeats a finding. `ship` answers every finding: fix it, or resolve it with a one-line reason.
- **gate:** ci is green, and no `important` or security finding is open.
- **out:** a pr ready for approval.

### 7. approval, scaled by risk

from the article. the change sets the tier, not the author.

- **low** (docs, copy, internal-only work, additive changes behind a flag): no person needed. it auto-merges once node 6 is green.
- **medium** (normal product code, and touchy areas such as caching, the updater, system prompts): one person approves.
- **high** (the riskiest code): two people approve. a repo with one person sets its own rule for this (ticket 16).
- **always a person**, whatever the tier: any path on the repo's sensitive-path list, and any ci workflow file.

more rules from the article:

- a second check asks "does this change need a person even though its tier says no?". if yes, it goes up one tier.
- only trusted authors get the lighter tiers. others always need a person.
- an agent's approval never counts as a person's.
- the person who prompted an agent-written change counts as one of its reviewers, and owns it.
- an approval covers one commit. a new push needs a new approval.

- **gate:** the approvals the tier needs, on the current commit.
- **out:** a pr allowed to merge.

### 8. merge

- **in:** an approved pr.
- **does:** a merge queue runs the checks again on the latest main with the change applied, so two good prs cannot combine into a broken main. new behavior ships behind a flag where it can.
- **gate:** the queue run is green.
- **out:** the change is on main.

### 9. post-merge

- **in:** a merged change, and the repo's signals (ci on main, error logs, revert and incident reports).
- **does:** watches the change. if it broke something, fixes forward or reverts, whichever makes things safe faster. asks "which node should have caught this?". saves the bad diff and the confirmed bug as a case in `.arkan/evals/review/` in that repo.
- **gate:** main is healthy again.
- **out:** a miss, with the node that should have caught it, for `learn`.

### 10. learn

- **in:** a miss from `post-merge`, a user correction, or a finding that keeps coming back.
- **does:** makes the mistake hard to repeat. tries the strongest fix first: code structure, then a type, then a lint rule, then a test, and only last a line in `REVIEW.md` or `CLAUDE.md`. proves each new check fails on the real past mistake. when `review` changes, it runs the reviewer on all cases in `.arkan/evals/review/` and keeps the change only if the score did not drop.
- **gate:** the new check fails on the old mistake.
- **out:** a stronger repo. a fix that is one task goes back to node 0; a bigger one goes back to shaping.

two skills run at every node: `write` for all prose, and `handoff` when a session must stop before the work is done.

## openings

each opening says where the fix belongs:

- **arkan:** this repo.
- **per-repo setup:** files and ci jobs that arkan puts into each repo that uses it (through `pre-setup`).
- **guard repo:** the other repo, which controls what agents may read, write and run.
- **repo host:** branch protection, merge queue, auto-merge, codeowners (github settings).

"how we know it works" says what proof would show the fix is real. "ticket" names the file under `.scratch/arkan-flow/issues/`.

### the flow cannot run yet

1. **`arkan-mode` replaces `poteto-mode`, but the playbooks are still pstack's text.** `skills/arkan-mode/playbooks/` now links to `skills/poteto-mode/playbooks/`, so node 0 can open them, but they still hold cursor-only parts. *where:* arkan. *how we know:* `poteto-mode` is gone, every playbook `arkan-mode` names exists in its own folder, and no cursor-only part is left. *ticket:* 01.
2. **the arkan core skills are not merged yet, and it is open which ones need merging.** the source skills are installed: matt's (`tdd`, `to-spec`, `to-tickets`, `implement`, `retro`, `handoff`, `grilling`, `pr`, ...) and pstack's `poteto-mode` plus 24 principles. 29 pstack skills wait on `completion-loop` ticket 02. *where:* arkan. *how we know:* each skill that `arkan-mode` names exists and passes its scenario test (opening 16). *ticket:* 03.
3. **no install or update command.** nothing installs or updates the arkan skills into `~/.agents/skills/`, and the readme does not say to run `pre-setup` first. *where:* arkan. *how we know:* a clean machine gets every skill with one command, and running it twice changes nothing the second time. *tickets:* 04, 07.
4. **harnesses look in different places.** most harnesses read `~/.agents/skills/`; claude code reads `~/.claude/skills/` and `CLAUDE.md` (as far as we know; check per harness). `pre-setup` must ask which harnesses the user has and set each one up the way it expects. *where:* arkan, `pre-setup`. *how we know:* in each harness, a fresh session lists the arkan skills. *ticket:* 06.

### gaps between nodes

5. **nothing starts `post-merge`.** a session ends at the merge, and a skill cannot wake itself. it needs a ci job on main and a scheduled job. *where:* per-repo setup. *how we know:* a planted bad merge in a test repo starts triage with no person in the loop. *ticket:* 08.
6. **no runner for node 6.** before the pr, review runs inside the author's session. on the pr, something must start the review skills on each push, outside that session (a ci job). *where:* per-repo setup. *how we know:* a push to a test pr gets review comments without any open session. *ticket:* 09.
7. **the round count has nowhere to live.** a new session does not remember earlier rounds. proposal: one review comment on the pr that the reviewer edits in place, with a hidden marker that holds the round and the findings already posted. *where:* arkan. *how we know:* a fourth round on a test pr gets the "step back" message. *ticket:* 10.
8. **the author picks its own tier.** the tier must come from a check the author cannot change: fixed rules for critical paths, and a vote of model classifiers (not the author) for the rest, tested on an eval set. *where:* per-repo setup plus guard repo. *how we know:* a test pr that touches a sensitive path but claims `low` still waits for a person. *ticket:* 11.
9. **one list of sensitive paths.** arkan's `review` and the guard repo must read the same list. *where:* `pre-setup` writes it; the guard repo protects it. *how we know:* adding a path to the list changes the tier of a test pr with no other edit. *ticket:* 12.
10. **`REVIEW.md`, the eval cases and the ci workflows must be protected from the agent.** if the agent can edit the rules its reviewer follows, it can weaken the reviewer. *where:* `pre-setup` plus guard repo. *how we know:* an agent's edit to these files is denied, or always needs a person. *ticket:* 13.
11. **approvals per commit, auto-merge, merge queue, flags.** arkan uses them but cannot create them. `pre-setup` can check them and offer to turn them on. *where:* repo host, through `pre-setup`. *how we know:* a push after approval removes the approval; a `low` test pr merges by itself; a `medium` one does not. *ticket:* 14.
12. **who starts `create-verification` and `REVIEW.md`.** decided 2026-10-18: a person starts `create-verification`; `arkan-mode` only tells the user when a repo has no verify skill. `review` writes a seed `REVIEW.md` on its first run, and `learn` grows it. *where:* arkan. *ticket:* 15 (done).

### questions for the owner

13. **two people for `high`.** a repo with one person can never get two approvals. `pre-setup` asks how many people review, and records the rule for `high`. *where:* `pre-setup`. *ticket:* 16.
14. **name clashes.** the repo has skills named `tdd`, `grilling`, `code-review` and `triage`, and claude code has built-in `/code-review` and `/security-review`. two things with one name confuse the agent. *where:* arkan. *ticket:* 17.
15. **noise is not measured.** nothing logs how each finding ended (fixed, wrong, intended, did not matter). *where:* arkan, inside `review`. *ticket:* 18.

### arkan must prove itself

16. **arkan has no tests for its own skills.** the owner tests the flow on many real scenarios. *where:* arkan. *ticket:* 19.
