# arkan

## Purpose

This repo is one bundle of agent skills named "arkan". It holds skills, plus `NOTICE` and `docs/resources/`, which record where the skills come from.

## Layout

- `skills/<name>/SKILL.md` is one skill. Extra files of a skill stay inside its folder and are linked from its `SKILL.md`.
- `NOTICE` lists each project arkan copies from, the skills that come from it, and its copyright notice and license text.
- `docs/resources/<yyyy-mm-dd>-<slug>.md` is one file per article: its link, its core claim, the parts arkan owns with their status, and the parts it leaves to others. It does not copy the article text.

## Sources

A skill copied or adapted from another project gets named in that project's entry in `NOTICE`, with the commit it came from. If that project's license asks for it, its copyright notice and license text go into `NOTICE` too. When you delete a skill, remove it from that entry.

An article, blog post or other resource that shapes a skill gets a file in `docs/resources/`.

Before you change or add a skill, check `docs/resources/` for articles, blogs and resources on that topic, and read the matching file.
