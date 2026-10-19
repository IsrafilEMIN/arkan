# Approvals

Who must approve a pull request before it merges, and which path merges it. The skills that open, verify and ship pull requests read this file.

## Merge path

A repo records one path here. `pre-setup` asks which path the repo uses and writes one exact line; the broker never reads this file.

`**Merge path:** <gate|broker>`

- `broker`: a broker on the person's machine merges the pull request. The repo installs no gate; arkan records `broker`.
- `gate`: `.github/workflows/arkan-merge.yml` merges the pull request, after `pre-setup`'s `ci-merge` apply.

With no line and no installed gate, `pre-setup` asks which path. An installed `.github/workflows/arkan-merge.yml` with no line is recognized as the `gate` path: shipping uses it, and the person may record the line later.

## Labels

Each pull request gets one label, set in ci, never by its author:

- `auto`: merges with no person once every check is green, both reviews (code and security) have no open finding, and the agent verifier posted `PASS` on the head commit.
- `manual`: merges only after the person posts `PASS` on the head commit.

Until the risk tier is installed (arkan ticket 42), every pull request is `manual`.

## Rules

- The person's `PASS` is an unmarked review on the head commit. The broker adds `<!-- arkan:verifier -->` to an agent's verdict; on a `manual` pull request, a marked `PASS` never substitutes for the person's.
- A pull request that touches a path in `docs/agents/sensitive-paths.md` is always `manual`.
- Trusted author: the repo owner only. A pull request from anyone else is always `manual`.
- An agent's `PASS` never counts as the person's. The person who directed the agent is the person who approves.
- A `PASS` covers one commit. A new push needs a new `PASS`.
- Start strict. Move a kind of change to `auto` only with evidence (the finding log, reverts).
