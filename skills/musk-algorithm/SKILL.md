---
name: musk-algorithm
description: "Cut a design, codebase, pipeline or process down with Musk's five steps: question requirements, delete, simplify, speed up, automate. Use for /skill:musk-algorithm, \"run the algorithm\", \"simplify this\", \"this is too heavy\", or before you optimize or automate a slow or complex system."
---

# Musk's algorithm

Do the five steps in order on one target: a feature, a module, a CI pipeline, a deploy process, a team workflow. Do not start a step before the step before it is done. The usual mistake is to do the steps in reverse: to automate, speed up and optimize a part that should not exist.

Name the target and what it must do for its users before step 1. Read the code, config, docs and history that the target has. Do not guess.

## 1. Make each requirement less dumb

List every requirement the target meets or claims to meet. For each one, write:

- **source:** the person who asked for it, by name, or the commit, issue or doc that added it. "Security", "legal" or "the team" is not a source. A requirement with no source is a candidate for deletion.
- **why:** the problem it solves today. A reason that was true only in the past does not count.
- **verdict:** keep, change (give the less dumb form), or drop.

Question the requirements from smart or senior people most: people question them least. Ask the user about each requirement that only the user can judge.

## 2. Delete the part or step

For each part, step, file, flag, config option, dependency, check or meeting, ask: "what breaks if this goes?" When nothing that a kept requirement needs breaks, delete it. Delete more than feels safe. A part that "might be needed later" goes: you can add it back.

After the deletions, find what broke: run the tests, build and checks that cover the target, and for each kept requirement, show that it still works. A deletion broke something only when a check fails or a kept requirement stops working. Add back that part, and only that part. Count it:

```
add-back rate = parts added back / parts deleted
```

The rate is a signal, not a target. A rate under 10% usually means that you were too careful: do step 2 again on the parts you kept. Stop when a pass finds no part that you can delete while each kept requirement still works. Do not delete a working part only to get the rate up. Report the rate.

Ask the user before a deletion they did not request: user code, data, branches, jobs or another person's process.

## 3. Simplify and optimize

Only what is left after step 2. Merge parts that do the same thing, remove layers and indirection, and pick the plain design. Do not optimize a part you did not try to delete in step 2.

## 4. Speed up the cycle

Measure the time of one cycle of the target (build, test, deploy, review, release, a request) before and after. Find the slowest step that is left and make it faster. Give numbers. Do not speed up a step that step 2 could delete.

## 5. Automate

Automate last, and only the steps that are left, are stable and run often. Automating a process that is still changing makes the bad parts permanent.

## Report

Give a table with one row for each step:

| step | output |
| --- | --- |
| 1. requirements | each requirement with its source, why, and verdict |
| 2. delete | what you deleted, what you added back, the add-back rate |
| 3. simplify | what you merged or simplified |
| 4. speed up | cycle time before and after, with the command or data that measured it |
| 5. automate | what you automated, or why nothing was ready |

Mark each number you did not measure as an estimate.
