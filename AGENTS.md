# arkan

## Purpose

This repo is one bundle of agent skills named "arkan". It holds only the skills; it has no ci, no pipeline and no shared contract with another repo.

## Layout

- `skills/<name>/SKILL.md` is one skill. Extra files of a skill stay inside its folder and are linked from its `SKILL.md`.
- `skills/<name>/agents/openai.yaml` is the codex metadata of the skill. A new skill gets one too.
- `.claude-plugin/` makes the bundle a claude code plugin.

## Sources

A skill copied or adapted from another project gets a row in the `## where the skills come from` table of `README.md`. If that project's license asks for it, its copyright notice and license text go into `NOTICE`. When you delete a skill, remove it from that table.
