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

Every ticket state change also updates its card in `TODO.md` (the Tern board), in the same branch and PR as the work. The change reaches `main` only after the PR checks pass and the merge is verified. See the `## Board` section of `docs/agents/issue-tracker.md`.

### Change log

Append to LOGS.md per change action: after every change, append a dated entry to `LOGS.md`.
