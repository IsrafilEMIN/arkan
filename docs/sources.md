# sources

this file maps what arkan takes from each source. it is step 1 of the v0.1 plan.

read on 2026-10-12:

- **pstack** by lauren tan (poteto). `cursor/plugins/pstack`, version 0.15.21. mit license. 52 skills (24 of them are principles), 23 playbooks, 2 agents.
- **skills** by matt pocock. `mattpocock/skills`, main branch. mit license. 27 main skills, plus 11 in misc and in-progress.
- **dune** by lauren tan. no public code. only talks, posts and write-ups by other people (see [dune](#dune)).

both repos use the mit license. when arkan copies text from them, arkan must keep their copyright notice. step 2 adds a `NOTICE` file for this.

## the idea from each source

**matt pocock: small skills that you compose.** each skill does one job. a router (`ask-matt`) shows the main flow: grill the idea, write a spec, split it into tickets, build with tdd, review, retro. he does not own your process. you can read and change each skill in minutes.

**pstack: one mode that holds the rigor.** `poteto-mode` is the entry point. it reads the task, picks a playbook (bug fix, feature, refactor, and so on), and calls the other skills when a step needs them. 24 short "principle" skills hold the engineering judgment (prove it works, fix root causes, subtract before you add). it also cares a lot about prose: `unslop` removes ai tells, and `technical-writing` uses ste rules (the same simple-english standard you use).

**dune: make the repo itself safe for agents.** skills tell an agent what to do. dune changes the repo so the wrong thing is hard to do. see below.

## dune

there is no dune code or official doc to read. what follows is secondhand, from write-ups of her talk and her posts, so treat each point as a claim, not a fact:

- the shortcut is the correct path. the repo is built so that the easiest change is also the right one.
- each feature lives in its own folder. there is one supported way to do each thing. lint rules reject the other ways.
- verifier agents open the real app, click around like a person, and look for regressions. because of this, she says her agents now merge their own prs.
- one critic notes that navigation docs go stale fast and then confuse agents. so structure and checks beat docs.

the pstack skills that carry this idea are `correct` (turn a repeated mistake into a check), `create-verification-skill` and `maintain-verification-skill` (a script that drives the real app). matt's `retro`, `improve-codebase-architecture` and `setup-ts-deep-modules` point the same way.

**so arkan has two layers:** skills that live in your user folder (how the agent works), and a per-repo setup (how the repo protects itself). v0.1 builds the first layer and one piece of the second (verification). if you have a link to the talk or your own notes on dune, add them here.

sources for this section: [ratstack.sh: dune, trust, and agent skills](https://ratstack.sh/lore/poteto-lauren-tan-2500-prs-dune), [redreamality.com: trust first, then parallel](https://redreamality.com/blog/lauren-tan-poteto-trust-before-parallel/), [tenten.co: pstack verification](https://developer.tenten.co/pstack-verification-agent-merge), [lauren on x](https://x.com/poteto/status/2087244771849089270), [matt pocock on x](https://x.com/mattpocockuk/status/2103431302527508886), [noahdgrant/nightshift #213](https://github.com/noahdgrant/nightshift/issues/213).

## what does not carry over as is

pstack is a cursor plugin. some parts work only in cursor, so arkan must rewrite them for claude code:

- model routing. pstack sends code work to grok and judgment to opus through `/setup-pstack`. claude code picks models in a different way.
- tool names. pstack says `Task`, `AskQuestion`, `.cursor/skills/`. claude code uses `Agent`, its own question tool, and `.claude/skills/`.
- links to other plugins. `poteto-mode` calls `deslop`, `control-cli` and `control-ui` from `cursor-team-kit`, which arkan does not have.

matt's skills already work in claude code. many of them expect an issue tracker (github issues or local files). for one person, local files are enough.

## the map

verdicts: **keep** (adapt and ship), **merge** (fold into another arkan skill), **later** (good, but not in v0.1), **drop** (does not fit a solo swe setup).

### the entry point

| arkan skill | from | verdict | why |
|---|---|---|---|
| `arkan-mode` | pstack `poteto-mode` + matt `ask-matt` | keep | one entry point that picks a flow. poteto-mode gives the playbooks and principles. ask-matt gives the simple main flow. |
| (principles) | pstack's 24 `principle-*` skills | merge | they become reference files inside `arkan-mode`, not 24 separate skills. 24 skill descriptions in every context window cost too much. |
| (playbooks) | pstack's 23 playbooks | merge | keep about 8 for v0.1: investigation, bug fix, feature, refactor, prototype, babysit, autonomous run, opening a pr. |

### the main flow

| arkan skill | from | verdict | why |
|---|---|---|---|
| `grill` | matt `grilling`, `grill-me`, `grill-with-docs`, `domain-modeling` | merge | one interview skill. it writes a glossary and decision records when a repo is there. |
| `plan` | matt `to-spec`, `to-tickets`, `wayfinder`; pstack `figure-it-out`, `multi-phase-plan` | merge | turn a talk into a spec and small tickets, each with its blockers. local files only (`.arkan/plans/`). |
| `build` | matt `implement`, `implement-spec`; pstack `architect`, feature playbook | merge | sketch the types first, then build ticket by ticket. |
| `tdd` | matt `tdd`; pstack `tdd`, `principle-test-behavior-not-implementation` | merge | matt's red-green loop, plus pstack's rule: a test that still passes when every function returns nothing is a bad test. |
| `debug` | matt `diagnosing-bugs`; pstack bug-fix playbook, `principle-fix-root-causes` | merge | get one command that fails on this bug first, then find the root cause, then fix with a regression test. |
| `review` | matt `code-review`; pstack `interrogate`, `blast-radius`, `no-comments` | merge | review against standards and the spec, then ask "what else can this break". |
| `ship` | matt `pr`; pstack opening-a-pr, babysit, shipping playbooks | merge | write the pr, then drive it to green. |
| `learn` | pstack `correct`, `reflect`; matt `retro` | merge | after a session, turn each repeated mistake into a check (structure, then types, then lint, then test, then docs last). this is the dune idea in skill form. |

### support skills

| arkan skill | from | verdict | why |
|---|---|---|---|
| `explain` | pstack `how`, `why`, `teach`, `bro`; matt `wait-what` | merge | "how does this work", "why is it like this", and "say that again in plain words". |
| `handoff` | matt `handoff`; pstack `recall`, `ketchup`, session-pickup, pause-safely | merge | save state before you stop, and pick it up again later. |
| `write` | pstack `unslop`, `technical-writing`; matt `writing-for-agents` | merge | one writing standard for prose, docs and skills. it uses ste rules and your lowercase style. |
| `verify` | pstack `create-verification-skill`, `maintain-verification-skill` | keep | makes a per-repo skill that drives the real app. this is the dune verifier idea. |
| `prototype` | matt `prototype`; pstack prototype playbook | keep | throwaway code to answer a design question. |
| `research` | matt `research` | keep | small and useful as is. |

### later (v0.2 or after)

| skill | from | why later |
|---|---|---|
| `swarm`, `arena` | pstack | parallel agents. strong, but costly. add once the core works. |
| `show-me-your-work` | pstack | a decision log for long runs. useful when you let agents work overnight. |
| `improve-codebase-architecture`, `codebase-design` | matt | per-repo health work. fits the dune layer in v0.2. |
| `setup-ts-deep-modules` | matt (in progress) | per-repo, typescript only. fits the dune layer. |
| `git-guardrails-claude-code` | matt | the installer could add these hooks. decide in step 3. |
| `automate-me` | pstack | turns your working style into a skill. good once arkan has run for a while. |
| `benchmark-checklist`, perf, hillclimb, forensics playbooks | pstack | only for perf work. |
| `typescript-best-practices` | pstack | per language. add per repo. |
| `wizard` | matt | steps only a human can do. |

### drop

| skill | from | why |
|---|---|---|
| `setup-pstack`, `poteto-help` | pstack | cursor model setup and pstack help. `arkan-mode` covers routing. |
| `make-bot-ui`, visual-parity, worktree-cleanup, autopilot and orchestrate playbooks | pstack | team or cursor specific. |
| `triage`, `to-questionnaire`, `setup-matt-pocock-skills` | matt | for issues from other people. you work alone. |
| `migrate-to-shoehorn`, `scaffold-exercises`, `setup-pre-commit` | matt | matt's own tools. |
| `teach`, `writing-*`, `chief-of-staff`, `loop-me`, `claude-handoff` | matt | not engineering, or still in progress. |

## the v0.1 core

if you agree with the map, step 2 builds these 10 skills:

`arkan-mode`, `grill`, `plan`, `build`, `tdd`, `debug`, `review`, `ship`, `learn`, `write`.

`explain`, `handoff`, `verify`, `prototype` and `research` follow right after, still in v0.1 if step 2 goes well.

## open questions

1. **name clash.** you already have some skills with the same names in your account (`tdd`, `grilling`, `code-review`, `prototype`, `research`). two skills with one name confuse the agent. options: give all arkan skills an `arkan-` prefix, or let arkan replace them. i suggest the prefix only where a clash exists.
2. **dune notes.** do you have the talk link or your own notes? the dune section above is secondhand.
3. **chopper.** where does the chopper repo live (github name or folder on your mac)? step 4 needs it.
