# review and ci: parked

**status:** parked by the owner on 2026-10-18. nothing here is built. it needs a ci review runner, a guard repo and repo host settings, which live outside this repo. when it comes back, split it into tickets again with `/to-tickets`.

these were tickets `arkan-flow` 09, 10, 11, 12, 13, 14, 16 and 18. their text is below as it was, one section each. a "blocked by" line that names one of these numbers now points at a section of this file.

## 09: run review on each pr push, outside the author's session

**What to build:** on every push to an open pr, a ci job starts a fresh agent that runs the review skill (code and security lenses) on the diff and posts its findings, so the review does not depend on the author's own session.

**Blocked by:** 03

what "runner" means: before the pr (node 4), the author's agent runs review in a subagent. that is the author checking its own work. at node 6, review must run again on each push, started by something the author does not control. that something is the runner: a ci job.

- [ ] a ci workflow (written or proposed by `pre-setup`, per ticket 05) runs on pr open and on each push
- [ ] it starts a fresh agent with the review skill and posts findings as pr comments with `file:line`
- [ ] it reports a required status check, so a pr with an open `important` or security finding cannot merge
- [ ] it works on prs from forks without leaking secrets, or skips them and says so
- [ ] proof: a push to a test pr gets review comments with no session open

## 10: store the review round count in the pr

**What to build:** the reviewer knows which round it is on, which commit it last reviewed, and which findings it already posted, even in a fresh session. on round 4 it stops and asks the author to step back.

**Blocked by:** 09

proposal: one review comment per pr that the reviewer edits in place (a "sticky" comment). it holds a hidden marker, for example:

`<!-- arkan:code-review round=2 head=<sha> findings=<id>:<state>,... -->`

- **round** goes up by one only when the head commit changed since the last review.
- **head** is the last reviewed commit; the next round reviews only `git diff <head>..<new head>`.
- **findings** holds an id per finding (from the bug class, the file and the symbol, not the line number, so a moved line keeps its id) and its state (open, fixed, dismissed). a finding whose id is already there is never posted again.
- on round 4: post the "step back and rethink the approach" message, add a label such as `arkan:rethink`, and stop reviewing until a person removes the label.

the same marker feeds the noise log (ticket 18). the pr is the only place that every session can read, so no extra store is needed.

- [ ] the reviewer reads and writes the marker on each run
- [ ] re-review covers only the new diff
- [ ] a finding is never posted twice
- [ ] proof: a fourth round on a test pr gets the "step back" message and the label

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

## 18: log how each review finding ends

**What to build:** for each finding the reviewer posts, the repo keeps how it ended: fixed, wrong, intended, or did not matter. the owner can see the noise rate per repo and per tag, and a change to the reviewer is judged against it.

**Blocked by:** 03

- [ ] each finding's end state is recorded (the round marker from ticket 10 is the first place to try)
- [ ] a short report gives the noise rate per tag (`important`, `nit`, `pre-existing`)
- [ ] `retro` reads the report when it changes `REVIEW.md` or the reviewer prompt
