# 26: spec mode in arkan-mode

**What to build:** `implement-spec` folds into `arkan-mode` as a spec playbook. given one ticket, `arkan-mode` runs one task loop; given a spec with tickets, it runs the spec playbook: integration branch, one subagent per ready ticket running the task loop, merge each, start the next ready ones, one review, one pr. gate: the agent may pick up any todo card tagged `#ready-for-agent` on its own, and for a spec it may run every such card in parallel; `#ready-for-human` and `#needs-info` cards wait. the person sets the tag (`triage`), so the tag is the person's go.

**Blocked by:** None (can start immediately).

- [ ] `skills/arkan-mode/playbooks/spec.md` holds the 9 steps of `implement-spec`, with each ticket run through the task loop
- [ ] `arkan-mode` step 0 picks the mode from what it was given, and carries the `#ready-for-agent` gate
- [ ] `skills/implement-spec/` is removed, and `README.md` matches
- [ ] proof: a small spec with two independent ready tickets and one blocked one: two run in parallel, the third starts after its blocker merges
