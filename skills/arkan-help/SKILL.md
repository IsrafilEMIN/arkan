---
name: arkan-help
description: "Answer 'which skill, playbook or principle fits this?' and 'how do I set arkan up?': route the question, hand back a prompt the person can send, and link the file the answer came from. Use for /arkan-help with a question."
disable-model-invocation: true
---

# Arkan help

Answer the person's question about arkan, hand them a prompt they can send, and link the file the answer came from. For a help question, do not start the work. The person asked how, and an arkan run spends real tokens, so let them send the prompt.

A message that asks for work, such as "fix this bug the arkan way", is not a help question. Read [`arkan-mode`](../arkan-mode/SKILL.md) and do the work under it.

## Where the answers live

This file holds no skill table. The routing lives in the files below; read the one you route to before you quote it.

- [`arkan-mode`](../arkan-mode/SKILL.md) section 0: when work is a task, and which person-started shaping skill comes first when it is not.
- `arkan-mode` section 2: which skill to reach for in which situation, including the skills only the person starts.
- `arkan-mode`'s `## playbooks` list: each playbook in [`../arkan-mode/playbooks/`](../arkan-mode/playbooks/) and when it applies.
- `arkan-mode`'s `## principles` list: each `principle-*` skill and the decision it changes.
- Every other skill in this skills folder: the `description` in its frontmatter. A skill whose frontmatter sets `disable-model-invocation: true` is person-started: it stays out of the model's skill list, so the model never picks it on its own. It runs when the person types it. `arkan-mode` also reads `principle-*` skills by path.

To answer "which skill for X", match X against section 2 first, then against the descriptions. Link the file by its path in the arkan checkout, such as `skills/arkan-mode/playbooks/babysit.md`.

## Find out what they need

Infer the need from the message and the chat. A named situation, such as "which skill reviews a diff?", goes straight to its section. If the need is still unclear, ask one multiple-choice question with these options, then answer only the one they pick:

- Get set up
- Start a task with `/arkan-mode`
- Pick a skill, playbook or principle
- Fix a run that went wrong
- Make arkan my own

Check the repo state that changes the answer, and mention it only when it does:

- No `docs/agents/issue-tracker.md` means `pre-setup` has not run in this repo. Ticket work and the shaping skills need it.
- No `verify-*` skill in the repo means agents have no scripted way to drive the app. Mention `verification` (create) when the question is about proving a change works.
- No `formal-verify-*` skill in the repo means no property is checked past what tests reach. Mention `formal-verification` when the question is about a race, an invariant or another case tests rarely hit, and its maintain mode when the code it covers changed since it last passed.

## Get set up

Point at [`pre-setup`](../pre-setup/SKILL.md) and read it before you answer. It links the arkan skills into omp, sets up the repo's issue tracker, triage labels, domain docs and board, and hints at `verification` and `setup-pre-commit` when they are missing. It is safe to run again. For a harness other than omp, the person links or copies `skills/<name>` into that harness's skills folder.

Then start a real task with `/arkan-mode`, a goal, and a check that can pass or fail. Offer to word that first prompt with them, per [`references/prompting.md`](references/prompting.md).

If cost is the worry, say where the tokens go: subagents, review rounds and parallel workers (`arena`, `swarm`, `interrogate`). Where the harness lets the person pick models, a cheaper model for small mechanical work spends less. Save `/arkan-mode` for work that needs rigor.

## Start a task with `/arkan-mode`

`arkan-mode` checks that the work is a task, matches it to a playbook, copies the playbook's steps into the todo list and runs the other skills as the steps need them. A step it skips stays in the list as `skip: <reason>`. A good prompt states the goal and how to tell it is done. It does not list skills, because a hand-written sequence drops or reorders steps the playbook keeps. Read [`references/prompting.md`](references/prompting.md) before you help word one.

Work that is not a task yet goes to a shaping skill first, per `arkan-mode` section 0: `grilling` for a fuzzy idea, `to-spec` then `to-tickets` for work that spans more than one pr, `wayfinder` when the destination itself is unclear, `triage` to give a ticket its role. arkan has no separate planning skill; that is the shaping step.

Mid-chat, "new task" makes the mode match a fresh playbook.

## Pick a skill, playbook or principle

The default answer is `/arkan-mode`, which runs most of the others when its steps need them. Name a skill directly when the person wants more or less of something than the playbook gives, or when the skill is person-started. Read the skill before you recommend it, and give one example prompt.

Close calls the descriptions do not settle on their own:

- `how` explains what the code does. `why` explains the reasons. `teach` runs one or both and explains the result plainly.
- `arena` gives every worker the same brief and merges the best parts. `swarm` splits work into slices or a race and returns one report.
- `interrogate` attacks the diff. `blast-radius` looks for breakage outside the diff. `code-review` is the review loop every ready diff gets.
- `recall` rebuilds context across recent chats, or catches the person up on this chat. Continuing one specific branch another agent left is the session pickup playbook.
- `figure-it-out` designs one rigorous run that no playbook fits. The orchestrate playbook runs a program that spans days and many prs. The autonomous run playbook drives one task to a checkable end.
- `sharpen` returns a better prompt and does not do the task. `arkan-help` returns a prompt for the right skill and does not do the task either.

Playbooks are step lists inside `arkan-mode`, not skills, so they have no slash command. Inside `/arkan-mode`, describing the task picks one, and phrases name one directly: "babysit this pr" or "check on pr 123" runs babysit, which drives the pr until it meets the broker's merge rule; "land this pr" runs shipping, which merges it; "take over this branch" runs session pickup; "pause safely" runs pause safely; "run the eval playbook" runs eval.

Principles are one-rule skills that `arkan-mode` reads and cites in its replies. The person rarely invokes one. They steer with the names instead, as in "apply prove it works. show me the real output."

## Fix a run that went wrong

| Symptom | Fix |
|---|---|
| A question got treated as the next step of the last task | Say "new task", or say the turn does not need the mode. |
| A skill did not load on its own | Person-started skills (`disable-model-invocation: true`) stay out of the model's skill list: they run when the person types them, or, for `principle-*` skills, when `arkan-mode` reads them by path. Others load when `arkan-mode` reaches for them, and it does not run every skill. |
| Parallel agents overwrote each other | Give each agent its own worktree, as step 6 of `arkan-mode` section 1 says. |
| An unattended run moved but finished nothing | Give it a check that can pass or fail, not a duration. That is the autonomous run playbook. |
| The reply claims success from a green build | Ask for the real command, flow, stored value or profile. That is `principle-prove-it-works`. |
| Runs cost more than expected | See the cost paragraph under Get set up. |

For a run that drifts, [`references/prompting.md`](references/prompting.md) has one-line steers.

## Make arkan my own

- [`automate-me`](../automate-me/SKILL.md) drafts a personal mode skill from the person's own working style, to use alongside `arkan-mode`.
- [`retro`](../retro/SKILL.md) after a session turns its lessons into checks and skill edits the person approves.
- [`correct`](../correct/SKILL.md) sweeps the repo for mistakes agents keep repeating and lands a check for each.
- `/arkan-mode write a skill for <workflow>` runs the authoring-a-skill playbook, which follows [`writing-for-agents`](../writing-for-agents/SKILL.md). The eval playbook tests a skill change before you promote it.
- Fix a misbehaving skill in its own pr, not inside the feature work where it went wrong.

## Reply

Lead with the answer. Give at most one example prompt in a code block, adapted from [`references/recipes.md`](references/recipes.md) when one fits, then the path of the file the answer came from. Keep it short unless the person asked for the whole map.
