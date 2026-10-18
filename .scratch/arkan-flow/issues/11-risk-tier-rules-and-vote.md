# 11: risk tier from fixed rules and a vote of classifiers

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
