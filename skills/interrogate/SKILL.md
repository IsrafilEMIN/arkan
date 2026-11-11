---
name: interrogate
description: "Adversaries try to break a change or design, and only findings proven by a run survive. Use for \"interrogate\", \"adversarial review\", \"multi-model review\", \"challenge this\", \"find blind spots\", or \"tear this apart\"."
---

# Interrogate

Adversaries try to break a change or a design. A finding survives only when a run proves it. Report the findings. Do not apply fixes.

Use it for a contested design, a change on a sensitive path (auth, billing, installers, release workflows, agent instruction files), or when the person asks. arkan-mode reaches for it on a contested design before shipping.

## Frame

The scope is what the person names. Otherwise it is the branch diff from its merge base with the base branch, through the working tree. Restate the intent in your own words, from the person's message, the commits and the pull request body. Ask the person when the intent is unclear.

## Fan out

Run Phase A steps 3 and 4 and Phase B of the `arena` skill, with three changes:

- The runners are adversaries. Two is the minimum. Arena's model rule applies: different model families where the harness lets you pick a model per subagent, else the current model in fresh contexts, and say so in the report.
- Copy the scope's uncommitted changes into each worktree.
- Spawn each adversary as a general-purpose subagent that can edit and run commands in its own worktree.

In place of the arena task and rationale, give each adversary the scope, the intent, the repo's `CODING_STANDARDS.md` when it exists, and this brief:

> Break this change. Prove each finding with a run against the real code, such as a failing test, a repro script, or command output that shows the wrong behavior. For a design or plan, run a prototype or probe the current tree. A broken line of `CODING_STANDARDS.md` counts only when a run shows it, such as a failing check. Keep repros in your own worktree. Report each finding with a title, the exact command, the output it printed, and the output the intent requires. Leave out anything you did not run. That covers style, naming, structure, and risks that need a future change to matter. No findings is a valid result.

## Verify

Verify each finding per arena Phase F by rerunning its command. Keep a finding when the output shows the failure and the failure breaks the intent. Drop the rest. Merge findings that share a root cause.

Skip arena Phases C, D and E. Adversaries find different failures, so the verdict keeps every verified finding, not one adversary's list.

## Output

- **Intent**: the restatement.
- **Adversaries**: one line each, with its model, or "same model, fresh context" where models could not differ.
- **Findings**: for each verified finding, the command, its output, how it breaks the intent, and the adversaries that found it. Say "no verified findings" when none survive.
- **Dropped**: for each adversary, the count of dropped findings and why.

Delete the adversary worktrees once the report is written.
