# how the claude code team does code review

- link: <https://claude.dev/blog/solving-code-review-at-anthropic/>
- authors: addy osmani, morgan westlee lunt, qing wang
- published: 2026-10-15

## core claim

machines do most of the code reading, and people spend their attention where the risk is. the team measures human time per change, and it uses revert and incident rates as the guardrail.

## what arkan owns

arkan owns the parts that an agent does inside any repo: review before the pr, the review loop, the pr body, the merge grade, and learning from misses.

| item | status | where |
|---|---|---|
| verify the work, then review the diff in a fresh context before the pr | done before | `arkan-mode/SKILL.md`, `code-review` |
| several finders, then a separate pass that tries to disprove each finding | done before | `code-review` step 5 |
| tag each finding `important`, `nit` or `pre-existing`; a `pre-existing` one becomes a ticket | done before | `code-review` step 5, `arkan-mode/SKILL.md` |
| round cap of 3, diff-only re-review, no repeated findings, fix the class of bug | done before | `arkan-mode/SKILL.md`, `code-review`, `retro` |
| `REVIEW.md`: what failure looks like, skipped paths, `file:line` evidence, a nit cap, a count first | done before | `pre-setup/references/review.md` |
| a repeated finding moves into a lint rule, a check or a standard | done before | `retro` |
| measure noise from what people did with each comment | done before | `retro` |
| an approval covers one commit; a bot approval is not a person's | done before | `arkan-mode/playbooks/shipping.md` |
| revert or fix forward, then ask which layer should have caught the miss | done before | `post-merge` |
| an explainer for one part of the code instead of reading trivial diffs | done before | `how`, `teach` |
| grade each change `auto` or `manual` from the diff, not the author | done | `code-review` step 6 |
| `## Risk` and `## Revert` in the pr body | done | `arkan-mode/playbooks/opening-a-pr.md` |
| run the reviewer on known-clean prs and track rounds to pass | done | `retro` |
| name `REVIEW.md` and `AGENTS.md` as reviewer inputs; flag a diff that makes an `AGENTS.md` line out of date | proposed | `code-review` step 3 |
| turn each miss into an eval case and score the reviewer again after each change to it | proposed | `post-merge`, `arkan-mode/playbooks/eval.md` |
| a nightly review of old code | proposed | prompt in arkan, schedule in `underground` |

## what arkan leaves to others

- `underground`: sensitive paths that always need a person, branch protection, CODEOWNERS, the trusted-author list, the merge through `agent-merge`, and the schedule for any nightly run.
- each repo's ci and release: required checks, the merge queue, feature flags, internal use first, staged release channels.
- people and the team: on-call, revert and incident dashboards, circuit breakers that tighten approval.
