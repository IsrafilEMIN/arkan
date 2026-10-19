# Seam

arkan and underground share one machine and one agent workflow. underground bounds an agent on the machine (local infra). arkan defines how agents work (the skills, the pipeline). They meet at exactly six interfaces, each with one owner. The agreement is underground's `docs/adr/0002-repo-seam.md`; this page is arkan's side of it.

| # | interface | owner | what arkan does with it |
|---|---|---|---|
| 1 | launcher entry points (`omp-srt`, `claude` on `PATH`) | underground | names them; never reaches past them |
| 2 | broker clients and their verbs (`agent-gh` and its ten verbs, `agent-merge`, `agent-worktree-remove`) | underground | `arkan-mode`'s forge steps call them on the broker route |
| 3 | hook wiring (`~/.agents/hooks.json`, the shell-hooks extension, `~/.agents/git-hooks/`) | underground | nothing; the `freeze` skill's own adapters are private to it |
| 4 | policy file (`~/.omp/policy.yml`) | underground | nothing |
| 5 | tracker contract (`docs/agents/issue-tracker.md`) | arkan | `pre-setup`'s seeds and `board.sh build\|check` |
| 6 | merge rule: the `PASS` verdict, the agent mark `<!-- arkan:verifier -->`, the risk marker `<!-- arkan:risk head=<sha> label=<auto\|manual> -->`, and the rule | arkan | `ci/github/arkan-risk.yml` writes the marker; `ci/github/arkan-merge.yml` applies the rule; `docs/agents/approvals.md` (from `pre-setup`) states it |

Row 2's verbs, as `agent-gh <verb>`: `push`, `worktree-remove`, `pr-create`, `pr-view`, `pr-checks`, `pr-merge`, `pr-retarget`, `pr-review`, `pr-reply`, `pr-diff`, and `raw` (the transport `pr-diff` and `worktree-remove` use).

## The merge rule (row 6)

- A verdict is a pull request review on the head commit whose body starts with `PASS`.
- The broker adds the agent mark to every verdict an agent posts; an agent cannot post one without it.
- A pull request whose risk marker for the current head says `auto` merges on a marked or an unmarked `PASS`. Any other pull request (`manual`, no marker, or a marker for an older head) merges only on an unmarked `PASS`: the person's.
- Both merge paths obey it: a repo's `arkan-merge` workflow, and the broker's `pr-merge`.

## Drift check

`scripts/check-seam.sh` runs in `scripts/check.sh`, so ci fails on drift:

- a file names `agent-gh <verb>` with a verb that is not in row 2's list above;
- `ci/github/arkan-merge.yml`, `ci/github/arkan-risk.yml` or their copies in `.github/workflows/` do not carry row 6's agent mark and risk marker exactly as written here;
- a file outside `.scratch/` and this page names a path inside underground (its broker sources, staged copies, probes, threat model or adr).

## Change rule

One change edits a row on both sides together: this page and the adr. A new string or file that the other repo reads becomes a row first. arkan cites underground by row number, never by a file path inside underground; underground does the same. Everything not in the table is private to its repo.
