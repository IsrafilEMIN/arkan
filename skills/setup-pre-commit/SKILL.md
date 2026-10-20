---
name: setup-pre-commit
description: "Set up the repo's commit hook for its language: rust (cargo fmt --check, cargo clippy), python (ruff format --check, ruff check), go (gofmt -l, go vet), or js/ts (husky + lint-staged + prettier). Use when the user wants a pre-commit hook, commit-time formatting or linting, or to run setup-pre-commit."
disable-model-invocation: true
---

# Setup Pre-Commit Hooks

The commit hook runs the language's formatter and linter. Tests and type checks stay in CI.

## Supported languages

| language | manifest | hook runs |
| --- | --- | --- |
| rust | `Cargo.toml` | `cargo fmt --check`, `cargo clippy --workspace -- -D warnings` |
| python | `pyproject.toml` | `ruff format --check`, `ruff check` |
| go | `go.mod` | `gofmt -l`, `go vet` |
| js/ts | `package.json` | husky + lint-staged + prettier |

## 1. Detect the language

Check every manifest in the repo root. Use the table above.

- No manifest: ask the user which language to hook.
- One manifest: use that language.
- Several manifests: ask the user which language to hook.

## 2. Rust, Python, Go

Run the installer from this skill:

```bash
scripts/install-hook.sh <language> [repo-root]
```

The script writes only the repo's own plain git hook. It reads the repo's local `core.hooksPath` (expanding `~/`, resolving a relative path against the repo root); with no local value it uses the hooks directory under `git rev-parse --git-common-dir`. It never writes a global hooks path. It compares that target with git's effective hooks path: when git runs hooks from elsewhere it notes the delegation if that hook chains back to the repo hook, and otherwise warns that the repo hook will not run until the path delegates. If the target is outside the repo, it warns that the hook runs for every repo that shares it. It writes `hook written: <path>` or `hook unchanged: <path>`, so rerunning it is safe. It refuses js/ts.

The hook checks the staged file names before it does anything: with no staged file of the language, the commit proceeds. It refuses a staged file whose worktree copy has unstaged changes, so the tools see what is committed. Python and go pass the staged paths to their tools, and ruff uses `--force-exclude` so the repo's excludes apply. Rust runs both cargo commands from the table because cargo has no file scope.

If the script stops with `exists and arkan did not write it` or `was edited after arkan wrote it`, show the hook to the user and ask before replacing it. Move or reconcile the existing hook, then rerun the script. The installer never writes a global hooks path.

## 3. js/ts

### 3.1 Detect package manager

Check for `package-lock.json` (npm), `pnpm-lock.yaml` (pnpm), `yarn.lock` (yarn), `bun.lockb` (bun). Use whichever is present. Default to npm if unclear.

### 3.2 Install dependencies

Install as devDependencies:

```
husky lint-staged prettier
```

### 3.3 Initialize Husky

```bash
npx husky init
```

This creates `.husky/` and adds `prepare: "husky"` to package.json.

### 3.4 Create `.husky/pre-commit`

Write this file (no shebang needed for Husky v9+):

```
npx lint-staged
```

Replace `npx` with the detected package manager's runner.

The hook runs the formatter only. Leave the typecheck and test commands out; CI owns them.

### 3.5 Create `.lintstagedrc`

```json
{
  "*": "prettier --ignore-unknown --write"
}
```

### 3.6 Create `.prettierrc` (if missing)

Only create if no Prettier config exists. Use these defaults:

```json
{
  "useTabs": false,
  "tabWidth": 2,
  "printWidth": 80,
  "singleQuote": false,
  "trailingComma": "es5",
  "semi": true,
  "arrowParens": "always"
}
```

### 3.7 Verify

- [ ] `.husky/pre-commit` exists and is executable
- [ ] `.lintstagedrc` exists
- [ ] `prepare` script in package.json is `"husky"`
- [ ] `prettier` config exists
- [ ] `npx lint-staged` works

### 3.8 Commit

Stage the created and changed files and commit with message `Add pre-commit hooks (husky + lint-staged + prettier)`.

## 4. Verify the hook

Run `scripts/install-hook.sh <language> [repo-root]` a second time: it prints `hook unchanged: <path>`. For js/ts, commit a staged file and watch lint-staged run.

## Notes

- Husky v9+ doesn't need shebangs in hook files
- `prettier --ignore-unknown` skips files Prettier can't parse (images, etc.)
- For rust, python and go the hook is a plain git hook, not a package-manager hook
