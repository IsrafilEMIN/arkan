# arkan

## Purpose

This repo enhances agent skills and ships them as one bundle named "arkan".

## Agent skills

### Issue tracker

Issues live as local markdown files under `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one root `GLOSSARY.md` and `docs/adr/`. See `docs/agents/domain.md`.

### Board

`TODO.md` (the Tern board) shows one card per ticket; the details stay in the ticket. See the `## Board` section of `docs/agents/issue-tracker.md`.

Do not edit `TODO.md` by hand. Before each commit that touches `.scratch/`, run `scripts/build-board.sh` to write `TODO.md` from the tickets, then run `scripts/check-board.sh`; it must print `ok`. If `TODO.md` has a merge conflict, run `scripts/build-board.sh` again to fix it.
