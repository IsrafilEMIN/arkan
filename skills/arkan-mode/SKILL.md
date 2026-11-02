---
name: arkan-mode
description: "the default way to do engineering work on one task: check that it is a task, pick a playbook, apply the principles, prove the result, and drive it to a merged change. use at the start of any non-trivial coding task (a ticket, a feature, a bug, a refactor, a question about the code, a long unattended run), when the user says arkan, /arkan-mode or 'do this properly', or when the user says 'diagnose' or 'debug this', or reports something broken, throwing, failing or slow."
---

# arkan mode

arkan mode is how you work on one task: pick a playbook, apply the principles that change your decisions, prove the result, and own the change until it merges.

other skills sit beside this file in the same skills folder (`../tdd/SKILL.md`, and so on). run or read a skill when a step names it; a `principle-*` leaf is read by path, not invoked.

## 0. check that the work is a task

a **task** is the smallest piece of work you can finish alone, from start to a checked pr that waits only on the person's merge approval, with no other decision from a person. a ticket is a task. a small, clear request is a task.

pick the mode from what you were given:

- one ticket, or a small, clear request → one task loop, from section 1 on.
- a spec with tickets → the spec playbook (`playbooks/spec.md`): one task loop per ready ticket, in parallel where the blocking edges allow, then one review and one pr.

arkan mode runs tasks only. the work before a task is **shaping**, and a person starts each shaping step:

- the idea or its words are still fuzzy → stop and tell the user to run `/grilling`.
- the work needs more than one pr or more than one session, and has no tickets yet → stop and tell the user to run `/to-spec`, then `/to-tickets`. if the destination itself is unclear, `/wayfinder`.

when you stop, say why the work is not a task yet, and which shaping step you recommend. a plain question about the code is a task: use the investigation playbook.

**the gate.** you may pick up a ticket on your own when its role is `ready-for-agent` and it is ready by the issue tracker doc's rule (on a `TODO.md` board: a `Todo` card tagged `#ready-for-agent`). for a spec, you may run every such ticket in parallel. a `ready-for-human` or `needs-info` ticket waits: name it in the reply and do not start it. if the person names one, say its role and ask before you start. the role comes from the person through `/triage`, or from `/to-tickets` after the person approves the breakdown. a spec has no role.

when the task is a ticket:

- the repo has no issue tracker set up (no `docs/agents/issue-tracker.md`) → tell the user to run `/pre-setup`.
- fetch the ticket from the issue tracker and state its title before you start. if the reference is ambiguous, ask.
- claim the ticket before any work: the **claim** operation in the [tickets playbook](playbooks/tickets.md).
- **a missing piece is a blocker, not a bug.** when code the ticket needs does not exist yet and belongs to another open ticket, do not build it and do not debug around it. stop, run **add blocker** with that ticket, then **release** (keep the branch), and report which piece is missing and which ticket owns it. commit that edit and the rebuilt board on your work branch; if you have none yet, open a small branch and PR for the edit alone (the board rule in `docs/agents/issue-tracker.md`). never commit it straight to `main`.

## 1. start every task like this

your first message on a task says, in your own words, the person's goal and the smallest change you expect to meet it. do not wait for confirmation. if the evidence rules out the change the person asked for, show it and stop. restate that goal in each subagent brief, and open each pr's `## Why` with it.

1. **match a playbook.** read the list in [playbooks](#playbooks). open the matched file and copy its steps into your todo list, word for word, before any other todo. if you skip a step, keep it in the list with `skip: <reason>`.
2. **name the data shape first.** before you write logic, write down the core types and how the data is read and changed. see `principle-model-the-domain` and `principle-type-system-discipline`.
3. **read the principles you will use.** each entry in [principles](#principles) names when it applies and the `principle-<title>` skill that holds its leaf. read that leaf in full (`../<skill>/SKILL.md`) before you apply it. in your reply, name each principle that changed a decision, and say which decision. cite only principles whose text you read in this session.
4. **work in small checked units.** each unit ends in a state you can check. do not start the next unit while the current one is red. run the type check and single test files often, and the full test suite once at the end. a unit that fails because a piece it needs is another open ticket's work is a missing blocker: stop the way step 0 says, instead of debugging.
5. **prove it.** check the real thing (run the feature, read the real value, run the test), not a proxy. "it compiles" is not proof.
6. **place the worktree.** work in a git worktree off the base branch, as a direct child of a dedicated worktree root, never inside the repo. if you do not know where the root goes, ask before you create it.

## 2. when to reach for another skill

each line names the skill to call today.

- a term or a domain rule is unclear inside the task → `grilling` with domain-modeling on. if the answer changes what to build, stop: the work is not a task (step 0).
- code crosses a function boundary → sketch the types and signatures with empty bodies before the code (the feature playbook).
- a behavior to build, or a bug with a cheap test path → `tdd`.
- something is broken, throwing, flaky or slow → the bug-fix playbook. a measured slowness with no functional bug → the perf issue playbook.
- a design question you can settle by running code → the prototype playbook.
- a diff is ready → `code-review` in a fresh context, before you open a pr. that is round 1. fix every `important` finding and the `nit`s worth fixing, and file each `pre-existing` one with the **create** operation, role `needs-triage`. run the full test suite again, then review again with the earlier report, so it reviews only the new diff. if a class of finding comes back in a second round, start `retro` (proposals only). a round with no `important` finding ends the loop. after round 3, do not start a fourth: stop, tell the person which findings keep coming back, ask them to rethink the approach, and start `retro` (proposals only), or suggest it if you cannot. these rounds are your own check; the verdicts that gate the merge come from the reviewer sessions in [`references/broker.md`](references/broker.md).
- a diff is ready and touches input, auth, secrets, ci or installers → `security-review` in a fresh context, before you open the pr.
- a pr to open → the opening-a-pr playbook. a pr to drive to merge → the babysit playbook, then the shipping playbook.
- push, pr, review records, ci logs, merge or cleanup → [the forge](#the-forge).
- a merged change broke something → fix forward or revert, whichever is safer faster, and tell the user. to find the bad merge and ticket the miss, a person starts `post-merge`.
- the user corrected you, or a session went badly → make the mistake hard to repeat: structure, then a type, then a lint rule, then a test, and a written rule only last. to turn lessons from one session into checks and skill edits, start `retro` (proposals only), or suggest it if you cannot. to sweep the repo for mistakes agents keep repeating and land a check for each, a person starts `correct`.
- any prose (replies, docs, pr bodies, commit messages) → the rules in [the reply](#the-reply), then `unslop`. a doc, readme or rfc → `technical-writing`. text that agents read (skills, `AGENTS.md`) → `writing-for-agents`.
- a repo has no scripted way to prove the app works → tell the user. a person starts `verification` (create); you do not.
- a step only the person can do (sign up, create a key, paste a secret into a dashboard, run a cutover they own) → do every step you can first, then hand them the rest as a script with `wizard`. the same holds for a HITL task ticket in `wayfinder`.
- concurrency, retries, a state machine, a parser or unsafe code where tests can't reach the case that breaks → tell the user. a person starts `formal-verification` (create), and its maintain mode after changes that skipped the check.
- a model check's result, or a bug to show as a path through states → a person starts `statechart`.
- you edit a `.ts` or `.tsx` file → `typescript-best-practices`.
- a design that is a one-way door (a public api, a data schema) → `architect`, which runs `arena`. the person asks to improve or audit the architecture of existing code → `architect`, which walks it for shallow modules first. a contested design, or a change on a sensitive path → `interrogate` before you ship.
- a small diff you don't trust, or a change that reaches past its diff → `blast-radius`.
- you are about to report a performance number → `benchmark-checklist`.
- "how does x work", or where code should live → `how`. why it is built that way → `why`. the person wants to really understand it → `teach`, which runs both.
- work that no playbook fits (a large migration, a multi-part change) → `figure-it-out`. wide parallel coverage → `swarm`.

more triggers:

- **a fork you are about to ask about.** if the answer is a fact you can see by running something (behavior, timing, layout, output, speed), it is not a question for the user. sketch it with the prototype playbook and let the result decide. ask only for a product or taste call that no experiment can settle, and give your recommended answer.
- **review bots and security bots.** they find real bugs and they also file noise. check each claim against the code. fix the real ones, and dismiss the rest with a concrete reason. never change code only to quiet a bot. classify each thread as fix, dismiss or ask with [`references/review-bot-triage.md`](references/review-bot-triage.md).
- **a broken skill in the middle of a task.** fix it in its own pr. do not block on it, and do not work around it in silence.
- **the person comes back.** they ask where things stand → `recall`, across recent chats or for what changed in this chat. the person starts it, as well as `bro` (say it simply), `automate-me` (their working style as a mode skill), `sharpen` (rewrite a prompt deeper, not bigger; it returns the prompt and does not do the task) and `arkan-help` (which skill or playbook fits; returns a prompt, does not do the work).
- **long or unattended work** ("going to bed", "run until done", "trust it when i'm back"). keep a decision trail with `show-me-your-work`: what you chose, why, and the evidence.

## the forge

github is the forge. every pr write goes through the `broker`, and [`references/broker.md`](references/broker.md) holds its commands, the role that may run each one, the merge rule, holds and attempts. read it before the first broker call of a session. if the broker is missing or refuses a call, stop and report its exact error. never fall back to `git push`, `gh pr create`, `gh pr merge`, a REST write or a built-in pr tool.

name every work branch `agent/<task>`: the broker refuses other names. run `broker sync` before work and before each push. read a pr with `broker pr-status` and its diff with local git (`git diff origin/<default>...<branch>`). `gh` is optional: use it only for reads, and only when it works in the session.

**a merged pr is not a finished task.** `broker merge` removes the local worktree and the local branch when the branch still points at the merged head, and prints a line for each. read those lines: a `kept` line or an error leaves cleanup to you, so report it. the broker cannot delete the remote branch, so report it as left over unless the repo deletes merged branches on its own (`git ls-remote --heads origin <branch>` prints nothing).

## autonomy

**do it.** reversible work goes ahead without asking: code, branches, prs, notes, scratch scripts. a wrong reversible choice costs less than a blocked agent. do the work, show the result, and say what the user can change.

**always stop and ask** before an action no one can undo, or one the person owns: force-push to a shared branch, deploy, delete data, send a message outside the project. a merge is not one of them: the broker's merge rule is the gate, so call `broker merge` once it can pass, and report a hold to the person.

**"keep going", "i'm going to bed", "run until done"** mean you do not stop at a checkpoint. use the autonomous-run playbook.

**no is a fine answer.** when asked if something is a good idea, give your real view. if it does not earn its place, say so and why. a recommendation is a judgment, not an agreement.

## subagents

- give bulk reading, wide searches and parallel work to subagents. keep summaries in your own context, not raw output. run them in the background where the harness supports it.
- point a subagent at files and skills by path. do not paste their content into the prompt.
- tell each subagent that writes code to read this file first, so it works the same way. this chat runs the playbook; never give the playbook itself to a subagent.
- match the model to the job, if the harness lets you pick: the strongest model for the hardest design and judgment, a fast model for small mechanical edits. a second opinion is the same prompt on a different model; when both agree, trust it more.
- you own every subagent's work. read its diff yourself, and write your own summary. a self-report is not proof.
- give new work to a fresh subagent with the full brief, every later instruction, and the last agent's report and branch. reuse a running subagent only when the work needs state that lives in it (its checkout, uncommitted changes, a running server).

## the reply

write the reply clean as you draft it. a cleanup pass after drafting does not remove bad patterns.

- lead with the result. then what you chose and why, then what is still open.
- short declarative sentences, one thought each. short is not a reason to drop a section the playbook's reply names.
- say who the change is for and what changes for them before you give implementation detail. then say what the next person who owns this code inherits.
- every claim carries its evidence or its label in the same sentence: a command and its output, a `file:line`, a link; else label it as inferred or a guess. never hand the user a check you could run.
- never make up a link, a citation or a test result. link only what you made or read in this session.

every playbook ends with a reply written this way, with the pr link in full.

## comments

comments follow the same rules as the reply. keep a comment only for a "why" that the code cannot show. a test or verify script gets no comments that narrate its steps; the assert message says what it checks. this holds for every file you write, and for every subagent's diff.

## principles

each entry names its `principle-<title>` skill. read that leaf in full before you use it. the entries are grouped by where the principle changes a decision.

**core**

- **laziness protocol** (`principle-laziness-protocol`). sizing a diff, or tempted to add a layer. make the smallest change that solves the problem.
- **subtract before you add** (`principle-subtract-before-you-add`). before an addition or a rewrite. remove dead code and extra checks first.
- **foundational thinking** (`principle-foundational-thinking`). before you write logic. get the data structures right, and do scaffold work first.
- **redesign from first principles** (`principle-redesign-from-first-principles`). a new requirement in an old design. design as if it was there from day one.
- **attack the premise** (`principle-attack-the-premise`). two fixes with the same premise failed. question the premise, not the fix.
- **minimize reader load** (`principle-minimize-reader-load`). code that is hard to follow. count layers and hidden state, and cut both.
- **experience first** (`principle-experience-first`). a product or scope trade-off. choose what the user feels over what is easy to build.
- **exhaust the design space** (`principle-exhaust-the-design-space`). a new design with no example in the code. build two or three options and compare.
- **build the lever** (`principle-build-the-lever`). any non-trivial work. write the script, codemod or check that does it or proves it.
- **outcome-oriented execution** (`principle-outcome-oriented-execution`). a planned rewrite or migration. aim for the end state, not smooth steps between.

**architecture**

- **model the domain** (`principle-model-the-domain`). stateful logic, or code with many branches. put the domain in a structure, not in scattered conditions.
- **boundary discipline** (`principle-boundary-discipline`). validation, error handling, adapters. check data where it enters, then trust the types.
- **type system discipline** (`principle-type-system-discipline`). designing types or signatures. make bad states impossible to write.
- **make operations idempotent** (`principle-make-operations-idempotent`). commands or loops that can crash and restart. the same end state after any number of runs.
- **migrate callers, then delete the old api** (`principle-migrate-callers-then-delete-legacy-apis`). a new internal api with old callers. move them all and delete the old one in one go.
- **separate before you serialize shared state** (`principle-separate-before-serializing-shared-state`). two actors may write the same thing. remove the sharing first.

**verification**

- **prove it works** (`principle-prove-it-works`). before you say done. check the real thing.
- **fix root causes** (`principle-fix-root-causes`). debugging. reproduce first, then ask "why" until you reach the cause.
- **sequence verifiable units** (`principle-sequence-verifiable-units`). multi-step work. each unit ends green before the next starts.
- **test behavior, not implementation** (`principle-test-behavior-not-implementation`). writing, changing or keeping a test. assert what the code's users can see.
- **explain the number** (`principle-explain-the-number`). before you measure, and before you trust, report or act on a number you measured. find what limits it, and rule out that it measured something other than the work you think.

**working with agents**

- **guard the context window** (`principle-guard-the-context-window`). large output, long files, wide searches. send bulk to subagents.
- **never block on the human** (`principle-never-block-on-the-human`). tempted to ask "should i do x?" on reversible work. do it and show it.
- **encode lessons in structure** (`principle-encode-lessons-in-structure`). you write the same instruction twice. make it a lint, type or check.

## playbooks

open the file at `playbooks/<file>`. where a step names a tool your harness does not have, do what the step means with the tools you have, and say so in the reply.

- **investigation** (`investigation.md`). a read-only question: how does x work, why is y like this, should we do x or y.
- **bug fix** (`bug-fix.md`). a defect to reproduce, find the root cause of, and fix with evidence: feedback loop first, then minimise, hypotheses, instrumentation, a regression test at the right seam, and cleanup. [`scripts/hitl-loop.template.sh`](scripts/hitl-loop.template.sh) drives a person when the loop needs one.
- **perf issue** (`perf-issue.md`). a measured slowness to trace and improve against a baseline.
- **hillclimb** (`hillclimb.md`). steady improvement of one metric toward a target: one change, one measurement, keep or revert. a one-off slowness is a perf issue.
- **runtime forensics** (`runtime-forensics.md`). diagnose a runtime symptom (a leak, an idle cpu spin, a glitch) from live instrumentation. the deliverable is a diagnosis, not a fix.
- **trace forensics** (`trace-forensics.md`). diagnose a profiling artifact handed to you after the fact (a cpuprofile, a trace, a heap snapshot). the deliverable is a diagnosis, not a fix.
- **feature** (`feature.md`). new or changed behavior, built from a named data shape.
- **refactor** (`refactoring.md`). the structure changes, the behavior does not.
- **prototype** (`prototype.md`). throwaway code to make a design decision, or to settle a question by watching what happens.
- **visual parity** (`visual-parity.md`). two ui implementations must look the same, or a styling system migrates.
- **authoring a skill** (`authoring-a-skill.md`). writing or changing a `SKILL.md`.
- **eval** (`eval.md`). test how a skill, structure or prompt change affects agent behavior before you promote it.
- **autonomous run** (`autonomous-run.md`). a long task driven to a checkable end without stopping.
- **orchestrate** (`orchestrate.md`). a standing program handed to one coordinator: many days, many prs, many subagents. autonomous run drives one task to a predicate.
- **pause safely** (`pause-safely.md`). stop cleanly so a fresh agent can continue.
- **session pickup** (`session-pickup.md`). continue work another agent left.
- **worktree cleanup** (`worktree-cleanup.md`). reclaim local disk from merged or abandoned worktrees and old simulators, with [`scripts/worktree-audit.sh`](scripts/worktree-audit.sh).
- **opening a pr** (`opening-a-pr.md`). the end of every other code playbook.
- **babysit** (`babysit.md`). drive an open pr until it meets the broker's merge rule: conflicts, `block` reasons, ci.
- **shipping** (`shipping.md`). land a pr that a verifier, not its author, has run, through `broker merge`.
- **spec** (`spec.md`). a spec with tickets: one task loop per ready ticket on an integration branch, then one review and one pr.
- **tickets** (`tickets.md`). every ticket change: create, set role, add blocker, claim, release, close, reopen, resolve.
