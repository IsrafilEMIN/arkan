# review and ci, parked (was 11, 12, 13, 14, 16)

**Closed:** no
**Priority:** 17

**status:** parked by the owner on 2026-10-18. nothing here is built. it needs a ci review runner, a guard repo and repo host settings, which live outside this repo. when it comes back, split it into tickets again with `/to-tickets`.

2026-10-19, ticket 05: the sensitive-path list (12), the host settings (14) and the approval rule (16, now two fixed labels) move into `pre-setup` (ticket 41). the risk tier (11) is ticket 42, with two labels, `auto` and `manual`. protecting the review rules (13) splits: codeowners goes to `pre-setup`, and the guard half to underground. the sections below stay as history.

these were tickets `arkan-flow` 09, 10, 11, 12, 13, 14, 16 and 18. on 2026-10-18 the owner took 09, 10 and 18 out of the park as tickets 30, 31 and 32; their sections are removed here. a line below that names 09 or 10 now points at ticket 30 or 31. their text is below as it was, one section each. a "blocked by" line that names one of these numbers now points at a section of this file.



## 11: risk tier from fixed rules and a vote of classifiers

**What to build:** each pr gets a risk tier (`low`, `medium`, `high`) that the author cannot pick. critical paths get a fixed tier by rule; the rest is judged by model classifiers that are not the author, voting, and tested on an eval set.

**Blocked by:** 09, 12

proposal:

1. **rules first.** each path on the sensitive-path list (ticket 12) has a floor tier (for example ci workflows and installers: always a person). a rule can raise a tier; nothing can lower it.
2. **vote.** for the rest, 3 classifier runs in fresh contexts (different models where the harness allows), each returns a tier and one line of reason. take the majority; on a three-way split, take the highest.
3. **second check.** one more run asks "does this need a person even though the tier says no?". yes raises the tier by one.
4. **in ci only.** the vote runs in the runner (ticket 09), never in the author's session. the author's own proposal (node 4) is only a hint.
5. **eval set.** labelled past prs per repo. a change to the classifier's prompt is kept only if it misses no `high` case it caught before.

- [ ] the tier is set in ci and shown on the pr (a label and the review comment)
- [ ] a test pr that touches a sensitive path but claims `low` still waits for a person
- [ ] the classifier prompt and its eval set exist, and the eval runs on each prompt change

## 12: one sensitive-path list per repo, set up by pre-setup

**What to build:** each repo has one list of sensitive paths (ci workflows, installers, auth, billing, and what the owner adds) with a floor tier per path. `review`, the tier check and the guard repo all read the same list.

**Blocked by:** 05

- [ ] `pre-setup` proposes a list from what it finds in the repo (workflow folders, install scripts, auth code), and the person edits it
- [ ] the list lives in one file, in a format a script and an agent can both read
- [ ] the tier check (ticket 11) and the review skill read it; nothing has its own copy
- [ ] proof: adding a path to the list changes the tier of a test pr with no other edit

## 13: protect the review rules from the agent

**What to build:** the agent cannot weaken its own reviewer. `REVIEW.md`, the eval cases, the sensitive-path list and the ci workflow files can change only with a person's approval.

**Blocked by:** 05, 12

- [ ] these files are on the sensitive-path list with the floor "always a person"
- [ ] `pre-setup` sets codeowners (or the host's equivalent) for them, after the person agrees
- [ ] the guard repo denies or flags an agent's direct edit to them, if the guard repo can see it
- [ ] proof: an agent's pr that edits `REVIEW.md` waits for a person, whatever its tier

## 14: repo host settings checked and offered by pre-setup

**What to build:** `pre-setup` checks the repo host settings that the flow needs, reports which are off, and offers to turn each one on, one at a time, after it shows the exact change.

**Blocked by:** 05

proposal for github (check each against github's docs when built; some depend on the plan and on whether the repo is owned by a person or an org):

- protect `main`: changes only through a pr; no force-push; required status checks (ci and the review runner from ticket 09).
- dismiss an approval when a new commit is pushed (an approval covers one commit).
- require a code owner's review for the sensitive paths (codeowners made from ticket 12's list).
- allow auto-merge, so a `low` pr can merge itself once green.
- merge queue, where the plan allows it; else the flow says main is checked again after merge (ticket 08).
- flags are per project, not a host setting; arkan only asks for them in the pr body.

a problem to solve here: on github, a pr's author cannot approve their own pr. if the agent opens prs as the owner's account, the owner can never approve them. options: the agent works as a bot or app account, or the owner merges by hand without an approval. ticket 16 needs the same answer.

- [ ] pre-setup reports each setting as on, off, or not available on this plan
- [ ] it changes a setting only after the person says yes to that setting
- [ ] proof: a push after approval removes the approval; a `low` test pr merges by itself; a `medium` one does not

## 16: approval rule for high-tier prs in a repo with one person

**What to build:** `pre-setup` asks how many people can approve prs in this repo, and records a rule for `high` that the repo can meet.

**Blocked by:** 05

options to offer when there is one person (recommended first):

1. **you plus a wait plus an outside check.** you approve, the pr waits a fixed time (for example 24 hours), and a fresh verifier agent that did not write the code runs the change the way a user would and posts a pass (pstack's shipping playbook does this).
2. **you plus one named outside reviewer** for `high` paths only.
3. **no auto path for `high`.** you merge it by hand after your own review.

- [ ] pre-setup asks the question and records the answer where ticket 05 decides
- [ ] the approval step (node 7) reads the recorded rule
- [ ] the github self-approval limit from ticket 14 is handled
