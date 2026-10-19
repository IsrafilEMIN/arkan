# 07: readme that says run pre-setup first

**Role:** ready-for-agent
**Closed:** no
**Priority:** 14

**What to build:** a `README.md` at the repo root that tells a new user, in order: what arkan is, how to install it (ticket 04), and that they must run `pre-setup` first, before any other arkan skill, on the machine and in each repo.

**Blocked by:** 04, 06

- [ ] the install command and the `pre-setup` step are the first two steps, in that order, and the readme says plainly that `pre-setup` comes first
- [ ] it says what `pre-setup` asks (harnesses, tracker, and so on) and that a re-run is safe
- [ ] it shows the flow, and links `GLOSSARY.md` for the words
- [ ] each command in it was run once on a clean machine and works as written

## Comments

- 2026-10-18: a first `README.md` exists, with what arkan is, the flow and where the skills come from. this ticket now finishes its install and `pre-setup` steps.
- 2026-10-19, ticket 05: the first step is the one command from ticket 04 (clone arkan, run `skills/pre-setup/scripts/setup.sh`); the second is `/arkan:pre-setup` in each repo (in claude code; another harness runs the `pre-setup` skill by its own name). a re-run reports what is done and skips it.
