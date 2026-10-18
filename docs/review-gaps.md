# review gaps: arkan against the claude code team's review flow

this file compares the arkan plan with one article, and lists what arkan must add. read on 2026-10-18.

source: addy osmani, morgan westlee lunt and qing wang, "how the claude code team does code review", claude.dev blog, 2026-10-15. <https://claude.dev/blog/solving-code-review-at-anthropic/>. the text came from a paste, because the link did not load from the cloud session. the numbers below are the article's claims, not facts we checked.

## the article in short

the goal is the least human time per change, with no rise in reverts or incidents. review does not end at one gate. it runs in layers, and each layer catches some problems:

1. **before the pr.** the agent runs tests, build and lint, and shows the output. a second agent reviews the diff in a fresh context.
2. **ai review on every pr.** finders look for bugs in parallel. verifiers vote on each finding, and only the ones they agree on get posted. each is tagged important, nit or pre-existing. every finding must be fixed or resolved with a reason.
3. **security review.** a separate pass. an open finding from either review blocks the merge.
4. **required ci.** lint, types, tests, build. the pr template asks for testing, risk and how to revert.
5. **approval scaled by risk.** a classifier sets the tier from the change, not the author: no person, one or two. some paths always need a person. a bot's approval never counts as a person's. an approval covers one commit.
6. **merge queue, flags, staged release.**
7. **fast detection and rollback.** each incident review asks which layer should have caught it. each incident becomes an eval case for the reviewer.

two more lessons:

- **review must converge.** an agent author and an agent reviewer can loop all night (one pr went 50+ rounds). about 59% of repeat flags were old code. fixes: cap at 3 rounds, re-review only the new diff, flag the class of bug, never repeat a finding. claimed result: mean reviews to pass went from 2.08 to 1.32.
- **measure noise.** sort each finding by what the person did with it (fixed, wrong, intended, did not matter). an agent author fixes every nit, so noise costs a full round.

## what arkan already covers

| article layer | arkan piece |
|---|---|
| show the output, do not say "done" | `arkan-mode` step 5, the `verification` principles |
| end-to-end check of real behavior | `create-verification`, `maintain-verification` |
| fix a repeated finding at the source | `learn` |
| review before a person looks | `review` |
| drive the pr to green, never merge alone | `ship` |
| learn a slice of code from an explainer | `explain` |
| a person owns the outcome | `arkan-mode` autonomy rules |

## gaps, and where each one went

| # | gap | change |
|---|---|---|
| 1 | review does not converge | `review`: 3-round cap, new-diff-only re-review, bug class, no repeats |
| 2 | no verifier on findings | `review`: find, then verify; drop style-only findings |
| 3 | no `pre-existing` tag | `review`: tags `important`, `nit`, `pre-existing`, each with a `file:line` |
| 4 | no security review | new skill `security-review` |
| 5 | no risk tier | `review` sets the tier; `ship` writes it in the pr body. enforcement (codeowners, branch protection) stays in the guard-rules repo |
| 6 | no triage after the merge | new skill `triage`: watch, fix forward or revert, incident to eval case |
| 7 | no `REVIEW.md` | `review` reads it; `learn` writes repeated findings into it |
| 8 | pr body lacks "how to revert" | `ship`: pr body has risk tier and how to revert |
| 9 | no noise metric | open. start with a log of how each finding ended. decide where it lives when `review` is built |

all changes are in [core-skills.md](core-skills.md).

## gaps in the repo, not from the article

- `skills/arkan-mode/SKILL.md` points to `playbooks/<name>.md`, but there is no `playbooks/` folder yet. step 1 of the skill finds nothing.
- 13 of the 14 core skills exist only as entries in `core-skills.md`.

## decisions

- **the reviewer eval set lives in each repo** (`.arkan/evals/review/`), not in arkan. arkan is infra that repos use, not a project with its own incidents. (decided 2026-10-18)

## open questions

- a per-repo setup step could create a starter `REVIEW.md`. is that part of `create-verification`, or of the install and pre-setup command?
