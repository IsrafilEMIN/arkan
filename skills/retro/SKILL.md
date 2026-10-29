---
name: retro
description: "Retrospective on one coding session: proposes repo guardrails (checks, CODING_STANDARDS.md, AGENTS.md lines) and edits to skills, so future runs go better, and files backlog tickets. Use when the person asks for a retrospective, a look back, or to turn lessons from this chat into skill edits, when a review loop stops after round 3, when the same class of finding comes back in two or more review rounds, or after `post-merge` tickets a miss."
---

This is a **retrospective** on one session, started by the person or by you. You suggest improvements to the coding agent's **environment** so future runs go better. It has two outputs:

- **guardrails** for the repo: checks, `CODING_STANDARDS.md` lines, `AGENTS.md` lines, tooling;
- **skill edits**: changes to skills and to `AGENTS.md` steering, found by reviewer subagents that read the session.

You only propose. Nothing is applied until the person approves it, row by row. Skill changes affect every future agent. The one thing you do without waiting is file backlog tickets.

Skip it when the session is trivial, off topic, or already covered by a skill the agent followed correctly. One-offs are not learnings. To find mistakes repeated across the repo's history and land a check for each, a person starts `correct`.

## Steps

1. Read the `writing-for-agents` skill for the writing style guide.

2. **Locate the session.** Take the session the person names; if they name none, take the current one. Find its transcript file (where each harness keeps them: the table in `recall`). Read only the active workspace's folder; never glob across other projects, which holds unrelated private chats. List the newest files, read each one's first line, and take the file whose opening user message matches the session. If none matches, or the folder is unreadable (a sandbox may deny it), use a tight digest of the session instead, and say so. Also read the session's review findings: each `code-review` report in it, with each finding's tag and `file:line` where it has them. Note each class of finding that comes up in more than one round.

3. **Guardrail candidates.** Look for candidates in these categories.

- **Navigation**: how easy was it for the agent to find the right files? Are there hidden dependencies between files? Would a **navigation pointer** make it easier? _Use when_ the session took a long time to find a piece of information.
- **Automated checks**: are there automated checks that could catch errors the agent made? Linting, typing, tests, filesystem linters? Read the repo's own check command first (its `package.json`/build-tool `lint`/`check` scripts, its CI workflow), so a check that already exists but sits unwired or silently broken is the finding, not a reinvention. A repo with no **guardrail** (no pre-commit hook and no CI job running its lint/typecheck/test command) is itself a finding: an un-linted repo is a standing missed opportunity, not a neutral default. _Use when_ the agent made a mistake an automated check could have caught, or the repo has no guardrail at all.
- **Repeated findings**: did review flag the same class of problem in two or more review rounds or sessions? Each repeat costs a review round, so move the fix upstream, where the problem stops being written. A class is the rule or smell behind the finding, not its text: the same rule broken in two files is one class. Count `important` and `nit` findings; a `pre-existing` finding is old code, not a mistake the session wrote. Classify the class like a coding-standards violation: a **mechanical** one gets a check (a lint rule, a type, a test, a hook) that fails before review; a **judgement call** gets one line in the repo's `CODING_STANDARDS.md`, which `code-review` reads as a standards source. Propose one check or one standard per class. _Use when_ the same class of finding shows up in two or more review rounds or sessions.
- **Reviewer noise**: before you propose a change to the reviewer or to `CODING_STANDARDS.md`, read the reviewer's past findings on recent merged pull requests (`gh api repos/{owner}/{repo}/pulls/<n>/comments` on GitHub) and how each ended: fixed, answered as wrong, or left alone. A tag whose findings often end wrong or ignored needs a tighter rule, not a new one. Also run `code-review` on two or three recent merged pull requests that were never reverted or fixed after merge, and count the findings that would have led someone to make a harmful change. From the session's review reports, count the rounds each pull request took to reach a round with no `important` finding. A rise in either count is a finding. _Use when_ you propose a reviewer or standards change.
- **Global AGENTS.md**: are there any steering instructions that should be moved to coding standards (or automated checks) instead? _Use when_ the AGENTS.md file is particularly large - in the repo OR the user's global scope.
- **Tool economy**: did the agent make expensive tool calls that could be streamlined? Is there any custom tooling (CLI's, MCP's) that is particularly token-inefficient? _Use when_ the agent made an expensive tool call.
- **No-ops**: look for instructions in steering files that don't modify the agent's behavior. _Use when_ the steering files are large and unwieldy.
- **Information access**: look for opportunities to increase the agent's access to information. Teeing dev server logs, readonly access to third-party services. _Use when_ a crucial piece of information was not available to the agent.

4. **Skill-edit candidates.** Run this step when the session used skills or ran long. Skip it when the session is short and the only signal is a repeated review finding; step 3 covers that.

   Spawn three reviewers at once, in fresh contexts. They may use the run's connectors to look up tickets, chat threads and traces the transcript references, but they never write.

   | lens | model, where the harness lets you pick | prompt |
   |---|---|---|
   | judgment | your strongest model | [`references/judgment-reviewer.md`](references/judgment-reviewer.md) |
   | tooling | a fast model, a different family where possible | [`references/tooling-reviewer.md`](references/tooling-reviewer.md) |
   | divergent | your strongest model | [`references/divergent-reviewer.md`](references/divergent-reviewer.md) |

   Pass each prompt as written, with the transcript path or digest where marked. Reviewers return findings in their reply.

   Then spawn one synthesizer, your strongest model, with [`references/synthesizer.md`](references/synthesizer.md) as written and each reviewer's full output inlined where marked. It spot-checks citations and returns an accepted / rejected / backlog list.

5. **Structural check.** Per **encode lessons in structure** (`principle-encode-lessons-in-structure`), move any accepted skill edit that a lint rule, script, metadata flag or runtime check would enforce more reliably out of the accepted list. If the check belongs in this repo and is cheap, add it to the guardrail candidates. Otherwise it goes to backlog.

6. **File backlog now.** File each backlog item without waiting, with the **create** operation in the [tickets playbook](../arkan-mode/playbooks/tickets.md), role `needs-triage`.

7. **Present.** Show the guardrail candidates in order of severity, then the synthesizer's full accepted / rejected / backlog output. Wait for the person's explicit approval. The person picks the subset and may redirect routings. If the person is not there, stop here.

8. **Apply what the person approved.** Guardrails go through the repo's normal flow. Follow each approved skill-edit row's routing exactly:

   - a trivial existing-skill edit (one bullet, a tightened sentence, a stale fact): make it directly;
   - a substantive existing-skill edit (a new section, a new table, more than ~10 lines): write it per `writing-for-agents`;
   - `tune description: <skill path>` (the skill exists but didn't trigger when it should have): rework its `description` and trigger phrases per `writing-for-agents`;
   - `new skill via writing-for-agents: <kebab-name>`: create it per `writing-for-agents`; don't invent the shape ad hoc.

   Ship the edits as one pull request through the repo's normal flow. Each edited skill keeps valid front matter (`name` and a quoted `description`).

9. **Summarize for the person.** A short list, no preamble:

   - guardrails and edits applied: the file, what changed, one line each;
   - new skills created: `<skill path>`, one line each (rare);
   - backlog filed: `<ticket>`, one line each;
   - dropped: one line per rejected finding, with the synthesizer's reason.

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
