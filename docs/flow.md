# the arkan flow

status: draft, 2026-10-18. this file says how a change moves from a task to a merged and watched change, node by node. it also lists every known opening (a place where the flow can break, or where it needs something arkan does not own).

## words used here

- **skill.** one job, in one `SKILL.md` file. the agent calls it when the situation fits. example: `debug`.
- **playbook.** a fixed list of steps for one kind of task, in one file. pstack's 23 playbooks are in `skills/poteto-mode/playbooks/` (for example `bug-fix.md`, `feature.md`, `babysit.md`, `shipping.md`). the agent copies the steps into its todo list and does them in order. a playbook names which skill to call at which step. a skill is a tool; a playbook is the order you use the tools in for one task type. playbooks are per task type, and the same set works in every repo. the per-repo part is the verify skill that `create-verification` makes. when no playbook fits a task, pstack's `figure-it-out` writes a one-off playbook for it.
- **principle.** a short rule that changes a decision, such as "fix the root cause". there are 24. the upstream text is in the 24 `skills/principle-*` folders; `skills/arkan-mode/principles/` holds a shorter draft rewrite of them in 4 files.
- **gate.** a check that must pass before the change goes to the next node.
- **evidence.** output you can check: a command and what it printed, a `file:line`, a screenshot, a ci run link.

## the flow in one view

```
task
 │
 0  arkan-mode ── picks a playbook, applies the principles
 │
 1  grill ─────── only if the idea is fuzzy
 2  plan ──────── only if the work is too big for one pr
 │
 3  build + tdd ─ (4 debug, when something is broken)
 │
 5  prove ─────── tests, build, lint, the repo's verify skill
 │
 6  review + security-review, before the pr (fresh context)
 │
 7  ship ──────── opens the pr, pr body, risk tier
 │
 8  pr review ─── the same review skills, run by ci on each push
 │
 9  approval ──── set by risk tier: auto, one person, two people
 │
10  merge ─────── merge queue, then main
 │
11  post-merge ── watch, fix forward or revert
 │
12  learn ─────── turn the miss into a check, then back to 0
```

## the nodes

each node says what goes in, what the agent does, the gate, and what comes out.

### 0. arkan-mode (entry)

- **in:** a task from the user.
- **does:** matches a playbook (investigation, bug-fix, feature, refactor, prototype, autonomous-run, pause-and-resume, opening-a-pr). copies its steps into the todo list. reads the principles that apply.
- **gate:** a playbook is picked, or the task is a plain question.
- **out:** a todo list with every playbook step, and the next node.

### 1. grill (optional)

- **in:** an idea with unclear words or scope.
- **does:** asks a few numbered questions per round, each with a recommended answer. looks up facts in the code by itself and asks the user only for decisions. writes terms into `GLOSSARY.md` and hard choices into a short decision record (adr).
- **gate:** no open question is left that changes what to build.
- **out:** a clear description of the change.

### 2. plan (optional)

- **in:** work too big for one session or one pr.
- **does:** writes a spec, then splits it into thin tickets that each work end to end. each ticket lists the tickets it waits for.
- **gate:** each ticket can be built and checked by itself.
- **out:** files in `.arkan/plans/<feature>/`. each ticket goes through nodes 3 to 12 on its own.

### 3. build + tdd

- **in:** a ticket or a clear change.
- **does:** names the data shape first. sketches types and signatures with empty bodies, then fills them in. where a cheap test path exists, writes one failing test, then just enough code to pass it, and repeats.
- **gate:** each small unit is green before the next one starts.
- **out:** a diff, and tests that would fail if the behavior broke.

### 4. debug (when something is broken)

- **in:** a failure, a flaky test, or slow code.
- **does:** builds one fast command that fails on this bug. shrinks the repro. writes 3 to 5 guesses and tests each one. writes a regression test, fixes the root cause, removes debug logs.
- **gate:** the failing command now passes, and the regression test fails on the old code.
- **out:** back to node 3 or 5.

### 5. prove

- **in:** a diff.
- **does:** runs the repo's tests, build and lint. runs the repo's verify skill (made by `create-verification`) to use the real app the way a person does.
- **gate:** all of it passes, and the output is saved.
- **out:** evidence for the pr body.

### 6. review + security-review (before the pr)

- **in:** a proved diff.
- **does:** a subagent that did not write the code reviews it. finders look for bugs in parallel, then a verifier tries to prove each finding wrong. survivors get a tag: `important`, `nit`, or `pre-existing`, each with a `file:line`. `security-review` does the same for security only. `review` also reads `REVIEW.md` and sets the risk tier (see node 9).
- **gate:** no open `important` or security finding. at most 3 rounds, then step back and rethink the approach.
- **out:** a clean diff, a risk tier, and a short list of findings with how each one ended.

### 7. ship

- **in:** a clean diff and its risk tier.
- **does:** makes small ordered commits. opens the pr with a body that has: why, what changed, risk tier, how it was checked (with evidence), how to revert.
- **gate:** the pr exists and its body is complete.
- **out:** an open pr.

### 8. pr review (on every push)

- **in:** an open pr.
- **does:** ci runs the required checks (lint, types, tests, build) and the same `review` and `security-review` skills, outside the author's session. after the first round, review looks only at the new diff and never repeats a finding. `ship` answers every finding: fix it, or resolve it with a one-line reason.
- **gate:** ci is green, and no `important` or security finding is open.
- **out:** a pr ready for approval.

### 9. approval, scaled by risk

from the article. the change sets the tier, not the author.

- **low** (docs, copy, internal-only work, additive changes behind a flag): no person needed. it auto-merges once node 8 is green.
- **medium** (normal product code, and touchy areas such as caching, the updater, system prompts): one person approves.
- **high** (the riskiest code): two people approve.
- **always a person**, whatever the tier: any path the repo lists as sensitive, and any ci workflow file.

more rules from the article:

- a second check asks "does this change need a person even though its tier says no?". if yes, it goes up one tier.
- only trusted authors get the lighter tiers. others always need a person.
- an agent's approval never counts as a person's.
- the person who prompted an agent-written change counts as one of its reviewers, and owns it.
- an approval covers one commit. a new push needs a new approval.

- **gate:** the approvals the tier needs, on the current commit.
- **out:** a pr allowed to merge.

### 10. merge

- **in:** an approved pr.
- **does:** a merge queue runs the checks again on the latest main with the change applied, so two good prs cannot combine into a broken main. new behavior ships behind a flag where it can.
- **gate:** the queue run is green.
- **out:** the change is on main.

### 11. post-merge

- **in:** a merged change, and the repo's signals (ci on main, error logs, revert and incident reports).
- **does:** watches the change. if it broke something, fixes forward or reverts, whichever makes things safe faster. asks "which node should have caught this?". saves the bad diff and the confirmed bug as a case in `.arkan/evals/review/` in that repo.
- **gate:** main is healthy again.
- **out:** a miss, with the node that should have caught it, for `learn`.

### 12. learn

- **in:** a miss from `post-merge`, a user correction, or a finding that keeps coming back.
- **does:** makes the mistake hard to repeat. tries the strongest fix first: code structure, then a type, then a lint rule, then a test, and only last a line in `REVIEW.md` or `CLAUDE.md`. proves each new check fails on the real past mistake. when `review` changes, it runs the reviewer on all cases in `.arkan/evals/review/` and keeps the change only if the score did not drop.
- **gate:** the new check fails on the old mistake.
- **out:** a stronger repo for the next task at node 0.

two skills run at every node: `write` for all prose, and `handoff` when a session must stop before the work is done.

## openings

each opening says where the fix belongs:

- **arkan:** this repo.
- **per-repo setup:** files and ci jobs that arkan puts into each repo that uses it.
- **guard repo:** the other repo, which controls what agents may read, write and run.
- **repo host:** branch protection, merge queue, auto-merge, codeowners (github settings).

"how we know it works" says what proof would show the fix is real.

### the flow cannot run yet

1. **`arkan-mode` points to an empty playbook folder.** its step 1 opens `skills/arkan-mode/playbooks/<name>.md`, which does not exist. the 23 pstack playbooks are in `skills/poteto-mode/playbooks/`, and they still hold cursor-only parts (ticket 01). node 0 stops until `arkan-mode` points there, or the playbooks move. *where:* arkan. *how we know:* each playbook named in `arkan-mode` exists, and a test run picks the right one for a sample task.
2. **the arkan core skills are not merged yet.** the source skills are installed: matt's (`tdd`, `to-spec`, `to-tickets`, `implement`, `retro`, `handoff`, `grilling`, `pr`, ...) and pstack's `poteto-mode` plus 24 principles. 29 pstack skills are not installed yet, among them `create-verification-skill`, `maintain-verification-skill`, `interrogate`, `blast-radius`, `unslop`, `correct` and `reflect` (ticket 02, blocked by ticket 01). the merged arkan skills in `core-skills.md` (`review`, `ship`, `learn`, `security-review`, `post-merge`, ...) do not exist yet. *where:* arkan. *how we know:* each skill file exists and passes its own test case (opening 16).
3. **no install or update command.** a `pre-setup` skill exists (it sets up the issue tracker, labels, domain docs, the board and the change log in a repo), but nothing yet installs or updates the arkan skills into a repo's `.agents/skills/`. *where:* arkan. *how we know:* a clean repo gets every skill with one command, and running it twice changes nothing the second time.
4. **harnesses look in different places.** claude code reads `.claude/skills/` and `CLAUDE.md`, not `.agents/skills/` and `AGENTS.md` (as far as we know; check per harness). *where:* arkan, pre-setup. *how we know:* in each harness, a fresh session lists the arkan skills.

### gaps between nodes

5. **nothing starts `post-merge`.** a session ends at the merge, and a skill cannot wake itself. it needs a scheduled job or a ci job on main. *where:* per-repo setup. *how we know:* a planted bad merge in a test repo starts triage with no person in the loop.
6. **no runner for node 8.** the review skills run inside a session before the pr, but on the pr they must run in ci, outside the author's session. *where:* per-repo setup (a ci workflow that calls the skills). *how we know:* a push to a test pr gets review comments without any open session.
7. **the round count has nowhere to live.** a new session does not remember earlier rounds. *where:* arkan (store a marker in the pr, for example in the review summary comment). *how we know:* a fourth round on a test pr gets the "step back" message.
8. **the author picks its own tier.** if the agent that wrote the change also sets its risk tier, it can pick `low` and skip people. the tier must come from a check the author cannot change. *where:* per-repo setup (classifier in ci) plus guard repo (the author cannot edit that check). *how we know:* a test pr that touches a sensitive path but claims `low` still waits for a person.
9. **one list of sensitive paths.** arkan's `review` and the guard repo must read the same list. today nothing links them. *where:* guard repo owns the list; arkan reads it. *how we know:* adding a path to the list changes the tier of a test pr with no other edit.
10. **`REVIEW.md`, the eval cases and the ci workflows must be protected from the agent.** if the agent can edit the rules its reviewer follows, it can weaken the reviewer. *where:* guard repo. *how we know:* an agent's edit to these files is denied, or always needs a person.
11. **approvals per commit, auto-merge, merge queue, flags.** arkan uses them but cannot create them. *where:* repo host. *how we know:* a push after approval removes the approval; a `low` test pr merges by itself; a `medium` one does not.
12. **who starts `create-verification` and `REVIEW.md` in a new repo.** proposals: in the chat log of 2026-10-18 (recommended: `review` writes a seed on its first run, `learn` grows it). *where:* arkan. *how we know:* a new repo gets both after its first run through the flow.

### questions for the owner

13. **two people for `high`.** if you work alone, a `high` change can never get two approvals. options: a second person for those paths, or `high` means you plus a waiting period. *where:* your decision.
14. **name clashes.** the repo already has skills named `tdd`, `grilling`, `code-review` and `triage` (matt's issue triage; that is why the after-merge skill is called `post-merge`). claude code also has built-in `/code-review` and `/security-review` commands. two things with one name confuse the agent. *where:* arkan (see open question 1 in `sources.md`).
15. **noise is not measured.** nothing logs how each finding ended (fixed, wrong, intended, did not matter). *where:* arkan, inside `review`.

### arkan must prove itself

16. **arkan has no tests for its own skills.** we cannot tell if a skill change made things better or worse. a fix: a small test repo with planted problems (a bug, a security hole, a sensitive-path change, a style nit), and a script that runs the flow on it and checks each node's gate and output. *where:* arkan. *how we know:* the script fails when a skill is broken on purpose.
