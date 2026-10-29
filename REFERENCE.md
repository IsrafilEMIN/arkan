# reference

every outside source arkan copies from or learns from.

## skill sources

| source | skills in arkan |
|---|---|
| [pstack](https://github.com/cursor/plugins/tree/182f2ce/pstack) by lauren tan, at commit `182f2ce` | `arkan-mode`: its `SKILL.md` is a rewrite of `poteto-mode`, and its playbooks are pstack's, with the cursor-only parts removed (the ones listed in the `c742dd6` row match that commit). the 24 `principle-*` skills are copies of pstack's, adapted, several with arkan additions; `principle-test-behavior-not-implementation` also carries `arkan-mode`'s failing-shape list. `tdd` folds in pstack's "when a test is impractical" section |
| [pstack](https://github.com/cursor/plugins/tree/d457567/pstack) by lauren tan, at commit `d457567` | `create-verification` (from `create-verification-skill`) and `maintain-verification` (from `maintain-verification-skill`), ported to arkan's repo-local skill path and sandbox limits; `blast-radius`, `architect`, `swarm`, `figure-it-out`, `benchmark-checklist`, `unslop`, `technical-writing`, `no-comments` (with its comment-sicko agent as a reference prompt), `show-me-your-work`, `how`, `why`, `teach`, `in-your-own-words`, `sharpen`, `recall`, `ketchup`, `bro`, `automate-me`, `typescript-best-practices`, `make-bot-ui`, `create-formal-verification`, `maintain-formal-verification`, ported to arkan-mode's principles and playbooks, with transcript paths per harness and the repo's own tracker as an evidence source, with cursor's model config replaced by "different model families where the harness allows". `reflect` is merged into `retro`: its steps and its reviewer and synthesizer prompts in `retro/references/` |
| [pstack](https://github.com/cursor/plugins/tree/c742dd6/pstack) by lauren tan, at commit `c742dd6` | `arkan-mode`'s autonomous run, perf issue, hillclimb, eval, runtime forensics, trace forensics, visual parity, orchestrate and worktree cleanup playbooks, and `skills/arkan-mode/scripts/worktree-audit.sh`; `principle-explain-the-number`, `arena`, `interrogate` and `correct`. `technical-writing`, `ketchup`, `recall`, `why` and `arkan-mode`'s review-bot triage carry content restored from `d457567` and `c742dd6` |
| [mattpocock/skills](https://github.com/mattpocock/skills/tree/93497a8) by matt pocock, base copy at commit `93497a8` (2026-10-06), with later parts from [commit `59db609`](https://github.com/mattpocock/skills/tree/59db609) (2026-10-27) | `code-review`, `codebase-design`, `diagnosing-bugs`, `domain-modeling`, `grilling` (with `grill-with-docs` and `grill-me` folded in), `retro`, `setup-pre-commit`, `tdd`, `to-spec`, `to-tickets`, `triage`, `wayfinder` (its `research.md` from `research`), `writing-for-agents`, `pre-setup` (from `setup-matt-pocock-skills`), and `arkan-mode`'s spec playbook (from `implement-spec`). some of them are changed. from `59db609`: `wizard` and `improve-codebase-architecture`, and later fixes to the issue tracker and triage labels in `pre-setup`, and to `to-tickets`, `code-review`, `diagnosing-bugs`, `tdd` and `wayfinder` |
| [claude-code-security-review](https://github.com/anthropics/claude-code-security-review/tree/0c6a49f) by anthropic, at commit `0c6a49f` | `security-review`: a copy of `.claude/commands/security-review.md`, with the claude-code-only parts ported |
| [good-css](https://github.com/vojtaholik/good-css/tree/92d436b) by vojta holik, at commit `92d436b` | `good-css`, from `skills/good-css/` |
| written for arkan | `post-merge`, with parts from pstack's babysit and shipping playbooks; `simplest-path` |

all four sources use the mit license. [`NOTICE`](NOTICE) keeps their copyright notices and license text.

## articles

| date | article | authors | what arkan took | notes |
|---|---|---|---|---|
| 2026-10-15 | [how the claude code team does code review](https://claude.dev/blog/solving-code-review-at-anthropic/) | addy osmani, morgan westlee lunt, qing wang | already in arkan: fresh-context review, verified findings with `important`, `nit`, `pre-existing` tags, round cap and diff-only re-review. removed: the `REVIEW.md` seed. added: the `auto` or `manual` merge grade in `code-review`, `## Risk` and `## Revert` in the pr body, the clean-pr and rounds-to-pass checks in `retro` | [docs/resources/2026-10-15-claude-code-team-code-review.md](docs/resources/2026-10-15-claude-code-team-code-review.md) |
| 2026-10-08 | [building effective agent automations](https://claude.dev/blog/building-effective-agent-automations/) | lance martin, cj avilla | added: `post-merge` reports an unread source as unread, not as a quiet day | [docs/resources/2026-10-08-building-effective-agent-automations.md](docs/resources/2026-10-08-building-effective-agent-automations.md) |
