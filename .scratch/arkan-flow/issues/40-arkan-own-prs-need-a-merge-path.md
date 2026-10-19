# 40: arkan's own pull requests need a merge path

**Role:** ready-for-agent
**Closed:** no
**Priority:** 28

**What to build:** decide how a pull request lands in arkan itself, and make that rule visible to a session before it calls the broker.

the observation, 2026-10-19, while landing board 04 (pr 32, merge commit `6bbf8c5`):

- `agent-merge 32 0650877` printed `no workflow runs for the head commit` and `no merge`, exit 1. the broker's `wait_for_checks` waits `FIRST_RUN_GRACE` = 120 s for a first run, then refuses when the head commit has none (`gh-broker`, `checks_state`).
- arkan has no `.github/workflows/`: the repo ships `ci/github/check.yml`, `ci/github/arkan-review.yml` and `ci/github/arkan-merge.yml` for other repos to copy, and runs none of them itself. so no head commit of arkan can have a run, and the broker's merge route cannot bind here.
- pr 32 landed by a person, and the merge was verified against the intended head (merge commit `6bbf8c5`, parents `f0101f4` + `0650877`). `shipping.md` step 4 already names that route: the repo's merge gate, the broker where none can bind, and the person otherwise.

the question for the owner:

1. is the person route the answer for arkan? then a session should read that before it pays the 120 s wait: the refusal reads as a broken gate, not as the rule. one line in `AGENTS.md` next to the checkpoints section, or in `shipping.md` step 4, would say it.
2. or does arkan get a check job of its own, so the broker's route binds? then it must be worth wiring: candidates are `scripts/board.sh check`, `bash -n` over `scripts/`, the yaml under `ci/`, and the skills' front matter. a job that exists only to satisfy the gate is not worth the runner time.

**Blocked by:** None (needs the owner's call first).

- [x] the owner picks one, and the rule lands where a session reads it (the broker's docs, `AGENTS.md`, or `shipping.md`)
- [ ] proof: one agent pull request of arkan lands through the chosen path, with the merge verified against the intended head

## Comments

- 2026-10-19, owner: option 2, so pull requests merge without a manual merge.
- 2026-10-19, agent: on branch `claude/ticket-40-merge-path`. `scripts/check.sh` runs `scripts/board.sh check`, `bash -n` over every tracked `*.sh`, and checks that each `skills/*/SKILL.md` has front matter whose `name` is its folder. it printed `check: ok`; with a broken script and a wrong skill name it named both and exited 1. `.github/workflows/check.yml` and `.github/workflows/arkan-merge.yml` are arkan's own `ci/github/` files, unchanged (`CHECK_COMMAND` already defaults to `bash scripts/check.sh`). `AGENTS.md` gains `### Merging`. not installed: `arkan-review` (it needs the `CLAUDE_CODE_OAUTH_TOKEN` secret and the skills in `.claude/skills/`); the gate waits only for the checks that exist.
- 2026-10-19, host steps for the owner: allow squash merges in the repo settings (the gate merges with `--squash`). a branch ruleset that requires `check` needs github pro on a private repo (`ci/README.md`, the plan gate); without it the gate still refuses a red head, but nothing stops a hand merge around it.
- 2026-10-19, owner: the repo gate merges (ticket 39 stands). to follow the claude code team's review post (an agent's approval never counts as a person's; start strict), the gate now refuses a `PASS` whose body holds `<!-- arkan:verifier -->`, the mark the broker adds to an agent's verdict (underground 48). a local test of the rule: a plain `PASS` passes, a marked one is refused. underground 49 lets the broker accept `claude/*` beside `agent/*`.
