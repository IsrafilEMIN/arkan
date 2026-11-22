---
name: opening-a-pr
description: "Shape the change into small commits and open a ready PR with a fixed title and body shape. Use at the end of any change that ships, for /skill:opening-a-pr, or \"open a PR\"."
---

# Opening a PR

Use at the end of every change that ships.

Work from a git worktree off trunk, and keep unrelated work out of it. Rebase into small, landable commits. Run `/skill:deslop` over the diff before commit.

Title: `type(scope): subject`, naming a real symbol when one carries the change. Body: a one-minute briefing under 40 lines with these `##` headings in order, dropping empty ones: `## Why`, `## What changed`, `## Scope`, `## Tradeoffs` (only rejected alternatives a reviewer would otherwise ask about), `## Blast Radius`, `## Verification`.

Stack follow-ups by base branch. Open PRs ready, with `gh pr create` without `--draft`. Opening a PR does not start a babysit.
