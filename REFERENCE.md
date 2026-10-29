# reference

every outside source arkan copies from or learns from.

## skill sources

| source | skills in arkan |
|---|---|
| [pstack](https://github.com/cursor/plugins/tree/182f2ce/pstack) by lauren tan, at commit `182f2ce` | `arkan-mode`: its playbooks are pstack's, with the cursor-only parts removed; perf issue, hillclimb, eval, runtime forensics, trace forensics, visual parity, orchestrate, worktree cleanup and `scripts/worktree-audit.sh` come from [commit `c742dd6`](https://github.com/cursor/plugins/tree/c742dd6/pstack). its `SKILL.md` is a rewrite of `poteto-mode`. the 24 `principle-*` skills are copies of pstack's, adapted; `principle-test-behavior-not-implementation` also carries `arkan-mode`'s failing-shape list |
| [mattpocock/skills](https://github.com/mattpocock/skills) by matt pocock, main branch | `code-review`, `codebase-design`, `diagnosing-bugs`, `domain-modeling`, `grilling` (with `grill-with-docs` folded in), `retro`, `setup-pre-commit`, `tdd`, `to-spec`, `to-tickets`, `triage`, `wayfinder`, `writing-for-agents`, `pre-setup` (from `setup-matt-pocock-skills`), and `arkan-mode`'s spec playbook (from `implement-spec`). some of them are changed. |
| [claude-code-security-review](https://github.com/anthropics/claude-code-security-review/tree/0c6a49f) by anthropic, at commit `0c6a49f` | `security-review`: a copy of `.claude/commands/security-review.md`, with the claude-code-only parts ported |
| [pstack](https://github.com/cursor/plugins/tree/d457567/pstack) by lauren tan, at commit `d457567` | `create-verification` (from `create-verification-skill`) and `maintain-verification` (from `maintain-verification-skill`), ported to arkan's repo-local skill path and sandbox limits; `blast-radius`, `interrogate`, `architect`, `arena`, `swarm`, `figure-it-out`, `benchmark-checklist`, `unslop`, `technical-writing`, `no-comments` (with its comment-sicko agent as a reference prompt), `show-me-your-work`, `how`, `why`, `teach`, `in-your-own-words`, `sharpen`, `recall`, `reflect`, `ketchup`, `bro`, `automate-me`, `typescript-best-practices`, `make-bot-ui`, `create-formal-verification`, `maintain-formal-verification`, ported to arkan-mode's principles and playbooks, with transcript paths per harness and the repo's own tracker as an evidence source, with cursor's model config replaced by "different model families where the harness allows" |
| written for arkan | `post-merge`, with parts from pstack's babysit and shipping playbooks |
| not recorded | `good-css`, `simplest-path` |

all three sources use the mit license. [`NOTICE`](NOTICE) keeps their copyright notices and license text.

## articles

| date | article | authors | what arkan took | notes |
|---|---|---|---|---|
| 2026-10-15 | [how the claude code team does code review](https://claude.dev/blog/solving-code-review-at-anthropic/) | addy osmani, morgan westlee lunt, qing wang | already in arkan: fresh-context review, verified findings with `important`, `nit`, `pre-existing` tags, round cap and diff-only re-review, the `REVIEW.md` seed. added: the `auto` or `manual` merge grade in `code-review`, `## Risk` and `## Revert` in the pr body, the clean-pr and rounds-to-pass checks in `retro` | [docs/resources/2026-10-15-claude-code-team-code-review.md](docs/resources/2026-10-15-claude-code-team-code-review.md) |
| 2026-10-08 | [building effective agent automations](https://claude.dev/blog/building-effective-agent-automations/) | lance martin, cj avilla | added: `post-merge` reports an unread source as unread, not as a quiet day | [docs/resources/2026-10-08-building-effective-agent-automations.md](docs/resources/2026-10-08-building-effective-agent-automations.md) |
