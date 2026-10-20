# arkan

arkan is a bundle of agent skills. It keeps the way of work in one place: a person shapes the work, an agent runs one task at a time, and a merge lands only after an independent check.

## install

start with them.
[`pre-setup`](skills/pre-setup/SKILL.md) sets up a repo: it installs the skills, seeds the tracker and the board, and offers the ci files.
the rest of this page shows how the flow works.

## the flow in one view

```
idea
  -> grill-with-docs -> to-spec -> to-tickets
  -> task line: arkan-mode
       -> one ticket or a small request
       -> work in a worktree, verify it, review it
       -> open a pr
       -> a verifier posts PASS on the head commit
       -> the broker merges a manual pr on the owner's PASS
```

above the task line, a person decides what to build. below it, the agent works alone and comes back to the person for approval and for any action that cannot be undone.

after a merge breaks main, `post-merge` finds the first bad merge, reverts or fixes forward on a branch, and opens a ticket for the miss. a person can start it, or [`ci/github/arkan-post-merge.yml`](ci/github/arkan-post-merge.yml) starts it when main's check fails or a revert lands, and once a day for slow signals. see [`ci/README.md`](ci/README.md#arkan-post-merge).

## review in ci

[`ci/github/arkan-review.yml`](ci/github/arkan-review.yml) runs `code-review` and `security-review` on each push to an open pr, keeps the findings and the round count in one comment on the pr (a later push gets only its new commits reviewed, and round 4 asks for a rethink), and sets an `arkan-review` check that fails while an `important` or security finding is open. the model reads committed files through a small runner with no shell or github access. to add it to a repo:

1. put arkan's skills in `skills/` or `.claude/skills/` on the default branch.
2. add the repo secret `OPENCODE_API_KEY`.
3. copy `ci/opencode_agent.py` to the default branch and the review file to `.github/workflows/arkan-review.yml`, then make `arkan-review` a required check.

it skips docs-only prs, prs from forks, and the pull request that first installs the runner; it says so on the pr. the details are in [`ci/README.md`](ci/README.md).

[`ci/github/arkan-risk.yml`](ci/github/arkan-risk.yml) labels each pr `auto` or `manual`. a path on `docs/agents/sensitive-paths.md` and a pr from anyone but the repo owner are always `manual`. three fresh model votes label the rest, and a second check can only raise the label to `manual`. an `auto` pr may merge on the agent verifier's `PASS`; a `manual` pr needs the owner's `PASS`.

[`ci/github/check.yml`](ci/github/check.yml) runs the repo's check command (`bash scripts/check.sh` by default) on each push and pr, as a `check` job; `check` and `arkan-review` are the two checks a branch rule requires. see [`ci/README.md`](ci/README.md#check).

[`ci/github/arkan-merge.yml`](ci/github/arkan-merge.yml) is the merge gate a repo can install once instead of the broker: it merges a pr when every check on the head passed and a review on that head, from a reviewer with write access, begins with `PASS`. arkan itself merges through the broker (`agent-merge <pr> <sha>` after the person's `PASS`), not this gate; a consumer repo chooses one path and records `**Merge path:** gate` or `**Merge path:** broker` in `docs/agents/approvals.md`. install steps and branch rules: [`ci/README.md`](ci/README.md#arkan-merge).

## where the skills come from

| source | skills in arkan |
|---|---|
| [pstack](https://github.com/cursor/plugins/tree/182f2ce/pstack) by lauren tan, at commit `182f2ce` | `arkan-mode`: its playbooks are pstack's, with the cursor-only parts removed; its `SKILL.md` is a rewrite of `poteto-mode`. the 24 `principle-*` skills are copies of pstack's, adapted; `principle-test-behavior-not-implementation` also carries `arkan-mode`'s failing-shape list |
| [mattpocock/skills](https://github.com/mattpocock/skills) by matt pocock, main branch | `code-review`, `codebase-design`, `diagnosing-bugs`, `domain-modeling`, `git-guardrails-claude-code`, `grill-with-docs`, `grilling`, `handoff`, `improve-codebase-architecture`, `pr`, `prototype`, `retro`, `setup-pre-commit`, `tdd`, `to-spec`, `to-tickets`, `triage`, `wait-what`, `wayfinder`, `wizard`, `writing-for-agents`, `pre-setup` (from `setup-matt-pocock-skills`), and `arkan-mode`'s spec playbook (from `implement-spec`). some of them are changed. |
| [claude-code-security-review](https://github.com/anthropics/claude-code-security-review/tree/0c6a49f) by anthropic, at commit `0c6a49f` | `security-review`: a copy of `.claude/commands/security-review.md`, with the claude-code-only parts ported |
| [pstack](https://github.com/cursor/plugins/tree/d457567/pstack) by lauren tan, at commit `d457567` | `create-verification` (from `create-verification-skill`) and `maintain-verification` (from `maintain-verification-skill`), ported to arkan's repo-local skill path, sandbox limits and merge path; `blast-radius`, `interrogate`, `architect`, `arena`, `swarm`, `figure-it-out`, `benchmark-checklist`, `unslop`, `technical-writing`, `no-comments` (with its comment-sicko agent as a reference prompt), `show-me-your-work`, `how`, `why`, `teach`, `in-your-own-words`, `sharpen`, `recall`, `reflect`, `correct`, `ketchup`, `bro`, `automate-me`, `typescript-best-practices`, `make-bot-ui`, `create-formal-verification`, `maintain-formal-verification`, ported to arkan-mode's… |
| written for arkan | `post-merge`, with parts from pstack's babysit and shipping playbooks |
| not recorded | `assess`, `freeze`, `good-css`, `product-brief`, `simplest-path`, `symlink-first`, `test-to-break` |

all three sources use the mit license. [`NOTICE`](NOTICE) keeps their copyright notices and license text. `skills/pr/CREDITS.md` names one more source, for part of the `pr` skill.
