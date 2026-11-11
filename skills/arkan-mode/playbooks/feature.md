### Feature

**You own the design. Plan, review, verify.** Delegate implementation. Stay in the lead.

1. Read the affected subsystem.
2. Sketch the design before the code: the data shape, then the types and signatures with empty bodies. When more than one shape is valid, sketch two or three and compare them (**exhaust the design space**, `principle-exhaust-the-design-space`).
3. Write the throughput checkpoint as four todo items. A dimension that genuinely does not apply (single file, no fan-out) keeps its item with `n/a: <reason>` rather than being dropped:
   - **Blocking first steps.** Gates run before fan-out.
   - **Independent workstreams.** Disjoint files, services, or layers parallelize. Shared writes serialize.
   - **Shared mutable state.** Default to splitting the target (**separate before you serialize shared state**, `principle-separate-before-serializing-shared-state`). Serialize only for real invariants.
   - **Smallest safe decomposition.** If one worker is best, name why.
4. Delegate code-writing to a subagent with a specific scope: file paths, the named data shape and its organizing structure (**model the domain**, `principle-model-the-domain`: a state machine over scattered booleans, a table or registry over branching, a typed model over repeated shape assumptions), chosen before the delegate writes logic, and success criteria. Match each subagent's model to the job, per **Subagents** in `SKILL.md`. Keep review separation: the agent that writes the code does not review it. A subagent that cannot spawn its own subagents owns the diff directly. No "standing by" reply that waits on a nested agent. Comments per **Comments** in `SKILL.md`. Surgical edits, re-ground against the source for upstream-derived files. Port shared-primitive improvements to all consumers and verify each. Commit liberally.
5. Verify on the matching surface. "Inconclusive" or wrong-surface is not a pass. Flag it.
6. Commit each verified unit as you go, small and in order, and checkpoint it with `gh-broker push` (see **Commits** in `playbooks/opening-a-pr.md`). Follow-ups are their own PRs on trunk.
   Use the **sequence verifiable units** principle (`principle-sequence-verifiable-units`), building and checking each small unit before the next.
7. If the design is contested, `interrogate` before shipping.
8. Run **Opening a PR**.

Code-coupled work (one feature, one migration) goes to a single owner with the checkpoint inline. That owner fans out internally after the blocking phase. Parent-level fan-out is for slices that produce independent artifacts (audits, cross-subsystem investigations, competing experiments). Rewrite the checkpoint at phase boundaries. Spawn a fresh owner rather than chaining interrupts.

**Reply:** what you built, what you chose and why, the throughput checkpoint, open decisions. Tables for design alternatives.
