# Harnesses

Where each harness reads skills and instructions, and how pre-setup sets it up. The canonical home is `~/.agents/skills/<name>/`: a harness that reads it needs no link.

Sources: `skills/symlink-first/SKILL.md`'s agent map (verified 2026-10 against each harness's docs or source), the sources ticket 04 read on 2026-10-18, and tickets 05 and 06. A fact with no source below is `unverified`: check the harness's own docs before you rely on it.

## Name scan scope

On 2026-10-20 the owner narrowed ticket 17 from eight harnesses to "scan your three harnesses": Claude code, Codex and Omp. Harness setup and detection below are unchanged. The name scanner does not traverse Pi, Hermes, dsh, Cursor or Opencode roots or parse their config. It reports those arguments as `unverified` and continues with supported arguments.

| harness | candidate roots | discovery and missing-name rule |
|---|---|---|
| Claude code | `~/.claude/skills` only | Immediate child directories containing `SKILL.md`. An omitted name uses the discovery directory name. Plain skills named `simplify`, `code-review` or `security-review` shadow built-ins. |
| Codex | `~/.agents/skills` and `${CODEX_HOME:-~/.codex}/skills` | Recursive `SKILL.md` discovery through depth 6. Hidden directories, including `.system`, are excluded. Missing or empty `name` in frontmatter falls back to the canonical source directory name. A file without frontmatter is skipped. |
| Omp | `~/.agents/skills`, `~/.claude/skills` and `~/.codex/skills` | Immediate child directories containing `SKILL.md`. Hidden children, including `.system`, are excluded. An omitted name uses the discovery directory name. |

Records are `(harness, namespace, effective name, canonical source, discovery root)`. Grouping is within one harness, namespace and name. Two links to the same canonical source are one skill. Plugins use separate namespaces and remain unscanned. Project roots and every other skill root are outside this inventory.

This is a candidate-name inventory, not a loader clone. It reads simple scalar `name:` frontmatter, not arbitrary YAML. It does not validate every metadata field, apply enable flags, or prove that every candidate is enabled. Codex requires a description to load a skill. Omp can disable foreign user providers and individual skills. Those controls do not change the inventory. A reported clash can therefore involve an invalid or disabled candidate.

`apply arkan` adds incoming candidates only for Codex and Omp. Its preflight follows link chains and substitutes the incoming source at owned `.agents/skills/<name>` links that apply will replace. Existing `.claude` mirrors through such links see the same incoming source in both Claude code and Omp inventories. This does not add incoming candidates to Claude code. A direct link to an old checkout, an unowned link or a real directory remains independent. Plain `check` never adds incoming candidates.

Sources read 2026-10-20:

- Claude's [skills frontmatter reference](https://code.claude.com/docs/en/skills#frontmatter-reference) is quoted in the official [documentation issue 39105](https://github.com/anthropics/claude-code/issues/39105), including "If omitted, uses the directory name." The docs host refused direct access in this session.
- Codex [parser](https://github.com/openai/codex/blob/464add49587a7cb6032d5ab04faa8a1585947853/codex-rs/skills/src/parser.rs), [host loader](https://github.com/openai/codex/blob/464add49587a7cb6032d5ab04faa8a1585947853/codex-rs/ext/skills/src/loader/host.rs), and [discovery](https://github.com/openai/codex/blob/464add49587a7cb6032d5ab04faa8a1585947853/codex-rs/ext/skills/src/loader/discovery.rs) supply fallback, canonicalization and recursive discovery. `loader/mod.rs` sets depth 6.
- Omp [skills docs](https://github.com/can1357/oh-my-pi/blob/2220e58146ebe31508e7a216242840d373e082d0/docs/skills.md) and [scanner](https://github.com/can1357/oh-my-pi/blob/2220e58146ebe31508e7a216242840d373e082d0/packages/coding-agent/src/discovery/helpers.ts) supply its non-recursive layout and discovery-directory fallback.

## Claude code

- user skills: `~/.claude/skills/<name>/` as a link, or the arkan plugin, which names each skill `arkan:<name>`. Source: `skills/symlink-first/SKILL.md`, agent map (verified 2026-10); ticket 06.
- project skills: `<repo>/.claude/skills/<name>/`. Source: `skills/pre-setup/SKILL.md`, `ci-review` row (2026-10-19).
- instruction file: `CLAUDE.md`, at `~/.claude/CLAUDE.md` for the user and `<repo>/CLAUDE.md` for a repo. Source: agent map (verified 2026-10); ticket 06.
- frontmatter: reads invocation from `SKILL.md` frontmatter, including `disable-model-invocation`. The full field list is `unverified`. Source: agent map (verified 2026-10).
- manual only: `disable-model-invocation: true` in `SKILL.md`. Source: agent map (verified 2026-10).
- symlinks: follows them. A link in `~/.claude/skills/` is how it reads a skill outside its own folder. Source: agent map (verified 2026-10).
- docs: <https://code.claude.com/docs/en/skills>, read 2026-10-18.
- setup: `apply claude-plugin` installs the plugin, with no link to an arkan skill in `~/.claude/skills/`. In a repo, `apply claude-md` links `CLAUDE.md` to `AGENTS.md`. Source: agent map (verified 2026-10); tickets 04 and 06.

## Codex

Version 0.161.

- user skills: `~/.agents/skills/`. It also reads `$CODEX_HOME/skills/`, which holds its `.system` skills and its installer's skills. Source: agent map (verified 2026-10).
- project skills: `unverified`.
- instruction file: `${CODEX_HOME:-~/.codex}/AGENTS.md` for the user. The project file is `unverified`. Source: agent map (verified 2026-10).
- frontmatter: it reads invocation from `agents/openai.yaml` beside `SKILL.md`, not from the `SKILL.md` frontmatter. The fields are `interface.display_name`, `interface.short_description` and `policy.allow_implicit_invocation`. Source: `skills/symlink-first/SKILL.md`, "Skill metadata for codex"; <https://learn.chatgpt.com/docs/build-skills>, verified 2026-10; codex source `codex-rs/skills/src/`, read 2026-10-18.
- manual only: `policy.allow_implicit_invocation: false` in `agents/openai.yaml`. Source: `skills/symlink-first/SKILL.md`, "Skill metadata for codex"; <https://learn.chatgpt.com/docs/build-skills>, verified 2026-10.
- symlinks: follows them. It reads the linked `~/.agents/skills/` tree. Source: agent map (verified 2026-10).
- docs: the codex skills page was blocked from the cloud session on 2026-10-18; the read source was `codex-rs/skills/src/` in <https://github.com/openai/codex>, read 2026-10-18. <https://learn.chatgpt.com/docs/build-skills>, verified 2026-10.
- setup: nothing. It already reads `~/.agents/skills/`.

## dsh

Version 0.2.

- user skills: `${DSH_AGENTS_HOME:-~/.agents}/skills/`. Source: agent map (verified 2026-10).
- project skills: `unverified`.
- instruction file: `${DSH_HOME:-~/.dsh}/AGENTS.md` for the user. The project file is `unverified`. Source: agent map (verified 2026-10).
- frontmatter: `unverified`.
- manual only: `unverified`.
- symlinks: follows them. It reads the linked skills tree. Source: agent map (verified 2026-10).
- docs: `unverified`. The agent map records no link.
- setup: nothing when `DSH_AGENTS_HOME` is unset or names `~/.agents`. Another value makes `harnesses` read `hint`: dsh then reads that root's `skills/`, not arkan's.

## Pi

Version 1.1.

- user skills: `~/.agents/skills/`. Source: agent map (verified 2026-10). Pi name scanning is outside ticket 17's approved scope.
- project skills: `unverified`.
- instruction file: `~/.pi/agent/AGENTS.md` for the user. The project file is `unverified`. Source: agent map (verified 2026-10).
- frontmatter: `unverified`.
- manual only: `unverified`.
- symlinks: follows them. It reads the linked `~/.agents/skills/` tree. Source: agent map (verified 2026-10).
- docs: <https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/skills.md>, read 2026-10-18.
- setup: nothing. It already reads `~/.agents/skills/`.

## Omp

Version 18.8.

- user skills: `~/.agents/skills/`. It also loads `~/.claude/skills/` and `~/.codex/skills/`. Source: agent map (verified 2026-10).
- project skills: `unverified`.
- instruction file: `~/.agents/AGENTS.md`, which it reads itself. The project file is `unverified`. Source: agent map (verified 2026-10).
- frontmatter: `unverified`.
- manual only: `unverified`.
- symlinks: follows them. It reads the linked `~/.agents/skills/` tree, plus the two mirrors it loads. Source: agent map (verified 2026-10).
- docs: <https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md>, read 2026-10-18.
- setup: nothing. It already reads `~/.agents/skills/`.

## Cursor

Version 2026.09.

- user skills: `~/.agents/skills/`. It also loads `~/.claude/skills/` and `~/.codex/skills/`. Source: agent map (verified 2026-10).
- project skills: `unverified`.
- instruction file: `unverified`. The agent map records its global instructions as not checked.
- frontmatter: `unverified`.
- manual only: `unverified`.
- symlinks: follows them. It reads the linked `~/.agents/skills/` tree, plus the two mirrors it loads. Source: agent map (verified 2026-10).
- docs: `unverified`. The agent map records no link.
- setup: nothing. It already reads `~/.agents/skills/`.

## Opencode

Version 2.0.

- user skills: `~/.agents/skills/`. It also loads `~/.claude/skills/`. Source: agent map (verified 2026-10).
- project skills: `unverified`.
- instruction file: `unverified`. The agent map records its global instructions as not checked.
- frontmatter: `unverified`.
- manual only: `unverified`.
- symlinks: follows them. It reads the linked `~/.agents/skills/` tree, plus the mirror it loads. Source: agent map (verified 2026-10).
- docs: `unverified`. The agent map records no link.
- setup: nothing. It already reads `~/.agents/skills/`.

## Hermes

Version 0.21.

- user skills: through config, not a link. A nested `skills.external_dirs` list in `~/.hermes/config.yaml` names `~/.agents/skills`:

  ```yaml
  skills:
    external_dirs:
      - ~/.agents/skills
  ```

  Source: agent map (verified 2026-10).
- project skills: `unverified`.
- instruction file: `unverified`. The agent map records its global instructions as not checked.
- frontmatter: `unverified`.
- manual only: `unverified`.
- symlinks: it reads the external directory, and its curator can edit a linked skill, so a write can reach the canonical copy. Source: agent map (verified 2026-10).
- docs: `unverified`. The agent map records no link.
- setup: nothing when the config's `skills.external_dirs` names `~/.agents/skills`. Without it, `harnesses` reads `hint`; the skill writes the block above after a yes. A local hermes skill with the same name wins over the external one.
