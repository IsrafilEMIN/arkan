# 14: repo host settings checked and offered by pre-setup

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
