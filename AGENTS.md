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

A pull request merges through `.github/workflows/arkan-merge.yml`: once every check on the head commit is green (`check` runs `scripts/check.sh`), a `COMMENT` review that starts with `PASS` on that commit makes the workflow merge it. `arkan-risk` labels each pull request `auto` or `manual`; a `manual` one needs the owner's `PASS`. Until the vote is on (arkan ticket 42), every pull request is `manual`, so an agent never posts that `PASS` here, and never merges.
