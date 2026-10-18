# arkan

arkan is one bundle of agent skills. this glossary names the parts of the way work moves through it.

## Language

**Task**:
the smallest piece of work an agent can take and finish alone, from start to a merged and checked change, with no more decisions from a person. a ticket is a task; a small, clear request from the user is also a task.
_Avoid_: job, work item

**Shaping**:
the work before a task exists: grilling an idea, writing a spec, and splitting it into tickets. a person starts each shaping step.
_Avoid_: pre-work, planning phase

**Spec**:
a written description of what to build and why, made during shaping, before it is split into tickets.
_Avoid_: prd, design doc

**Ticket**:
a task written down in the repo's issue tracker, with the tickets it waits for.
_Avoid_: issue, story

**Task loop**:
the part of the flow that `arkan-mode` drives on its own, from one task to a merged, watched change.
_Avoid_: pipeline, execution phase

**Playbook**:
a fixed list of steps for one kind of task, which the agent copies into its todo list and does in order.
_Avoid_: recipe, workflow

**Principle**:
a short rule that changes an engineering decision, such as "fix the root cause".
_Avoid_: guideline, best practice
