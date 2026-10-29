---
name: figure-it-out
description: "Design an auditable playbook when none of arkan-mode's playbooks fits: a large migration or an ambitious multi-part change. Scales rigor to the task, runs a hypothesis loop, and logs decisions. Use for /figure-it-out or 'figure it out'."
---

# Figure it out

When a task matches none of arkan-mode's playbooks (`skills/arkan-mode/playbooks/`), design one. The deliverable before any code is the workflow itself: a list of phases that scales rigor to the task, runs the scientific method, and leaves a decision trail a person can audit after stepping away.

It is still a task: if the goal itself is unclear, that is shaping (arkan-mode step 0), and a person starts `grilling` or `to-spec` instead.

## Start

Open a todo list whose first item is to read arkan-mode's principles (`../arkan-mode/SKILL.md#principles`) and the `principle-<title>` leaf each entry names. Then add the phases below as todos.

## Phase A: frame

Ground first, then commit. Do not start the run until you can state:

- the definition of done as a falsifiable predicate (**prove it works**, `principle-prove-it-works`);
- the scope, in rough units and effort, plus the blockers grounding found;
- the rigor level, biased high. One-way doors and a large blast radius get more; reversible low-stakes steps get less. Rigor is gates and artifacts, not "try harder".

Show the framing and its tradeoffs before committing to a long run. Reversible work goes ahead (**never block on the human**, `principle-never-block-on-the-human`), but a multi-hour run earns one checkpoint with the person.

## Phase B: design the workflow

Break the work into atomic units that can each land on their own. Order them riskiest unknown first. Scaffold and verification come before features (**foundational thinking**, `principle-foundational-thinking`).

- Build the verification harness before the work, with a baseline captured from the state before the change, so each check reads "old value vs new value". Use the repo's verify skill where it has one.
- For a one-way-door design decision, run `architect` (it runs `arena`). Skip it for mechanical work whose shape is already concrete: a second arena over a settled design is over-engineering (**laziness protocol**, `principle-laziness-protocol`).
- Decide what fans out. Parallelize only across seams, and give each worker its own worktree or branch (**separate before you serialize shared state**, `principle-separate-before-serializing-shared-state`). Don't over-fan. Code units fan out as `arkan-mode` subagents, each owning one branch and one PR (the orchestrate playbook for many). `swarm` is only for audits and checks: its workers report and never push or open PRs.
- Plan the landing: each unit lands as its own pull request on trunk, through the opening-a-pr and shipping playbooks.
- Write the designed phase list down. That list is what the person reviews.

Then run the design. Add its steps to the todo list as concrete items between phase C and phase D. Run each under the phase C loop, and write the phase D log as each step lands, a row at a time, not all at the end.

## Phase C: run the loop

Each unit is an experiment. State the hypothesis, make the smallest change, measure against the predicate on the real artifact, keep it if it moved forward, revert it if it did not. Verify each unit before starting the next (**sequence verifiable units**, `principle-sequence-verifiable-units`); do not batch checks at the end.

- Verify by inspecting the artifact, never a self-report. When something passes too easily, suspect the way you observed it before the system.
- Pair delegated work with a judge. If a worker games the gate, reset and harden the contract. If the gate itself is wrong, fix the gate in its own change instead of routing around it.
- A verdict is VERIFIED, NOT VERIFIED or INCONCLUSIVE. Inconclusive is not a pass. Don't hide a negative.

## Phase D: keep the audit trail

Log the run with `show-me-your-work`. Work this size usually earns a committed trail, so the person can read it in the pull request. The trail plus the diff is what lets the person come back and trust the work.

## Phase E: verify and hand back

Check the whole against the phase A predicate on the real product, not just the harness. Turn any repeated correction into a gate, a lint rule, a check or a script (**encode lessons in structure**, `principle-encode-lessons-in-structure`); a correction that keeps coming back in review goes to `retro`.

**Reply:** the playbook you designed, the rigor level and why, the decision trail's path, what is verified against the predicate, and what is still open.
