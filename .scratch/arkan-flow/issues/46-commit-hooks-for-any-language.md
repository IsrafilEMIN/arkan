# 46: commit hooks for any language

**Role:** ready-for-agent
**Closed:** yes
**Priority:** 31

**What to build:** `setup-pre-commit` works for the repo's own language, not only js/ts. it detects the language and sets up a commit hook that runs that language's formatter and linter (not the tests: arkan-flow 36 allows red-first commits on a work branch). examples: rust → `cargo fmt --check` and `cargo clippy`; python → `ruff format --check` and `ruff check`; go → `gofmt -l` and `go vet`; js/ts → today's husky + lint-staged + prettier. `pre-setup`'s `hooks` item points to it for any detected language, not only when `package.json` exists.

**Blocked by:** None (can start immediately).

- [ ] the skill detects at least rust, python, go and js/ts from their manifest files (`Cargo.toml`, `pyproject.toml`, `go.mod`, `package.json`), and asks when it finds none or several
- [ ] for a language with no package-manager hook tool, it writes a plain `.git/hooks/pre-commit` (or the repo's `core.hooksPath`) that runs the formatter and linter on staged files
- [ ] the hook runs format and lint only; tests stay in ci
- [ ] `pre-setup`'s `hooks` check reports `hint` for any detected language with no hook
- [ ] proof: a scratch rust repo and a scratch python repo each get a hook that blocks a badly formatted commit and lets a clean one through

## Comments

- 2026-10-19, owner: capture the language adaptation in a ticket.
- 2026-10-19, agent: proof passed. a scratch rust repo blocked a badly formatted commit (`cargo fmt --check`) and passed after `cargo fmt`; a scratch python repo blocked one through `uvx ruff` and passed after `ruff format`; a second `install-hook.sh` run printed `hook unchanged`.
