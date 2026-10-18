# 12: one sensitive-path list per repo, set up by pre-setup

**What to build:** each repo has one list of sensitive paths (ci workflows, installers, auth, billing, and what the owner adds) with a floor tier per path. `review`, the tier check and the guard repo all read the same list.

**Blocked by:** 05

- [ ] `pre-setup` proposes a list from what it finds in the repo (workflow folders, install scripts, auth code), and the person edits it
- [ ] the list lives in one file, in a format a script and an agent can both read
- [ ] the tier check (ticket 11) and the review skill read it; nothing has its own copy
- [ ] proof: adding a path to the list changes the tier of a test pr with no other edit
