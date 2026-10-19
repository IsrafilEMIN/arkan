# Approvals

Who must approve a pull request before the merge gate (`.github/workflows/arkan-merge.yml`) merges it. The skills that open, verify and ship pull requests read this file.

## Labels

Each pull request gets one label, set in ci, never by its author:

- `auto`: merges with no person once every check is green, both reviews (code and security) have no open finding, and the agent verifier posted `PASS` on the head commit.
- `manual`: merges only after the person posts `PASS` on the head commit.

Until the risk tier is installed (arkan ticket 42), every pull request is `manual`.

## Rules

- A pull request that touches a path in `docs/agents/sensitive-paths.md` is always `manual`.
- Trusted author: the repo owner only. A pull request from anyone else is always `manual`.
- An agent's `PASS` never counts as the person's. The person who directed the agent is the person who approves.
- A `PASS` covers one commit. A new push needs a new `PASS`.
- Start strict. Move a kind of change to `auto` only with evidence (the finding log, reverts).
