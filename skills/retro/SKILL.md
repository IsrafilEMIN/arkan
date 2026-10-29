---
name: retro
description: "Retrospective on a coding session: proposes changes to the agent's environment so future runs go better. Use when the person asks for a retrospective or a look back, when a review loop stops after round 3, when the same class of finding comes back in two or more review rounds, or after `post-merge` tickets a miss."
---

This is a **retrospective**, started by the user or by you. You are suggesting improvements to the coding agent's **environment** to improve future runs. You only propose: you write nothing, and the user picks what to apply.

## Steps

1. Read the `writing-for-agents` skill for the writing style guide.

2. Read the primary sources for the session the user specifies. This may mean searching through session logs on this machine. If the user doesn't specify a session, default to the current one. Also read the review findings of that session: each `code-review` report in it, with each finding's tag and `file:line` where it has them. Note each class of finding that comes up in more than one round.

3. Look for candidates for improvement in these categories.

- **Navigation**: how easy was it for the agent to find the right files? Are there hidden dependencies between files? Would a **navigation pointer** make it easier? _Use when_ the session took a long time to find a piece of information.
- **Automated checks**: are there automated checks that could catch errors the agent made? Linting, typing, tests, filesystem linters? Read the repo's own check command first (its `package.json`/build-tool `lint`/`check` scripts, its CI workflow), so a check that already exists but sits unwired or silently broken is the finding, not a reinvention. A repo with no **guardrail** (no pre-commit hook and no CI job running its lint/typecheck/test command) is itself a finding: an un-linted repo is a standing missed opportunity, not a neutral default. _Use when_ the agent made a mistake an automated check could have caught, or the repo has no guardrail at all.
- **Coding standards**: should the **reviewer agent** be given a new rule to enforce? Should an existing rule be removed or clarified? Classify the violation first: a **mechanical** one (a fixed syntactic pattern, a banned API, an import shape, a file-location rule) gets a deterministic check, full stop: a custom rule in the repo's own linter, a new pre-commit hook, or a new CI job, whichever the repo's language and existing guardrail make cheapest. Default to building the check over writing the rule. Reserve `CODING_STANDARDS.md` for genuine **judgement calls** (cross-file consistency, "matches the surrounding style," anything no guardrail could ever substitute for). _Use when_ the reviewer agent failed to catch a mistake.
- **Repeated findings**: did review flag the same class of problem in two or more review rounds or sessions? Each repeat costs a review round, so move the fix upstream, where the problem stops being written. A class is the rule or smell behind the finding, not its text: the same rule broken in two files is one class. Count `important` and `nit` findings; a `pre-existing` finding is old code, not a mistake the session wrote. Classify the class like a coding-standards violation: a **mechanical** one gets a check (a lint rule, a type, a test, a hook) that fails before review; a **judgement call** gets one line in the repo's `CODING_STANDARDS.md`, which `code-review` reads as a standards source. Propose one check or one standard per class. _Use when_ the same class of finding shows up in two or more review rounds or sessions.
- **Reviewer noise**: before you propose a change to the reviewer or to `CODING_STANDARDS.md`, read the reviewer's past findings on recent merged pull requests (`gh api repos/{owner}/{repo}/pulls/<n>/comments` on GitHub) and how each ended: fixed, answered as wrong, or left alone. A tag whose findings often end wrong or ignored needs a tighter rule, not a new one. Also run `code-review` on two or three recent merged pull requests that were never reverted or fixed after merge, and count the findings that would have led someone to make a harmful change. From the session's review reports, count the rounds each pull request took to reach a round with no `important` finding. A rise in either count is a finding. _Use when_ you propose a reviewer or standards change.
- **Global AGENTS.md**: are there any steering instructions that should be moved to coding standards (or automated checks) instead? _Use when_ the AGENTS.md file is particularly large - in the repo OR the user's global scope.
- **Tool economy**: did the agent make expensive tool calls that could be streamlined? Is there any custom tooling (CLI's, MCP's) that is particularly token-inefficient? _Use when_ the agent made an expensive tool call.
- **No-ops**: look for instructions in steering files that don't modify the agent's behavior. _Use when_ the steering files are large and unwieldy.
- **Information access**: look for opportunities to increase the agent's access to information. Teeing dev server logs, readonly access to third-party services. _Use when_ a crucial piece of information was not available to the agent.

4. Present these candidates to the user, in order of severity.

## Reference

### Implementation vs Review

Remember that all work goes through two stages: implementation and review. The implementation agent has the most **context pressure**. They are responsible for exploration, writing code, and debugging failures.

The review agent has the least context pressure - it receives a diff, so no exploration needed. It often does not need to write code or debug.

This means that the review agent should be responsible for imposing coding standards, not the implementation agent.

### Files

You have access to several files in the repo:

- `AGENTS.md`/`CLAUDE.md`: these files are pushed to the context window of any agent working in this repo. They should be used incredibly sparingly, usually only for **navigation pointers** to other files.
- `CODING_STANDARDS.md`: this file is read during review, not implementation. Keep it short: when a check now enforces one of its standards (one you propose, or one already in the repo), propose removing that standard, since review skips anything tooling enforces. Add **navigation pointers** to docs folders if the standards file gets more than 1,000 lines long.
- Docs: use docs as references files, pointed to by other files. Look for existing docs before writing new ones.
- Skills: use skills for docs (since their description goes into the agent's context window), or for user-invoked commands. Follow the advice in the `writing-for-agents` skill.
