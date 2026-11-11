---
name: automate-me
description: "Use for \"automate me\", \"create/update/refresh my -mode skill\", \"turn my preferences or working style into a skill\", or wanting agents to follow how the person works. Drafts or revises a personal <handle>-mode skill per arkan-mode's authoring-a-skill playbook and unslop, from the person's answers and their recent chats."
disable-model-invocation: true
---

# Automate me

A guided flow that turns the person's working conventions into a skill agents follow. The output is one `<handle>-mode` skill made for them (for example `jay-mode`). It sits on top of `arkan-mode`: it holds only what is personal, never a copy of arkan-mode's rules.

This skill sequences others; it doesn't replace them: a mining pass (step 1, the same way `recall` mines chats), arkan-mode's [authoring-a-skill playbook](../arkan-mode/playbooks/authoring-a-skill.md) (authoring) and `unslop` (prose).

## Flow

### 0. Check for an existing skill

Look for `*-mode/SKILL.md` matching the person's handle under the repo's `.agents/skills/` and `.claude/skills/`, under `~/.agents/skills/` and `~/.claude/skills/`, and in omp's skills folder (`~/.omp/agent/skills/`). If one exists, confirm intent (unless they already said "update my skill" or similar):

- update the existing skill (default for repeat runs);
- start fresh (rare; ask why before doing it).

Update mode changes the rest of the flow:

- step 1 mines only history since the skill was last edited (`git log -1 --format=%cI <path>`, or the file's modification time outside git);
- step 2 asks what changed or is missing, not what to capture from zero;
- step 4 edits the file in place. Keep sections the person hasn't contradicted. Revise ones with new evidence. Add sections only for new rules.

### 1. Mine their history

Find the active workspace's transcripts with the table in `recall`. Use only that folder. Never glob across other projects: that reads private chats from unrelated work. If the folder is unreadable (a sandbox may deny it), skip mining, say so, and lean on step 2. The repo's own record helps too: corrections in ticket comments, review replies, and `AGENTS.md` lines the person added.

Spawn parallel subagents across slices of history (for example the last 2 to 4 weeks, in 3 slices so each has enough material), on a fast model where the harness lets you pick. Each reads only the path you give it, looks for the signals below, and returns a short list of patterns with evidence pointers (session id and a quote). Signals worth hunting:

- reply preferences (length, tone, format, case, "simplify" corrections);
- delegation habits (subagents, models, parallel work);
- verification posture (what "done" means, tests versus a live run, reviewers);
- code and prose discipline (style, principles cited, lint and format tools);
- process conventions (worktrees, commits, pull requests, review and merge);
- meta preferences (fixing skills mid-task, proposing new ones).

Cross-check across slices before keeping a signal. A pattern seen in 2 or more slices is strong. A lone signal is weak and usually dropped.

### 2. Ask the person directly

Mining misses intent that hasn't come up yet. Use the harness's structured question tool where it has one (claude code: `AskUserQuestion`); otherwise a short numbered list they can answer by number.

Shape: one or two questions with 4 to 6 options each, multi-select for category questions. Start broad ("which areas matter most?"), then follow up on the chosen areas with specific options. After the structured rounds, one free-form question catches what the options missed. Don't dump 20 questions.

### 3. Cluster findings

Group the signals into sections. Use only what applies:

- **reply style:** length, tone, format, case.
- **autonomy:** how much to do without asking; which connectors to use.
- **understand first:** which skills to reach for when scoping (`how`, `why`).
- **subagents:** default, parallel work, model per task.
- **prose and code discipline:** principles, lint tools, style guides.
- **review and verify:** repro posture, verify skills, live-testing tools.
- **process:** worktrees, commits, pull requests, review and merge.
- **skills:** authoring habits, fix-the-skill-first, proposing new skills.

`arkan-mode` shows the granularity. Read it for shape, not content: a rule arkan-mode already states does not go in the mode skill.

### 4. Draft the skill

Write it per the authoring-a-skill playbook. Placement:

- **path:** keep an existing mode skill where it is. A new personal mode goes in `~/.agents/skills/<handle>-mode/` with `~/.claude/skills/<handle>-mode` as a symlink to it. A mode the whole team shares goes in the repo's `.agents/skills/<handle>-mode/` with the `.claude/skills/` link. If the sandbox refuses the write, write it to `${TMPDIR:-/tmp}/<handle>-mode-draft/`, outside the repo, and give the person the exact `mv` and `ln -s` commands to run in a plain terminal.
- **handle:** the person's first name or chosen identifier.
- **`description`:** trigger on their name, `/<handle>-mode` and "work in their style", not on generic words like "write code" or "review pr". One yaml scalar, quoted.
- **`disable-model-invocation: true`** by default. Drop it only if the person wants their mode on every turn.

### 5. Iterate on prose

Apply `unslop` and the authoring-a-skill playbook to every line. Show the draft and take feedback. Expect several rounds. Cut hard: a mode skill is not a manual.

### 6. Land it

A personal skill outside any repo needs no pull request; show the final path. A repo skill goes through the repo's normal flow: a branch, a pull request per the `opening-a-pr` playbook, merged by the person. Never push to main.

## Guardrails

- **Don't overfit to one conversation.** A preference stated once and contradicted another time is noise. Require several instances before writing it down.
- **Don't be clever.** No restating other skills, no metaphors, no poetic prose for an agent reader. Keep it operational.
- **Reference, don't inline.** Skills and principle docs the person relies on appear as names or paths, not pasted excerpts.
- **Keep sections minimal.** Add a section only for a specific, non-default rule. "communicate clearly" is not a section. "short paragraphs. tables when comparing options. bullets only when items are parallel." is.
- **Name conventions generically.** Write "the person" in imperatives, not the author's first name.
- **Don't force symmetry.** No process rules worth writing down means no process section.
- **Strip private context.** No secrets, client names or personal details from the transcripts go into the skill.

## Evaluation

A mode skill is subjective. Check it with the person: does it read like them? Did it miss anything? Then ship. Tune the description only if it misfires in practice.

## When not to use

- A task-specific skill (not working conventions): the authoring-a-skill playbook alone, no mining.
- One narrow workflow ("how i write commit messages"): a regular skill, not a mode skill.
- Lessons from one chat into existing skills: `reflect`.
