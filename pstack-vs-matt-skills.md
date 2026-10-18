# discussion summary: pstack and matt pocock's skills

## pstack

- pstack emphasizes end-to-end task coordination through `/poteto-mode`.
- run `/setup-pstack` once to configure models and the reasoning budget.
- `/poteto-mode` selects a playbook and uses supporting skills as needed.
- a typical feature flow is: understand the code → explore designs → delegate implementation → verify runtime behavior → prepare a pull request.
- planning exists through `architect`, `arena`, prototypes, and the multi-phase plan playbook.
- pstack does not provide matt's dedicated interview → specification → tickets layer.
- pstack targets cursor; its model routing and subagent features may require adaptation elsewhere.

## matt's skills

- matt emphasizes explicit stages, with particularly strong support before implementation.
- run `/setup-matt-pocock-skills` once per repository.
- a typical flow is: `/grill-with-docs` → `/to-spec` → `/to-tickets` → `/implement` or `/implement-spec`.
- the user starts each major stage; the stages do not automatically invoke one another.
- stages invoke supporting skills such as `grilling`, `domain-modeling`, `tdd`, and `code-review`.
- `/implement-spec` can coordinate parallel implementation of an entire specification.
- not every task needs every stage.

## comparison

- both emphasize understanding, deliberate design, maintainable code, parallel work, and verification.
- the main difference is the control boundary: pstack coordinates the overall task; matt exposes major stages for the user to select.
- the distinction is not planning versus no planning, or automation versus no automation.
- a proposed combination uses matt for requirements and planning, then pstack for execution; neither collection supplies that combined workflow.

sources: [pstack](https://github.com/cursor/plugins/tree/main/pstack), [matt's skills](https://github.com/mattpocock/skills).
