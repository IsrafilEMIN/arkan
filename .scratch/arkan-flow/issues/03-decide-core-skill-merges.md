# 03: decide which core skills to merge, if any

**What to build:** the owner decides which of the 14 planned core skills in `docs/core-skills.md` get written, which are only routes to skills that exist, and which source skills retire. `core-skills.md` and `arkan-mode` then name only skills that exist or have a ticket.

**Blocked by:** None (can start immediately). needs the owner's decision.

proposal (rule: merge only when two skills start at the same moment and do the same job, or when a name clash forces it; small skills that compose are the point, so no merge for tidiness):

| planned | proposal | why |
|---|---|---|
| grill | no new skill. keep `grill-with-docs` | it already is the merge (`grilling` + `domain-modeling`), and it is a shaping step a person starts |
| plan | no new skill. keep `to-spec`, `to-tickets`, `wayfinder` | shaping steps; the pause between spec and tickets is a decision point for the person |
| build | no new skill. fold `implement` into `arkan-mode`; keep `implement-spec` | a ticket now enters `arkan-mode`, which does what `implement` did (claim, tdd, review, resolve the card). `implement-spec` runs many tasks in parallel, one `arkan-mode` run per ticket |
| tdd | keep `tdd` (+ `test-to-break` as its policy) | already one engine and one policy. do not install pstack's `tdd` (name clash) |
| debug | keep `diagnosing-bugs` | does the job; renaming costs more than it gives |
| review + security-review | **one new skill**, `arkan-review`, with two lenses (code, security) | same finder/verifier machinery, same tags, one round count and one marker; also removes the clash with the built-in `/code-review` and `/security-review`. retires matt's `code-review` |
| ship | no new skill | the `pr` skill plus the opening-a-pr, babysit and shipping playbooks; tier and approval live in ci (tickets 09, 11) |
| learn | **one new skill**, `learn` | fires on a correction or a miss; retires `retro` (and pstack `correct`, `reflect` if installed) |
| post-merge | **one new skill** | nothing does it today (ticket 08) |
| write | no new skill for now | `arkan-mode` holds the reply rules; `writing-for-agents` covers agent text. revisit after pstack `unslop` is installed |
| create-/maintain-verification | keep pstack's two skills | they start at different times (once, then on a schedule) |

result: 3 new skills (`arkan-review`, `learn`, `post-merge`), 3 retired (`implement`, `code-review`, `retro`), the rest are routes.

- [ ] the owner accepts, changes or rejects each row; the decision is recorded here
- [ ] `docs/core-skills.md` lists only the decided skills
- [ ] `arkan-mode` section 2 routes to the decided names, with no bracketed plan names left for skills that will not exist
- [ ] a follow-up ticket exists for each new skill and each retirement
