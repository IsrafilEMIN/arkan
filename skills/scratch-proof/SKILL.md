---
name: scratch-proof
description: "Prove how a command, git, shell or a small script behaves by running it in a throwaway dir or scratch git repo, show the output as proof, then trash the dir. Use for \"prove whether X\", \"check if git X does Y\", \"try it in a scratch repo\", \"test this in a temp dir\", \"does this flag really do that\". Read this before you make a temp dir, temp repo or throwaway script."
---

# Scratch proof

Answer "does X behave like Y" by running X once in a throwaway place, not by reasoning about it. Build the smallest setup that shows the behavior, run one command per check, paste the output, then trash the setup.

## Hard rules

Most wasted calls in past sessions came from these. Follow them from the first call.

1. Make the scratch dir with `d=$(mktemp -d)`. Never type a `/tmp/...` path, never write into the user's repo, never use a fixed name.
2. Work only inside `"$d"`. Do not change the repo you were asked about; copy or clone it into `"$d"` when you need its content.
3. Clean up with `trash "$d"`. Never `rm`, `rm -rf`, `unlink`, `rmdir`, `find -delete`, `rsync --delete`, the edit tool's file delete, or Python/JS delete calls.
4. Do not put delete commands in a `trap`, a here-doc, a string or an eval cell either. The guard matches text, so `trap 'rm -rf "$d"' EXIT` or the text `rm -rf` inside a Python string blocks the whole call.
5. In bash, do not start any command (also after `;`, `&&` or `|`) with `cat`, `head`, `tail`, `less`, `grep`, `rg`, `find -name/-type`, `sed -i`, or `echo`/`printf`/`cat` redirected into a file. One such command blocks the whole call. See "Instead of" below.
6. One check per command, and print its exit code: `cmd; echo "exit=$?"`.

## 1. Make the scratch dir

```bash
d=$(mktemp -d) && echo "d=$d"
```

`mktemp -d` uses `$TMPDIR`, a private per-user folder. Keep the printed path. The bash tool keeps shell variables between calls on most hosts, but give `d=<printed path>;` again at the start of a call when `$d` is empty. When a test needs a dir under `$HOME` (for example a headless omp run), use `d=$(mktemp -d "$HOME/scratch-<topic>.XXXX")`.

## 2. Build the setup

### Git repo with a bare origin and a clone

```bash
set -u
export GIT_AUTHOR_NAME=scratch GIT_AUTHOR_EMAIL=scratch@example.invalid GIT_COMMITTER_NAME=scratch GIT_COMMITTER_EMAIL=scratch@example.invalid
git init -q --bare -b main "$d/origin.git"
git clone -q "$d/origin.git" "$d/work" 2>/dev/null
cd "$d/work"
git commit -q --allow-empty -m base && git push -q origin main
git switch -q -c feature
printf 'one\n' | tee a.txt >/dev/null && git add a.txt && git commit -q -m "add a"
git log --oneline --all; echo "exit=$?"
```

- The `export` line gives git an identity for this shell only. Never change git config.
- Need a second user of the same remote? `git clone -q "$d/origin.git" "$d/other"`.
- Need the real repo's history? `git clone -q --no-local <repo-path> "$d/work"`. The clone is yours to change.

### Fixture tree

Write each file with the `write` tool at `"$d/..."` (absolute path). For many small files in bash, pipe into `tee`:

```bash
mkdir -p "$d/fx/src" "$d/fx/logs"
printf 'export const a = 1;\n' | tee "$d/fx/src/a.ts" >/dev/null
printf 'ok\nERROR old\nERROR new\n' | tee "$d/fx/logs/app.log" >/dev/null
ls -R "$d/fx"; echo "exit=$?"
```

### TypeScript or JavaScript check

`node` and `bun` are often not on `PATH` on omp hosts. omp ships bun:

```bash
BUN_BE_BUN=1 omp "$d/probe.ts"; echo "exit=$?"
BUN_BE_BUN=1 omp test "$d/probe.test.ts"; echo "exit=$?"
BUN_BE_BUN=1 omp -e 'console.log(process.versions.bun)'
```

Write `probe.ts` with the `write` tool. Use `bun:test` (`import { expect, test } from "bun:test"`) for tests.

### Python check

Use `python3 "$d/probe.py"` or the eval tool. In eval, make the dir with `tempfile.mkdtemp()` and clean it with `sh(f"trash {d}")`. Do not call file delete functions (`os.remove`, `shutil.rmtree`, `Path.unlink`, `.delete()`) even on scratch files: the guard blocks the cell.

### A server or watcher

Start it as a named bash service (bash tool `name` and `ready`), not with `&` or `nohup`. Stop it through `proc://<name>/kill`. To stop a process you started yourself, `kill <pid>`; never `pkill` or `killall`.

## 3. Run the checks

- Make the first check show the setup is what you think (`git log --oneline --graph --all`, `ls -R`).
- Then run the command under test, one per line, each followed by `echo "exit=$?"`.
- Add the control case: the same check on a setup where the answer must be the other one. A proof with no control often proves nothing.
- Read files with the `read` tool and search with the `grep` tool, also inside `"$d"`.

## 4. Undo a step without destructive git

The guard blocks these in every repo, scratch repos too: `git reset --hard`, `git checkout -- <path>` or `git checkout .`, `git restore <path>`, `git clean -f`, `git branch -D`, `git stash drop`, `git update-ref -d`. Instead:

| need | do |
|---|---|
| start over | make a new clone: `git clone -q "$d/origin.git" "$d/work2"` |
| go back to a commit | `git switch -q -c retry <sha>` |
| drop a merged branch | `git branch -d <name>` (lowercase, no `-f`) |
| put a file back | `git show HEAD:<path> \| tee <path> >/dev/null` |

## 5. Clean up

```bash
trash "$d"; echo "exit=$?"; [ -e "$d" ] && echo "dir still there" || echo "dir gone"
```

It must print `exit=0` and `dir gone`. Trash it in the same turn you finish; never leave the dir for later. On a host without `trash`, ask the user before you delete anything.

## Instead of

| blocked | use |
|---|---|
| `cat f`, `head`, `tail` | `read` tool, or `sed -n '1,40p' f` |
| `grep`, `rg`, `... \| grep x` | `grep` tool, or `awk '/x/' f` |
| `find . -name '*.ts'` | `glob` tool, or `ls -R` |
| `echo x > f`, `cat > f <<EOF` | `write` tool, or `printf 'x\n' \| tee f >/dev/null` |
| `rm`, `rm -rf`, `trap '... rm ...'` | `trash "$d"` at the end |
| `node`, `bun` not found | `BUN_BE_BUN=1 omp` |
| `cmd &`, `nohup cmd` | bash tool with `name` |

## Reply (required)

Start with the answer in one sentence, then give the four labeled parts. This fits a host that wants short replies; do not drop a part to save words.

```
<the answer: yes, no, or how it behaves, in one sentence>
setup: <what the scratch dir held: repo, branches, files>
proof:
  $ <command>
  <output, trimmed to the lines that matter>
  exit=<n>
control: <command + output for the case with the other answer, or "none: <why>">
cleanup: trash <dir> -> exit=0, dir gone
```

Before you send, check the draft: `setup:`, `proof:`, `control:` and `cleanup:` are there, and each command in `proof:` has its `exit=` line. Add what is missing.

## Common mistakes

- `rm -rf "$d"` or `trap 'rm -rf …' EXIT` at the end of a long setup command: the guard blocks the whole call, so the setup never runs either.
- A here-doc `cat > file <<EOF` or `printf … > file` to write a fixture: blocked; use `write` or `| tee`.
- `… | grep x` or `… | head` to trim output: blocked; trim with `awk` or `sed -n`.
- `git reset --hard` or `git checkout -- .` to retry inside the scratch repo: blocked; make a new clone.
- After a block, the agent left the scratch dir behind. Always end with `trash "$d"`.
- Writing to a fixed `/tmp/foo` path: it collides with other agents and stays on disk.
- Answering from memory after the setup failed. If the proof did not run, say "not proven" and give the error.

On an underground host: the bash interceptor and the underground guard both run, and both match text, not intent. Without these guards (another host), the same steps still work; only the "blocked" notes do not apply.
