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
| rust | `Cargo.toml` | `cargo fmt --check`, `cargo clippy` |
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

The script writes the repo's plain git hook. It asks git for the hooks directory with `git rev-parse --git-path hooks`, so a configured `core.hooksPath` is respected. It writes `hook written: <path>` or `hook unchanged: <path>`, so rerunning it is safe. It refuses js/ts.

The hook checks the staged file names before it does anything: with no staged file of the language, the commit proceeds. Python and go pass the staged paths to their tools. Rust runs the workspace commands from the table, because cargo has no file scope.

If the script stops with `exists and arkan did not write it`, show the existing hook to the user and ask before replacing it. Delete it only after the user agrees, then rerun the script.

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
