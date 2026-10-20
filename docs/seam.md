# Seam

arkan and underground share one machine and one agent workflow. underground bounds an agent on the machine (local infra). arkan defines how agents work (the skills, the pipeline). They meet at exactly six interfaces, each with one owner. The agreement is underground's `docs/adr/0002-repo-seam.md`; this page is arkan's side of it.

| # | interface | owner | what arkan does with it |
|---|---|---|---|
| 1 | launcher entry points (`omp-srt`, `claude` on `PATH`) | underground | names them; never reaches past them |
| 2 | broker clients and their verbs (`agent-gh` and its ten verbs, `agent-merge`, `agent-worktree-remove`) | underground | `arkan-mode`'s forge steps call them on the broker route |
| 3 | hook wiring (`~/.agents/hooks.json`, the shell-hooks extension, `~/.agents/git-hooks/`) | underground | nothing; the `freeze` skill's own adapters are private to it |
| 4 | policy file (`~/.omp/policy.yml`) | underground | nothing |
| 5 | tracker contract (`docs/agents/issue-tracker.md`) | arkan | `pre-setup`'s seeds and `board.sh build\|check\|fields`; with a local tracker the field and board checks run locally through `pre-setup`, because a consumer repo's ci does not fetch arkan (arkan's own ci runs its `scripts/board.sh` copy) |
| 6 | merge rule: the `PASS` verdict, the agent mark `<!-- arkan:verifier -->`, the risk marker `<!-- arkan:risk head=<sha> label=<auto\|manual> -->`, and the rule | arkan | `ci/github/arkan-risk.yml` writes the marker; the broker's `pr-merge` applies the rule (its merge loop, where deployed, uses the same code); `ci/github/arkan-merge.yml` is the gate a consumer repo can install; `docs/agents/approvals.md` (from `pre-setup`) states the rule and records the repo's merge path (`**Merge path:** broker` for arkan) |

Row 2's verbs, as `agent-gh <verb>`: `push`, `worktree-remove`, `pr-create`, `pr-view`, `pr-checks`, `pr-merge`, `pr-retarget`, `pr-review`, `pr-reply`, `pr-diff`, and `raw` (the transport `pr-diff` and `worktree-remove` use).

## The merge rule (row 6)

- A verdict is a pull request review on the head commit whose body starts with `PASS`.
- The broker adds the agent mark to every verdict an agent posts; an agent cannot post one without it.
- A pull request whose risk marker for the current head says `auto` merges on a marked or an unmarked `PASS`. Any other pull request (`manual`, no marker, or a marker for an older head) merges only on an unmarked `PASS`: the person's. On a `manual` pull request, an agent's marked `PASS` never substitutes for the person's.
- Both merge paths obey it: a repo's `arkan-merge` workflow, and the broker's `pr-merge` (and its merge loop, where deployed). arkan uses the broker and installs no gate; `ci/github/arkan-merge.yml` stays as the gate a consumer repo can install.

The merge path is a local `pre-setup` choice recorded in `docs/agents/approvals.md` as `**Merge path:** gate` or `**Merge path:** broker`; arkan's line says broker. The broker never reads that file: it applies the rule above from the marker and the review on the head.

## Drift check

`scripts/check-seam.sh` runs in `scripts/check.sh`, so ci fails on drift:

- a file names `agent-gh <verb>` with a verb that is not in row 2's list above;
- `ci/github/arkan-merge.yml`, `ci/github/arkan-risk.yml` or their copies in `.github/workflows/` do not carry row 6's agent mark and risk marker exactly as written here;
- a file outside `.scratch/` and this page names a path inside underground (its broker sources, staged copies, probes, threat model or adr).

## Change rule

One change edits a row on both sides together: this page and the adr. A new string or file that the other repo reads becomes a row first. arkan cites underground by row number, never by a file path inside underground; underground does the same. Everything not in the table is private to its repo.
