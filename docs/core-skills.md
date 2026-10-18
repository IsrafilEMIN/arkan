# arkan core skills: what each one does

status: proposal, waiting for kutluk's approval (2026-10-12). updated 2026-10-18: grill and plan are shaping steps that run before the task, and a person starts them; `arkan-mode` runs the task. whether these skills need merging at all is open (ticket `arkan-flow` 03). updated 2026-10-18 with the gaps in [review-gaps.md](review-gaps.md): `review`, `ship` and `learn` changed, `security-review` and `post-merge` added (named `post-merge`, because `skills/triage` is already matt's issue-triage skill).

each entry says what the skill does, when it starts, and which source skills it comes from. "it starts" means the agent can call it by itself when the situation fits. you can also type its name, for example `/debug`.

## the core (14 skills)

### 1. arkan-mode

**what it does.** the entry point for every task (see `GLOSSARY.md`: the smallest piece of work an agent can finish alone). it replaces pstack's `poteto-mode`. it first checks that the work is a task; if the work is still fuzzy or too big, it stops and names the shaping step to run (`grill` or `plan`). then it picks a playbook (a fixed list of steps for one kind of task), and calls the other skills when a step needs them. it also holds 24 short engineering rules ("principles"), such as "prove it works" and "fix the root cause, not the symptom". before the agent says "done", it must check the real result.

**it starts** at the beginning of any non-trivial task.

**playbooks inside it:** investigation (answer a question about the code), bug fix, feature, refactor, prototype, authoring a skill, autonomous run (work until a goal is met, without stopping), pause safely, session pickup, opening a pr, babysit, shipping.

**from:** pstack `poteto-mode` and its principles and playbooks, plus matt's `ask-matt` flow.

### 2. grill

**what it does.** interviews you about an idea until nothing is left unclear. it asks a few numbered questions per round, each with its recommended answer, so "yes" accepts the recommendation. it looks up facts in the code by itself and asks you only for decisions. as words get clear, it writes them into a `GLOSSARY.md`, and it writes a short decision record (an "adr") for hard-to-undo choices.

**it starts** before the task, when you start it: an idea or a feature is still fuzzy, or you say "grill me". it is a shaping step, so `arkan-mode` does not call it; it tells you to run it.

**from:** matt `grilling`, `grill-me`, `grill-with-docs`, `domain-modeling`.

### 3. plan

**what it does.** turns a talk or an idea into a spec (what to build and why) and then into small tickets. each ticket is a thin slice that works end to end and can be checked by itself. each ticket lists the tickets that must finish first. each ticket is a task: an agent can build, check and merge it alone. tickets go to the repo's issue tracker, which `pre-setup` sets (local files under `.scratch/<feature>/` work without any service).

**it starts** before the task, when you start it: the work is more than one task (more than one session or one pr). it is a shaping step, so `arkan-mode` does not call it; it tells you to run it.

**from:** matt `to-spec`, `to-tickets`, `wayfinder`, pstack `figure-it-out` and the multi-phase playbook.

### 4. build

**what it does.** builds a ticket or a feature. first it sketches the shape (types, function signatures, module edges) with empty bodies, then fills in the code against that sketch, test first where it can. if the sketch keeps fighting the code, it throws the sketch away and designs again. for a full plan, it can run several tickets in parallel with subagents (helper agents) and merge them on one branch.

**it starts** when code crosses a function boundary, or when a plan has tickets ready.

**from:** pstack `architect` and the feature playbook, matt `implement`, `implement-spec`.

### 5. tdd

**what it does.** test-driven development: write one failing test, write just enough code to pass it, repeat. it tests what a user of the code sees, not internal details. it rejects weak tests, for example a test that still passes when the code returns nothing. if a good test is too costly for a small bug fix, it uses the closest real check and says so.

**it starts** when you build a behavior or fix a bug that has a cheap test path.

**from:** matt `tdd`, pstack `tdd` and the "test behavior, not implementation" principle.

### 6. debug

**what it does.** fixes hard bugs in a strict order. first it builds one fast command that fails on this exact bug. then it shrinks the repro, writes 3 to 5 guesses about the cause, and tests each guess with logs or a debugger. then it writes a regression test, fixes the root cause, and removes all debug logs.

**it starts** when something is broken, flaky or slow.

**from:** matt `diagnosing-bugs`, pstack bug-fix playbook and "fix root causes".

### 7. review

**what it does.** reviews a diff before it ships. it runs in a fresh context (a subagent that did not write the code). it checks two things on their own: does the code follow the repo's standards, and does it do what the spec asked. then it asks "what else can this break?" and proves the one fact the change is safe because of by running real code. it reads the repo's `REVIEW.md` if there is one. it also deletes comments that only explain a workaround.

findings go through two steps:

- **find, then verify.** finders look for bugs in parallel. then a separate verifier tries to prove each finding wrong. only the findings that survive go on. style-only findings are dropped.
- **tag each finding.** `important` (blocks the pr), `nit` (optional) or `pre-existing` (the bug was there before this diff, so it does not block and it is not the author's fault). each finding names a `file:line` as evidence, not a guess from a name.

review must converge (reach an end):

- at most 3 rounds. after round 3, it stops and asks the author to rethink the approach.
- after the first round, it reviews only the new diff.
- it names the class of bug, so the author fixes every instance in one round, not one line per round.
- it never posts a finding again that it already posted.

it also sets the risk tier of the change from the diff, not from the author: `low` (docs, copy, additive work behind a flag), `medium` (normal product code), `high` (risky code). paths the repo lists as sensitive (ci workflows, installers, auth, billing) are never `low`. a second check asks if this change needs a person even when its tier says no; if yes, the tier goes up one. the tier tells `ship` how many people must approve (see node 7 in [flow.md](flow.md)). the repo host and the guard repo enforce it, not this skill.

**it starts** when a diff is ready, before a pr, and again on each new push to an open pr.

**from:** matt `code-review`, pstack `interrogate`, `blast-radius`, `no-comments`, and the claude code team's review flow (see [review-gaps.md](review-gaps.md)).

### 8. ship

**what it does.** opens the pr and drives it to merge-ready. it makes small ordered commits, writes a short pr body (why, what changed, risk tier, how it was checked, how to revert), then fixes ci failures, merge conflicts and review comments one by one. it answers every finding: it fixes it, or it resolves the thread with a one-line reason. an `important` or security finding that is still open means the pr is not ready. then it merges by risk tier: a `low` change auto-merges once ci and both reviews are green; `medium` waits for one person, `high` for two; a sensitive path or a ci workflow file always waits for a person. an agent's approval never takes the place of a person's, and a new push needs a new approval.

**it starts** when work is ready for a pr, or when you say "get this pr green".

**from:** matt `pr`, pstack opening-a-pr, babysit and shipping playbooks, and the claude code team's pr template (testing, risk, how to revert).

### 9. learn

**what it does.** after a session, or after you correct the agent, it finds the mistakes that repeat and makes them hard to repeat. it tries the strongest fix first: change the code structure, then add a type, then a lint rule whose error names the right fix, then a test, and only last a written rule. it proves each new check fails on a real past mistake. this is the dune idea in skill form.

when the reviewer keeps flagging the same thing, it moves that rule into the repo's `REVIEW.md` (or `CLAUDE.md`, or a lint rule). it keeps both files short.

**it starts** when you correct the agent, or when you say "learn" or "retro", or when `post-merge` finds a miss.

**from:** pstack `correct`, `reflect`, matt `retro`.

### 10. write

**what it does.** one writing standard for every text the agent writes: replies, docs, pr bodies, commit messages and skills. it uses simple english (ste rules), your lowercase style, and a list of ai habits to remove (filler, hype words, "not just x but y", and so on). it has a part for writing text that agents read, such as skills and `CLAUDE.md`.

**it starts** for any prose.

**from:** pstack `unslop`, `technical-writing`, matt `writing-for-agents`.

### 11. create-verification

**what it does.** makes a verification skill inside one repo (for example `.claude/skills/verify-chopper/`). that skill tells any agent how to start the real app, check it is healthy, use it the way a person does (browser, terminal or api calls), save proof (screenshots, output) and shut it down. it also writes a short feature map: one file per main feature, with how to reach it and what "it works" looks like. it runs the new skill once end to end before it calls it done.

**it starts** only when a person starts it (decided 2026-10-18). when a repo has no scripted way to prove that the app works, `arkan-mode` tells you, and does not start it by itself.

**from:** pstack `create-verification-skill`. this is the dune "verifier agent" idea.

### 12. maintain-verification

**what it does.** keeps that verification skill true as the app changes. it reads the code for each feature in the map, drives every feature once in the real app, and fixes the steps or the map where they are wrong. it makes at most one pr of proven corrections.

**it starts** when you ask, or on a schedule you choose.

**from:** pstack `maintain-verification-skill`.

### 13. security-review

**what it does.** a separate review pass that looks only for security problems: secrets in code, injection, unsafe input, wrong auth checks, risky changes to ci workflows and installers. it uses the same find-then-verify step and the same tags as `review`. an open finding blocks the pr until it is fixed or closed with a reason. if a later commit fixes it, the finding clears.

**it starts** when a diff is ready, beside `review`.

**from:** the claude code team's security review layer, and claude code's `/security-review` command.

### 14. post-merge

**what it does.** watches a change after it merges, and handles what went wrong. it checks the signals the repo has (ci on main, error logs, revert and incident reports). when a merged change breaks something, it fixes forward or reverts, whichever is faster to make safe. then it asks "which layer should have caught this?" and hands the answer to `learn`. it also saves each real incident or revert as a test case for the reviewer: the bad diff and the bug an expert confirmed. the cases live in the repo they came from (`.arkan/evals/review/`), not in arkan, because arkan is shared infra, not a project. when `review` or its prompts change, it runs the reviewer on all saved cases, and keeps the change only if the score did not drop.

**it starts** after a merge, when a change breaks something, or when you ask.

**from:** the claude code team's "fast detection, fast rollback" layer and their incident eval set.

## after the core

| skill | what it does |
|---|---|
| `explain` | answers "how does this work" and "why is it like this", and restates a reply in plain words. |
| `handoff` | saves the state of the work before you stop, so a fresh agent can continue. |
| `prototype` | throwaway code to answer a design question fast. |
| `research` | reads trusted sources on a topic and saves the findings as a file in the repo. |
