# 03: decide which core skills to merge, if any

**What to build:** the owner decides which of the 14 planned core skills (from `docs/core-skills.md`, now removed; see git history) get written, which are only routes to skills that exist, and which source skills retire. `README.md` and `arkan-mode` then name only skills that exist or have a ticket.

**Blocked by:** None (can start immediately). needs the owner's decision.

proposal (rule: merge only when two skills start at the same moment and do the same job, or when a name clash forces it; small skills that compose are the point, so no merge for tidiness):

| planned | proposal | why |
|---|---|---|
| grill | no new skill. keep `grill-with-docs` | it already is the merge (`grilling` + `domain-modeling`), and it is a shaping step a person starts |
| plan | no new skill. keep `to-spec`, `to-tickets`, `wayfinder` | shaping steps; the pause between spec and tickets is a decision point for the person |
| build | no new skill. **decided:** `implement` retires by moving each of its jobs into `arkan-mode` → skills → playbooks (table below); keep `implement-spec` | a ticket now enters `arkan-mode`. `implement-spec` runs many tasks in parallel, one `arkan-mode` run per ticket |
| tdd | keep `tdd` (+ `test-to-break` as its policy) | already one engine and one policy. do not install pstack's `tdd` (name clash) |
| debug | keep `diagnosing-bugs` | does the job; renaming costs more than it gives |
| review + security-review | **decided: two separate skills**, `code-review` and `security-review` | the owner rejected one merged skill (2026-10-18). each runs in fresh-context subagents. the clash with the harness's built-in commands of the same names is ticket 17 |
| ship | no new skill | the `pr` skill plus the opening-a-pr, babysit and shipping playbooks; tier and approval live in ci (parked: `.scratch/review-ci/spec.md`, sections 09 and 11) |
| learn | open. **keep `retro`** (revised) | `retro` is a person-started look back over a whole session that proposes changes to the agent's environment. `learn` would start by itself on one miss (a correction, or a hand-off from `post-merge`) and make the fix. they start at different moments, so by the rule above they do not merge. option: no `learn` skill; `post-merge` and `arkan-mode` call `retro` on the one miss |
| post-merge | **one new skill** | nothing does it today (ticket 08) |
| write | no new skill for now | `arkan-mode` holds the reply rules; `writing-for-agents` covers agent text. revisit after pstack `unslop` is installed |
| create-/maintain-verification | keep pstack's two skills | they start at different times (once, then on a schedule) |

result (revised 2026-10-18): new skills `security-review` (as its own skill), `post-merge`, and `learn` only if the owner wants it beside `retro`. retired: `implement` (its jobs move as below). kept: `code-review`, `retro`, and the rest as routes.

where each job of `implement` goes:

| `implement` job | new home |
|---|---|
| fetch the ticket, state its title, ask if the reference is unclear | `arkan-mode` step 0 |
| no tracker set → tell the user to run `/pre-setup` | `arkan-mode` step 0 |
| claim the ticket before work (push its branch) | `arkan-mode` step 0, per the `## Board` section of `docs/agents/issue-tracker.md` |
| `tdd` at agreed seams | feature and bug-fix playbooks → `tdd` skill |
| typecheck and single test files often, full suite once at the end | `arkan-mode` step 1.4 and 1.5 (prove) |
| `code-review`, fix every finding, full suite again | `arkan-mode` section 2 → `code-review`, then the opening-a-pr playbook |
| commit to the branch | opening-a-pr playbook |
| close the ticket the tracker's way, board **Resolve** in the same branch | opening-a-pr playbook (a new step), so the card reaches `main` with the merge |

- [ ] the owner accepts, changes or rejects each row; the decision is recorded here
- [ ] `README.md` lists only the decided skills
- [ ] `arkan-mode` section 2 routes to the decided names, with no bracketed plan names left for skills that will not exist
- [ ] a follow-up ticket exists for each new skill and each retirement

## Comments

- 2026-10-18, owner: retire `implement` once `arkan-mode` has all of its jobs. done on branch `claude/fervent-turing-qu5b6e`: `arkan-mode` step 0 now has the tracker check, the ticket fetch and the claim; step 1.4 has the type check, single tests and full suite; section 2 has "fix every issue `code-review` raises, then run the full suite again"; the opening-a-pr playbook has the ticket close. `skills/implement/` is removed. the `build` row is settled.
