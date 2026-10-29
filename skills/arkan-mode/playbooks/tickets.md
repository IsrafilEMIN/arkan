### Tickets

**Every ticket change is one named operation below. Do the operation, then rebuild and check the board, in the branch that causes the change.**

The repo's `docs/agents/issue-tracker.md` holds the mechanics: where a ticket lives, its field lines, the `gh` calls. This playbook holds when each operation runs, who runs it, and what it sets. Other skills point here by operation name.

**Board step.** On a local tracker, after each operation run the `pre-setup` skill's `scripts/board.sh build`, then `scripts/board.sh check`, from the repo root. The check must print `ok` before the commit. On GitHub, apply the board operation the tracker doc names.

**Role when none is given.** A ticket that a skill files on its own gets `needs-triage`. Only `to-tickets` and a person set `ready-for-agent` or `ready-for-human`.

| operation | sets | who runs it |
|---|---|---|
| **create** | a new ticket: heading, `**Role:**` (or `**Type:**` for wayfinder), `**Closed:** no`, `**Priority:**`, `**Blocked by:**`; body under `##` headings | `to-tickets` (person), `wayfinder` (person), `post-merge` (person), `retro` (person or agent), and agents filing a finding: `arkan-mode` (`pre-existing` review findings), `interrogate`, `swarm`, `create-formal-verification`, `maintain-formal-verification`, `maintain-verification`, `no-comments` |
| **create spec** | `spec.md`: heading, `**Closed:** no`, `**Priority:** 0`; no role | `to-spec` (person) |
| **set role** | `**Role:**` | `triage` (person) |
| **add blocker** | appends a ref to `**Blocked by:**`; never removes one | `arkan-mode` step 0 when a missing piece belongs to another ticket (agent), `wayfinder` (person) |
| **claim** | no field: the pushed work branch is the claim | `arkan-mode` step 0, `spec` implementers (agent) |
| **release** | no field. Never delete an unmerged branch to release: stop, keep the branch, and report the blocker. A person frees the ticket | `arkan-mode` (agent) |
| **close done** | `**Closed:** yes`, in the work's own branch, so the close lands with the merge | `opening-a-pr` (agent), `spec` playbook (agent) |
| **close wontfix** | `**Closed:** yes`. A ticket with `**Role:**` also gets `**Role:** wontfix`. A wayfinder ticket keeps its `**Type:**` and gets a `## Answer` that says why. A spec gets no role | `triage` (person) |
| **reopen** | `**Closed:** no`. A ticket with `**Role:**` also gets `**Role:** needs-triage`. A wayfinder ticket keeps its `**Type:**`. A spec stays without a role | a person, or `triage` |
| **resolve** | appends `## Answer`, then **close done** | `wayfinder` (person or agent) |
| **close spec** | the spec's `**Closed:** yes`, after its last ticket closes | `spec` playbook (agent) |

Each branch edits only its own tickets. A conflict in `TODO.md` is fixed by running `board.sh build` again, never by hand.

**Reply:** each ticket changed, the operation, and the `board.sh check` result.
