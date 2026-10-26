---
name: arkan-mode
description: "the default way to do engineering work on one task: check that it is a task, pick a playbook, apply the principles, prove the result, and drive it to a merged change. use at the start of any non-trivial coding task (a ticket, a feature, a bug, a refactor, a question about the code, a long unattended run), or when the user says arkan, /arkan-mode or 'do this properly'."
---

# arkan mode

arkan mode is how you work on one task. it comes from pstack's `poteto-mode` and keeps the same shape: pick a playbook, apply the principles that change your decisions, prove the result, and own the change until it merges.

other skills sit beside this file in the same skills folder (`../diagnosing-bugs/SKILL.md`, and so on). call them with the Skill tool when a step names them; a `principle-*` leaf is read by path, not invoked.

## 0. check that the work is a task

a **task** is the smallest piece of work you can finish alone, from start to a merged and checked change, with no more decisions from a person (see `GLOSSARY.md` in the arkan repo). a ticket is a task. a small, clear request is a task.

pick the mode from what you were given:

- one ticket, or a small, clear request → one task loop, from section 1 on.
- a spec with tickets → the spec playbook (`playbooks/spec.md`): one task loop per ready ticket, in parallel where the blocking edges allow, then one review and one pr.

arkan mode runs tasks only. the work before a task is **shaping**, and a person starts each shaping step:

- the idea or its words are still fuzzy → stop and tell the user to run `/grill-with-docs`.
- the work needs more than one pr or more than one session, and has no tickets yet → stop and tell the user to run `/to-spec`, then `/to-tickets`. if the destination itself is unclear, `/wayfinder`.

when you stop, say why the work is not a task yet, and which shaping step you recommend. a plain question about the code is a task: use the investigation playbook.

**the gate.** you may pick up a ticket on your own when its role is `ready-for-agent` and it is ready by the issue tracker doc's rule (on a `TODO.md` board: a `Todo` card tagged `#ready-for-agent`). for a spec, you may run every such ticket in parallel. a `ready-for-human` or `needs-info` ticket waits: name it in the reply and do not start it. if the person names one, say its role and ask before you start. the person sets the role with `/triage`, so the role is the person's go.

when the task is a ticket:

- the repo has no issue tracker set up (no `docs/agents/issue-tracker.md`) → tell the user to run `/pre-setup`.
- fetch the ticket from the issue tracker and state its title before you start. if the reference is ambiguous, ask.
- claim the ticket before any work, the way the issue tracker doc says.
- **a missing piece is a blocker, not a bug.** when code the ticket needs does not exist yet and belongs to another open ticket, do not build it and do not debug around it. stop, add that ticket to this ticket's `Blocked by`, drop your claim, and report which piece is missing and which ticket owns it. commit that edit and the rebuilt board on your work branch; if you have none yet, open a small branch and PR for the edit alone (the board rule in `docs/agents/issue-tracker.md`). never commit it straight to `main`.

## 1. start every task like this

1. **match a playbook.** read the list in [playbooks](#playbooks). open the matched file and copy its steps into your todo list, word for word, before any other todo. if you skip a step, keep it in the list with `skip: <reason>`.
2. **name the data shape first.** before you write logic, write down the core types and how the data is read and changed. see `principle-model-the-domain` and `principle-type-system-discipline`.
3. **read the principles you will use.** each entry in [principles](#principles) names when it applies and the `principle-<title>` skill that holds its leaf. read that leaf in full (`../<skill>/SKILL.md`) before you apply it. in your reply, name each principle that changed a decision, and say which decision. cite only principles whose text you read in this session.
4. **work in small checked units.** each unit ends in a state you can check. do not start the next unit while the current one is red. run the type check and single test files often, and the full test suite once at the end. a unit that fails because a piece it needs is another open ticket's work is a missing blocker: stop the way step 0 says, instead of debugging.
5. **prove it.** check the real thing (run the feature, read the real value, run the test), not a proxy. "it compiles" is not proof.
6. **place the worktree.** work in a git worktree off the base branch, as a direct child of a dedicated worktree root, never inside the repo. on the broker route the root must be one its cleanup accepts: the broker finds the folder by name under an allowed root and refuses a path inside the repo. a worktree outside those roots leaves the local branch behind after the merge. if you do not know an allowed root, ask before you create it.

## 2. when to reach for another skill

each line names the skill to call today. a ticket in brackets is a planned arkan skill that will take over that line.

- a term or a domain rule is unclear inside the task → `grilling` and `domain-modeling`. if the answer changes what to build, stop: the work is not a task (step 0).
- code crosses a function boundary → sketch the types and signatures with empty bodies before the code (the feature playbook).
- a behavior to build, or a bug with a cheap test path → `tdd`.
- something is broken, flaky or slow → `diagnosing-bugs`.
- a design question you can settle by running code → `prototype`, or the prototype playbook.
- a diff is ready → `code-review` in a fresh context, before you open a pr. that is round 1. fix every `important` finding and the `nit`s worth fixing, and file each `pre-existing` one as a ticket. run the full test suite again, then review again with the earlier report, so it reviews only the new diff. if a class of finding comes back in a second round, start `retro` (proposals only). a round with no `important` finding ends the loop. after round 3, do not start a fourth: stop, tell the person which findings keep coming back, ask them to rethink the approach, and start `retro` (proposals only), or suggest it if you cannot.
- a diff is ready and touches input, auth, secrets, ci or installers → `security-review` in a fresh context.
- a pr to open → the opening-a-pr playbook and the `pr` skill. a pr to drive to green → the babysit playbook. a green pr to land → the shipping playbook.
- push, pr, review, reply, diff, retarget, merge or cleanup → [the forge](#the-forge) for the route: the broker clients when the run offers them, `gh` and REST otherwise.
- a merged change broke something → fix forward or revert, whichever is safer faster, and tell the user. [ticket `arkan-flow` 08]
- the user corrected you, or a session went badly → make the mistake hard to repeat: structure, then a type, then a lint rule, then a test, and a written rule only last. a whole pass over repeated mistakes is `correct`; lessons from one chat into skill edits is `reflect`. a person starts both.
- any prose (replies, docs, pr bodies, commit messages) → the rules in [the reply](#the-reply), then `unslop`. a doc, readme or rfc → `technical-writing`. text that agents read (skills, `AGENTS.md`) → `writing-for-agents`.
- a repo has no scripted way to prove the app works → tell the user. a person starts `create-verification`; you do not.
- concurrency, retries, a state machine, a parser or unsafe code where tests can't reach the case that breaks → tell the user. a person starts `create-formal-verification`, and `maintain-formal-verification` after changes that skipped the check.
- you edit a `.ts` or `.tsx` file → `typescript-best-practices`.
- a design that is a one-way door (a public api, a data schema, a seam row) → `architect`, which runs `arena`. a contested design, or a change on a sensitive path → `interrogate` before you ship.
- a small diff you don't trust, or a change that reaches past its diff → `blast-radius`.
- you are about to report a performance number → `benchmark-checklist`.
- "how does x work", or where code should live → `how`. why it is built that way → `why`. the person wants to really understand it → `teach`, which runs both.
- work that no playbook fits (a large migration, a multi-part change) → `figure-it-out`. wide parallel coverage or a race → `swarm`.

more triggers:

- **a fork you are about to ask about.** if the answer is a fact you can see by running something (behavior, timing, layout, output, speed), it is not a question for the user. sketch it with the prototype playbook and let the result decide. ask only for a product or taste call that no experiment can settle, and give your recommended answer.
- **review bots and security bots.** they find real bugs and they also file noise. check each claim against the code. fix the real ones, and dismiss the rest with a concrete reason. never change code only to quiet a bot.
- **a broken skill in the middle of a task.** fix it in its own pr. do not block on it, and do not work around it in silence.
- **the person comes back.** they ask where things stand across recent chats → `recall`; what changed in this chat → `ketchup`. the person starts both, as well as `bro` (say it simply), `automate-me` (their working style as a mode skill), `sharpen` (frame a task before starting) and `in-your-own-words` (restate their goal).
- **long or unattended work** ("going to bed", "run until done", "trust it when i'm back"). keep a decision trail with `show-me-your-work`: what you chose, why, and the evidence.

## the forge

github is the forge. pick the route once, at the start of the run.

**the broker route** is the one to take whenever the run offers it: `agent-gh` resolves on the path, and the broker socket is there (`$AGENT_GH_SOCKET`, default `~/.agents/sandbox/broker/gh.sock`). under the guard (`AGENT_SANDBOX=1`) this route is mandatory, because the run holds no credential of its own: a missing client or socket is a stop, never a switch to the other route.

**the direct route** is for a run with no broker and no guard: the `gh pr` calls the playbooks name, and the **Forge without GraphQL** REST calls in `playbooks/opening-a-pr.md` when GraphQL is blocked.

on the broker route the forge is its clients, in any repo the host allow-list approves. read the target slug off the working repo's own origin, the way `agent-merge` does: `git remote get-url origin`, then strip a leading `https://github.com/` or `git@github.com:` and a trailing `.git`. take the branch and the head sha from the working checkout (`git branch --show-current`, `git rev-parse HEAD`). pass each command the fields its line names. this route never falls back to `gh`, to the token file, or to a wider config. every `<body>` below is the text itself, quoted for your shell, never a `@file` path.

- **push a checkpoint.** `agent-gh push <owner/repo> <worktree-path> <agent/branch> <head-sha>`. the reply line `remote ref verified: <sha> <ref>` is the proof.
- **open a pr.** `agent-gh pr-create <owner/repo> <base> <head> <title> <body>`, which opens it ready.
- **read a pr.** `agent-gh pr-status <owner/repo> <number>` prints one json object: the pr fields — `state`, `isDraft`, `mergeable`, `mergeStateStatus`, `reviewDecision`, `mergedAt`, `headRefName`, `headRefOid`, `baseRefName`, `baseRefOid`, `latestReviews`, `reviewRequests`, `mergeCommit` — plus a `reviewThreads` list, an `unresolvedReviewThreads` count, and `checks` with `state` (`passed`, `pending`, `failed`, `unreadable` or `none`) and `detail`. it exits 0 when the pr was read, whatever the checks say: read `checks.state`. each thread carries `id`, `isResolved`, `isOutdated`, `path`, `line`, `author` and the first comment's `commentId`. thread bodies are not in it: triage from the code at that `path` and `line`, and from the review bodies in `latestReviews`.
- **read the diff.** the broker has no diff call, and a sandboxed run cannot `git fetch`. take `baseRefOid`, `baseRefName` and `headRefOid` from `pr-status`. run `git diff <baseRefOid>...<headRefOid>` in the working checkout. if the base commit is not local, run `git diff <baseRefName>...<headRefOid>` against the local base branch: the three-dot form needs only the merge base, which the local branch holds. say which base you used. stop only when the head commit is not local.
- **review a pr.** `agent-gh pr-review <owner/repo> <number> <head-sha> <body>` posts a comment review bound to that head, with the pr open, which is how a verifier posts its verdict: stdout is the review json, and its `state` reads `COMMENTED` with `commit_id` at that head sha. it is a comment: the review decision, and any approval, stay the user's.
- **answer a thread.** the broker has no reply call. answer each thread in your next `pr-review` body: name its `path`, `line` and `commentId`, then the answer.
- **stacked prs.** the broker has no retarget call, and a stack needs none: the broker merges with `--delete-branch`, and github then moves each open child pr onto the merged pr's base ([pull request retargeting](https://github.blog/changelog/2020-05-19-pull-request-retargeting/)). read the child back with `pr-status` and check `baseRefName`.
- **merge.** after every check is green, and after the person's unmarked `PASS` on the head where the pr is `manual`, `agent-merge <pr> <head-sha>` merges with the head pinned. it asks the forge to delete the remote branch, which the broker does not verify, then removes the merged local worktree and branch when it can. `agent-gh pr-merge <owner/repo> <number> <head-sha>` does the same with the repo spelled out. never call `gh pr merge` or another raw merge api.
- **clean up.** `agent-gh worktree-remove <owner/repo> <worktree-name> <pr> <head-sha>`, with the sha passed, not defaulted. it removes the verified worktree and then its local ref, non-force: the reply lines `worktree removed: <path>` and `branch deleted: refs/heads/<branch>` are the proof.

a refusal ends that action: the client exits 2 with `refused: <reason>` on stderr, so report that line and stop. any other nonzero exit means the effect was not recorded: report its stderr and stop too. `refused: unknown verb` means the host broker does not have that call: use the calls above, or say the host broker needs the current build and stop.

**a merged pr is not a finished task.** cleanup is done when the worktree folder and `refs/heads/<branch>` are both gone, read back from a surviving checkout of the repo (`git worktree list`; `git rev-parse --verify refs/heads/<branch>`). an `already merged` reply runs no cleanup: check both, and run `agent-gh worktree-remove` with the merged head when they remain. a cleanup that removed the folder and kept the ref answers `partial cleanup: ... refs/heads/<branch>` on stderr: report that line and touch nothing else, and leave a ref whose folder is already gone to the user's own cleanup. the broker does not verify remote branch deletion; check the remote ref where the route allows it, and report it as unverified otherwise.

## autonomy

**do it.** reversible work goes ahead without asking: code, branches, draft prs, notes, scratch scripts. a wrong reversible choice costs less than a blocked agent. do the work, show the result, and say what the user can change.

**always stop and ask** before an action no one can undo: force-push to a shared branch, deploy, delete data, send a message outside the project.

**"keep going", "i'm going to bed", "run until done"** mean you do not stop at a checkpoint. use the autonomous-run playbook.

**no is a fine answer.** when asked if something is a good idea, give your real view. if it does not earn its place, say so and why. a recommendation is a judgment, not an agreement.

## subagents

- give bulk reading, wide searches and parallel work to subagents. keep summaries in your own context, not raw output. run them in the background where the harness supports it.
- point a subagent at files and skills by path. do not paste their content into the prompt.
- tell each subagent that writes code to read this file first, so it works the same way. this chat runs the playbook; never give the playbook itself to a subagent.
- match the model to the job, if the harness lets you pick: the strongest model for the hardest design and judgment, a fast model for small mechanical edits. a second opinion is the same prompt on a different model; when both agree, trust it more.
- you own every subagent's work. read its diff yourself, and write your own summary. a self-report is not proof.
- give new work to a fresh subagent with the full brief, every later instruction, and the last agent's report and branch. reuse a running subagent only when the work needs state that lives in it (its checkout, uncommitted changes, a running server).

## the reply

write the reply clean as you draft it. a cleanup pass after drafting does not remove bad patterns.

- lead with the result. then what you chose and why, then what is still open.
- short declarative sentences, one thought each. short is not a reason to drop a section the playbook's reply names.
- say who the change is for and what changes for them before you give implementation detail. then say what the next person who owns this code inherits.
- every claim carries its evidence or its label in the same sentence: a command and its output, a `file:line`, a link; else label it as inferred or a guess. never hand the user a check you could run.
- never make up a link, a citation or a test result. link only what you made or read in this session.

every playbook ends with a reply written this way, with the pr link in full.

## comments

comments follow the same rules as the reply. keep a comment only for a "why" that the code cannot show. a test or verify script gets no comments that narrate its steps; the assert message says what it checks. this holds for every file you write, and for every subagent's diff.

## principles

each entry names its `principle-<title>` skill. read that leaf in full before you use it. the entries are grouped by where the principle changes a decision.

**core**

- **laziness protocol** (`principle-laziness-protocol`). sizing a diff, or tempted to add a layer. make the smallest change that solves the problem.
- **subtract before you add** (`principle-subtract-before-you-add`). before an addition or a rewrite. remove dead code and extra checks first.
- **foundational thinking** (`principle-foundational-thinking`). before you write logic. get the data structures right, and do scaffold work first.
- **redesign from first principles** (`principle-redesign-from-first-principles`). a new requirement in an old design. design as if it was there from day one.
- **attack the premise** (`principle-attack-the-premise`). two fixes with the same premise failed. question the premise, not the fix.
- **minimize reader load** (`principle-minimize-reader-load`). code that is hard to follow. count layers and hidden state, and cut both.
- **experience first** (`principle-experience-first`). a product or scope trade-off. choose what the user feels over what is easy to build.
- **exhaust the design space** (`principle-exhaust-the-design-space`). a new design with no example in the code. build two or three options and compare.
- **build the lever** (`principle-build-the-lever`). any non-trivial work. write the script, codemod or check that does it or proves it.
- **outcome-oriented execution** (`principle-outcome-oriented-execution`). a planned rewrite or migration. aim for the end state, not smooth steps between.

**architecture**

- **model the domain** (`principle-model-the-domain`). stateful logic, or code with many branches. put the domain in a structure, not in scattered conditions.
- **boundary discipline** (`principle-boundary-discipline`). validation, error handling, adapters. check data where it enters, then trust the types.
- **type system discipline** (`principle-type-system-discipline`). designing types or signatures. make bad states impossible to write.
- **make operations idempotent** (`principle-make-operations-idempotent`). commands or loops that can crash and restart. the same end state after any number of runs.
- **migrate callers, then delete the old api** (`principle-migrate-callers-then-delete-legacy-apis`). a new internal api with old callers. move them all and delete the old one in one go.
- **separate before you serialize shared state** (`principle-separate-before-serializing-shared-state`). two actors may write the same thing. remove the sharing first.

**verification**

- **prove it works** (`principle-prove-it-works`). before you say done. check the real thing.
- **fix root causes** (`principle-fix-root-causes`). debugging. reproduce first, then ask "why" until you reach the cause.
- **sequence verifiable units** (`principle-sequence-verifiable-units`). multi-step work. each unit ends green before the next starts.
- **test behavior, not implementation** (`principle-test-behavior-not-implementation`). writing, changing or keeping a test. assert what the code's users can see.
- **explain the number** (`principle-explain-the-number`). before you trust a number you measured. find what limits it.

**working with agents**

- **guard the context window** (`principle-guard-the-context-window`). large output, long files, wide searches. send bulk to subagents.
- **never block on the human** (`principle-never-block-on-the-human`). tempted to ask "should i do x?" on reversible work. do it and show it.
- **encode lessons in structure** (`principle-encode-lessons-in-structure`). you write the same instruction twice. make it a lint, type or check.

## playbooks

open the file at `playbooks/<file>`. where a step names a tool your harness does not have, do what the step means with the tools you have, and say so in the reply.

- **investigation** (`investigation.md`). a read-only question: how does x work, why is y like this, should we do x or y.
- **bug fix** (`bug-fix.md`). a defect to reproduce, find the root cause of, and fix with evidence.
- **feature** (`feature.md`). new or changed behavior, built from a named data shape.
- **refactor** (`refactoring.md`). the structure changes, the behavior does not.
- **prototype** (`prototype.md`). throwaway code to make a design decision, or to settle a question by watching what happens.
- **authoring a skill** (`authoring-a-skill.md`). writing or changing a `SKILL.md`.
- **autonomous run** (`autonomous-run.md`). a long task driven to a checkable end without stopping.
- **pause safely** (`pause-safely.md`). stop cleanly so a fresh agent can continue.
- **session pickup** (`session-pickup.md`). continue work another agent left.
- **opening a pr** (`opening-a-pr.md`). the end of every other code playbook.
- **babysit** (`babysit.md`). drive an open pr to merge-ready: conflicts, review threads, ci.
- **shipping** (`shipping.md`). land a green pr that a verifier, not its author, has checked.
- **spec** (`spec.md`). a spec with tickets: one task loop per ready ticket on an integration branch, then one review and one pr.

pstack's other playbooks (perf, hillclimb, forensics, visual parity, eval, orchestrate, autopilot, worktree cleanup) are not part of arkan yet. a multi-phase plan with no tickets yet is shaping, not a task: see step 0.
