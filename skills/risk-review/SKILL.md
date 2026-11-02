---
name: risk-review
description: "grade whether a pr head can merge without a person: pass or manual, with a one-line reason. use in every risk-review reviewer session, or when the user asks for a risk review or a merge grade."
---

grade the merge of one head. grade from the diff, never from who wrote it.

1. **pin the head.** in a reviewer session, follow **reviewer sessions** in `../arkan-mode/references/broker.md`: the head is the sha `broker sync <owner/repo> --pr <n>` prints, and the diff is `git --git-dir "$UG_REVIEW_STORE" diff origin/<default>...origin/pr/<n>`. outside one, review the current branch against its base. _done when_ you have the head sha and a non-empty diff.
2. **read the open findings.** read `broker pr-status <owner/repo> <n>` for the `block` records on this head, and any `code-review` report you were given. an open `important` finding counts as open until a later head fixes it.
3. **grade.**
   - `manual` when the diff touches auth, billing, secrets, ci workflows, installers, release or auto-update paths, caching, system prompts, data migrations or a public api; when any `important` finding is still open; or when you are unsure.
   - `pass` only for docs, copy, tests, internal-only code, or additive behaviour behind a flag, with no open `important` finding.

   paths the repo's guards list as sensitive always need a person; the grade never overrides them. the grade covers the head you reviewed, so a new head needs a new grade.
4. **record it.** in a reviewer session, run `broker review <owner/repo> <n> <head-sha> <pass|manual> "<reason>"`. the reason names the path or finding that decided the grade. a `manual` record is a hold on every later head of the pr (see `../arkan-mode/references/broker.md`).

**reply:** the head sha, the grade and its one-line reason.
