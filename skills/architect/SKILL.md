---
name: architect
description: "Sketch types, signatures and module structure before code, compare at least two designs, then stay in the loop while the code fills in. Use for /architect, 'architect this', 'design this', or non-trivial work where jumping to code would lock in the wrong shape."
---

# Architect

Sketch types, function signatures, class shapes and module boundaries with `not implemented` bodies and pseudocode. Compare designs from more than one model, then fill in the code against the chosen sketch.

It is the deep version of arkan-mode's "code crosses a function boundary → sketch the types first" (step 2 of the feature playbook). Use it when the shape is a one-way door; a small change with an obvious shape needs only the playbook's sketch.

## Start

Open a todo list with one entry per phase before starting: 1 ground, 2 sketch, 3 agree, 4 implement, 5 scrap.

## Phase A: ground the problem

Build a real mental model of every system the new code touches. Run the `how` skill over the relevant parts. Naming a file is not grounding: produce the architectural explanation `how` prescribes. If the design redefines ownership or layering, also run `why` on the existing shape, so the old reasons become constraints, not guesses. Read the repo's `GLOSSARY.md` and the adrs in `docs/adr/` that touch the area.

Skip phase A only for truly greenfield work with no surrounding system.

## Phase B: sketch

Run the `arena` skill with the design-sketch task and the phase A grounding, passing [`references/runner-prompt.md`](references/runner-prompt.md) as each runner's prompt. Runners use different model families where the harness allows (the `arena` skill's model rule).

Design it twice. Require at least two structurally different candidates before synthesis, even when the first looks good enough: whole-shape alternatives, not point fixes inside one shape. This is **exhaust the design space** (`principle-exhaust-the-design-space`) made concrete.

Screen every candidate against [`references/design-red-flags.md`](references/design-red-flags.md) before synthesis. Assume the next contributor is an agent that sees only the files it opened, copies the nearest example, and takes the shortest path that compiles. Prefer the design where a change that looks right from one file is right for the whole repo.

Compare the viable candidates on interface depth: prefer the design that hides more behind a smaller, simpler public surface (`codebase-design` has the vocabulary). A rich interface can keep call chains short by concentrating capability instead of spreading it across layers.

Arena returns one synthesized design. Its synthesis decision fills the rationale's "synthesis decision" section.

## Phase C: agree (opt-in)

Default: go straight to implementation with the synthesized design, with no checkpoint.

Stop for the person's sign-off only when they asked for it ("/architect with checkpoint", "show me before you implement"). A one-way door with a large blast radius (a public api, a data schema, a wire format another repo reads) is a product call: show the design and ask, per arkan-mode's rule on forks.

The synthesis can ship as its own commit either way, as the "scaffold first" mode of **foundational thinking** (`principle-foundational-thinking`). Planned breakage during fill-in is fine, per **outcome-oriented execution** (`principle-outcome-oriented-execution`). For adversarial pressure on the design before implementing, run `interrogate` on the sketch.

If the person pushes back on the shape, treat that as phase A evidence: ground again and re-run phase B before writing more code.

## Phase D: implement against the sketch

Replace `not implemented` bodies with code, and pseudocode with logic, test-first per `tdd`. The sketch is the contract. A deviation from it is a signal to surface, not friction to absorb in silence: if a function needs a parameter the sketch did not foresee, ask whether the sketch was wrong, the requirement was missed, or the implementation is overreaching.

## Phase E: scrap when the architecture is wrong

If implementation keeps producing friction the sketch cannot absorb, throw the sketch out. Don't bolt fixes onto a wrong design, per **redesign from first principles** (`principle-redesign-from-first-principles`) and **fix root causes** (`principle-fix-root-causes`).

The signal is a pattern, not one instance:

- the same shape of workaround appears again and again in unrelated code;
- several unrelated edge cases all need special-case branches;
- types need escape hatches (`any`, casts, optional fields that are always set) to compile;
- the "we need a lock" reflex where the sketch said the state was not shared;
- callers have to know the abstraction's internal rules to use it;
- two or more independent phase D deviations of the same shape.

Use judgment: a few edge cases do not condemn an architecture, and complexity in the data is not complexity in the design.

When you scrap:

1. re-run `how` over what has been built;
2. redesign as if the new constraints had been there on day one;
3. subtract before adding, per **subtract before you add** (`principle-subtract-before-you-add`): the new sketch is smaller than the old one before it grows;
4. go back to phase B and re-run arena.

## Outputs

The caller's usage written first, and the type sketch derived from it. One file of new types and signatures for a small change; a module map plus type definitions for larger work. The rationale ships with it, shaped per [`references/rationale-template.md`](references/rationale-template.md), including the usage sketch and the synthesis decision. A decision with lasting effect also becomes an adr through `domain-modeling`.
