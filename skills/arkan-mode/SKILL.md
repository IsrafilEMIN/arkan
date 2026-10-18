---
name: arkan-mode
description: "the default way to do engineering work: pick a playbook, apply the principles, prove the result. use at the start of any non-trivial coding task (a feature, a bug, a refactor, a question about the code, a long unattended run), or when the user says arkan, /arkan-mode or 'do this properly'."
---

# arkan mode

arkan mode is how you work on code. it does three things: it picks a playbook for the task, it applies the principles that change your decisions, and it makes you prove the result before you say "done".

other arkan skills sit beside this file in the same skills folder (`../grill/SKILL.md`, `../tdd/SKILL.md`, and so on). call them with the Skill tool when a step names them.

## start every task like this

1. **match a playbook.** read the list in [playbooks](#playbooks). open the matched file and copy its steps into your todo list, word for word, before any other todo. if you skip a step, keep it in the list with `skip: <reason>`.
2. **name the data shape first.** before you write logic, write down the core types and how the data is read and changed. see `principles/architecture.md`.
3. **read the principles you will use.** each entry in [principles](#principles) names when it applies. read the full text in `principles/` before you apply one. in your reply, name each principle that changed a decision, and say which decision.
4. **work in small checked units.** each unit ends in a state you can check. do not start the next unit while the current one is red.
5. **prove it.** check the real thing (run the feature, read the real value, run the test), not a proxy. "it compiles" is not proof.

## when to reach for another skill

- the idea is still fuzzy, or terms are unclear → the **grill** skill.
- the work needs more than one session, or more than one pr → the **plan** skill.
- code crosses a function boundary → the **build** skill (sketch the shape before the code).
- a behavior to build or a bug with a cheap test path → the **tdd** skill.
- something is broken, flaky or slow → the **debug** skill.
- a diff is ready → the **review** skill and the **security-review** skill, before you open a pr.
- a pr to open, or a pr to drive to green → the **ship** skill.
- a merged change broke something → the **triage** skill.
- the user corrected you, or a session went badly → the **learn** skill.
- any prose (replies, docs, pr bodies, commit messages, skills) → the **write** skill.

## autonomy

**do it.** reversible work goes ahead without asking: code, branches, draft prs, notes, scratch scripts. a wrong reversible choice costs less than a blocked agent. do the work, show the result, and say what the user can change.

**always stop and ask** before an action no one can undo: force-push to a shared branch, deploy, delete data, send a message outside the project.

**a fact is not a question for the user.** if you can find the answer by running something (behavior, timing, output, layout), run it. use the prototype playbook. ask the user only for a product or taste call that no experiment can settle. when you ask, give your recommended answer.

**"keep going", "i'm going to bed", "run until done"** mean you do not stop at a checkpoint. use the autonomous-run playbook.

**no is a fine answer.** when asked if something is a good idea, give your real view. if it does not earn its place, say so and why.

## subagents

- give bulk reading, wide searches and parallel work to subagents (the Agent tool). keep summaries in your own context, not raw output.
- point a subagent at files and skills by path. do not paste their content into the prompt.
- tell each subagent to read this file first, so it works the same way.
- you own every subagent's work. read its diff yourself, and write your own summary. a self-report is not proof.
- give new work to a fresh subagent with the full brief, every later instruction, and the last agent's report. reuse a running subagent only when the work needs state that lives in it (its checkout, a running server).

## the reply

write the reply with the **write** skill. in short:

- lead with the result. then what you chose and why, then what is still open.
- every claim carries its evidence in the same sentence: a command and its output, a `file:line`, a link. if you did not check it, label it as inferred or a guess.
- never make up a link, a citation or a test result.
- say who the change is for and what changes for them before you give implementation detail.

## principles

the full text is in `principles/`. one file per group.

**core** (`principles/core.md`)

- **laziness protocol.** sizing a diff, or tempted to add a layer. make the smallest change that solves the problem.
- **subtract before you add.** before an addition or a rewrite. remove dead code and extra checks first.
- **foundational thinking.** before you write logic. get the data structures right, and do scaffold work first.
- **redesign from first principles.** a new requirement in an old design. design as if it was there from day one.
- **attack the premise.** two fixes with the same premise failed. question the premise, not the fix.
- **minimize reader load.** code that is hard to follow. count layers and hidden state, and cut both.
- **experience first.** a product or scope trade-off. choose what the user feels over what is easy to build.
- **exhaust the design space.** a new design with no example in the code. build two or three options and compare.
- **build the lever.** any non-trivial work. write the script, codemod or check that does it or proves it.
- **outcome-oriented execution.** a planned rewrite or migration. aim for the end state, not smooth steps between.

**architecture** (`principles/architecture.md`)

- **model the domain.** stateful logic, or code with many branches. put the domain in a structure, not in scattered conditions.
- **boundary discipline.** validation, error handling, adapters. check data where it enters, then trust the types.
- **type system discipline.** designing types or signatures. make bad states impossible to write.
- **make operations idempotent.** commands or loops that can crash and restart. the same end state after any number of runs.
- **migrate callers, then delete the old api.** a new internal api with old callers. move them all and delete the old one in one go.
- **separate before you serialize shared state.** two actors may write the same thing. remove the sharing first.

**verification** (`principles/verification.md`)

- **prove it works.** before you say done. check the real thing.
- **fix root causes.** debugging. reproduce first, then ask "why" until you reach the cause.
- **sequence verifiable units.** multi-step work, and how you order commits. each unit ends green before the next starts.
- **test behavior, not implementation.** writing or keeping a test. assert the exact result a user sees.
- **explain the number.** before you trust a number you measured. find what limits it.

**working with agents** (`principles/agents.md`)

- **guard the context window.** large output, long files, wide searches. send bulk to subagents.
- **never block on the human.** tempted to ask "should i do x?" on reversible work. do it and show it.
- **encode lessons in structure.** you write the same instruction twice. make it a lint, type or check.

## playbooks

open the file at `playbooks/<name>.md`.

- **investigation.** a read-only question: how does x work, why is y like this, should we do x or y.
- **bug-fix.** a defect to reproduce, find the root cause of, and fix with evidence.
- **feature.** new or changed behavior, built from a named data shape.
- **refactor.** the structure changes, the behavior does not.
- **prototype.** throwaway code to make a design decision, or to settle a question by watching what happens.
- **autonomous-run.** a long task driven to a checkable end without stopping.
- **pause-and-resume.** stop cleanly so a fresh agent can continue, or pick up work another agent left.
- **opening-a-pr.** the end of every other code playbook.

a large or cross-cutting task (a migration across many files, work for more than one session) goes to the **plan** skill first, then back here for each ticket.
