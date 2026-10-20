# Approvals

Who must approve a pull request before the repo's merge path lands it. The skills that open, verify and ship pull requests read this file.

**Merge path:** broker

arkan merges through the broker on the owner's machine. `ci/github/arkan-merge.yml` stays in arkan as the gate a consumer repo can install instead; arkan installs no gate of its own. A repo records the choice the same way: `**Merge path:** gate` or `**Merge path:** broker`. `pre-setup` reads the line as a local setup choice; the broker never reads this file.

## Labels

Each pull request gets one label, set in ci, never by its author:

- `auto`: merges with no person once every check is green, both reviews (code and security) have no open finding, and the agent verifier posted `PASS` on the head commit.
- `manual`: merges only after the person posts `PASS` on the head commit.

A pull request with no risk marker, or with a marker for an older head, is `manual`.

## Rules

- The person's `PASS` is a review on the head commit with no agent mark. The broker adds `<!-- arkan:verifier -->` to every verdict an agent posts, so an agent cannot post the person's verdict.
- A pull request that touches a path in `docs/agents/sensitive-paths.md` is always `manual`.
- Trusted author: the repo owner only. A pull request from anyone else is always `manual`.
- An agent's `PASS` never counts as the person's. The person who directed the agent is the person who approves.
- A `PASS` covers one commit. A new push needs a new `PASS`.
- Start strict. Move a kind of change to `auto` only with evidence (the finding log, reverts).
