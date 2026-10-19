# arkan

## Purpose

This repo enhances agent skills and ships them as one bundle named "arkan".

## Seam

arkan and underground meet at six interfaces, one owner each. See `docs/seam.md`. A string or file the other repo reads becomes a row there first. If your change touches a seam row, update both repos in the same change.

## Agent skills

### Issue tracker

Issues live as local markdown files under `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one root `GLOSSARY.md` and `docs/adr/`. See `docs/agents/domain.md`.

### Board

`TODO.md` (the Tern board) shows one card per ticket; the details stay in the ticket. See the `## Board` section of `docs/agents/issue-tracker.md`.

Do not edit `TODO.md` by hand. Before you commit a change under `.scratch/`, run `scripts/board.sh build` to write `TODO.md` from the tickets, then run `scripts/board.sh check`; it must print `ok`. If `TODO.md` has a merge conflict, run `scripts/board.sh build` again to fix it.

### Approvals

Pull requests are `auto` or `manual`; the person approves `manual` ones. See `docs/agents/approvals.md` and `docs/agents/sensitive-paths.md`.

### Review

What the reviewer cares about in this repo. See `REVIEW.md`.

### Merging

A pull request merges through the broker: once every check on the head commit is green (`check` runs `scripts/check.sh`), a `COMMENT` review that starts with `PASS` on that commit lets the broker merge it. `arkan-risk` labels each pull request `auto` or `manual`; a `manual` one needs the owner's unmarked `PASS`, because the broker adds its mark to every verdict an agent posts. Until the vote is on (arkan ticket 42), every pull request is `manual`, so an agent never posts that `PASS` here. Where the owner's broker merge loop is deployed, it lands the pull request; otherwise the agent runs `agent-merge <pr> <sha>` with the head pinned after the owner's `PASS`. A consumer repo may install `ci/github/arkan-merge.yml` instead and merge through that gate under the same rule. No session calls `gh pr merge` or another raw merge api.
