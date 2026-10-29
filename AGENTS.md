# arkan

## Purpose

This repo is one bundle of agent skills named "arkan". It holds skills, plus `REFERENCE.md` and `docs/resources/`, which record where the skills come from.

## Layout

- `skills/<name>/SKILL.md` is one skill. Extra files of a skill stay inside its folder and are linked from its `SKILL.md`.
- `REFERENCE.md` lists the skill sources and the articles that shaped arkan.
- `docs/resources/<yyyy-mm-dd>-<slug>.md` is one file per article: its link, its core claim, the parts arkan owns with their status, and the parts it leaves to others. It does not copy the article text.

## Sources

A skill copied or adapted from another project gets a row in the `## skill sources` table of `REFERENCE.md`. If that project's license asks for it, its copyright notice and license text go into `NOTICE`. When you delete a skill, remove it from that table.

An article, blog post or other resource that shapes a skill gets a row in the `## articles` table of `REFERENCE.md` and a file in `docs/resources/`.

Before you change or add a skill, check `REFERENCE.md` for articles, blogs and resources on that topic, and read the matching `docs/resources/` file.
