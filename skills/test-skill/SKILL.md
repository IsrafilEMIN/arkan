---
name: test-skill
description: "Test a skill draft with a small model before you ship it: does it trigger, are the steps followed, is the answer right. Use for \"test this skill\", \"does this skill work with a small model\", \"check whether the skill actually works\", \"try the skill with haiku\", or before you commit a new or changed SKILL.md. Runs headless omp on a fixture with planted answers and grades the JSONL."
---

# Test a skill

A skill that reads well can still fail: the model never loads it, a command in it is blocked on the host, or the model drops the output template. Run the draft with a weak model on a fixture whose right answer you planted, grade the run log against a rubric you wrote first, fix the skill, run again.

## Hard rules

1. Write `RUBRIC.md` before run 1. Never change it to fit an output you saw.
2. The prompt never names the skill and never says "use a skill". Write it as a user would.
3. When a run fails, fix the skill, not the fixture or the prompt. When the user asked only for a check, edit the lab copy and list the fixes in the report; when they asked you to make it work, edit the source and re-copy it.
4. Grade from the JSONL tool calls, not only from the final message.
5. Keep every file inside the lab dir. Trash the lab before your final reply, also when you offer more runs: put the numbers in the report first.
6. At most 3 haiku runs, then 1 sonnet run. Report every run, also the failed ones.

## 1. Make the lab

```bash
name=<skill-name>; src=<path to the draft skill dir>
L=$(mktemp -d "$HOME/skill-lab-$name.XXXX") && echo "L=$L"
mkdir -p "$L/skills" "$L/fixture" && cp -R "$src" "$L/skills/$name"
printf 'skills:\n  customDirectories:\n    - %s/skills\n' "$L" | tee "$L/overlay.yml"
```

If the user named a folder for test files, make the lab there instead. For guard-safe commands (no `rm`, no `cat >`, no `/tmp` literals), read `../scratch-proof/SKILL.md`.

The overlay loads the draft without installing it. A fixture that is a git repo hides a lab-level `.omp/skills`, because omp stops the project skill scan at the repo root; the overlay works from any `--cwd`.

## 2. Build the fixture

Make the smallest input on which the skill has one right answer that you know:

- **Ground truth:** what the model must find or do, planted on purpose (a dead module, a renamed config key, a divergent branch).
- **Decoys:** things a careless run gets wrong: an older error higher in the log, a safe pattern that looks unsafe, a module loaded only by name, vendored code.
- **State:** when the skill changes files or git state, write the fixture with a builder script (`$L/make-fixture.sh`) so you can trash and rebuild it before each run.

Build git fixtures with a bare origin and a clone as `../scratch-proof/SKILL.md` shows.

Source files that must hold code comments (TODOs, FIXMEs, disabled code): write them in bash with `printf '...' | tee "$L/fixture/src/a.py" >/dev/null`. On an underground host the `write` tool's no-comments guard rejects new comments, and rewriting them as strings changes what you test.

## 3. Write RUBRIC.md (before run 1)

Write `$L/RUBRIC.md` with the `write` tool:

```
# Rubric: <skill>
prompt: <exact prompt text>
trigger: the run reads skill://<name> before its first action
steps: <the skill steps that must show up as tool calls, in order>
must find: <each planted item>
must not flag: <each decoy>
forbidden: <actions that fail the run: edits, deletes, git state changes, writes outside the fixture>
output: <template parts that must be in the final message>
pass: trigger + all must-find + no forbidden action
```

## 4. Run

Write the prompt to `$L/prompt-1.txt` with the `write` tool, then:

```bash
omp -p --no-session --model anthropic/claude-haiku-5-5 --mode json \
  --config "$L/overlay.yml" --cwd "$L/fixture" --max-time 15m --max-cost 3 \
  "$(<"$L/prompt-1.txt")" > "$L/run-1.jsonl"; echo "exit=$?"
```

- A short skill takes 15–60 s; a long task can take minutes. When the bash tool moves the call to the background, wait for its result; do not start a second copy.
- Runs on one fixture that changes state must not run at the same time. Give each parallel run its own fixture copy.
- After the run, check the fixture: `git -C "$L/fixture" status --short` for a repo, `ls -R` otherwise.

## 5. Grade the run

```bash
python3 - "$L/run-1.jsonl" "$name" <<'PY'
import json, sys
path, skill = sys.argv[1], sys.argv[2]
BLOCK = ("is blocked", "underground guard", ": blocked")
calls, order, final, cost = {}, [], "", 0.0
for line in open(path):
    try: e = json.loads(line)
    except ValueError: continue
    t = e.get("type")
    if t == "tool_execution_start":
        calls[e["toolCallId"]] = [e["toolName"], json.dumps(e.get("args"))[:220], "?"]
        order.append(e["toolCallId"])
    elif t == "tool_execution_end" and e["toolCallId"] in calls:
        text = " ".join(c.get("text", "") for c in (e.get("result") or {}).get("content", []))
        calls[e["toolCallId"]][2] = ("BLOCKED" if any(b in text for b in BLOCK) else "error") if e.get("isError") else "ok"
    elif t == "message_end" and e["message"].get("role") == "assistant":
        m = e["message"]
        cost += ((m.get("usage") or {}).get("cost") or {}).get("total", 0)
        text = "".join(p.get("text", "") for p in m.get("content", []) if p.get("type") == "text")
        if text.strip(): final = text
trig = None
for i, k in enumerate(order, 1):
    tool, args, status = calls[k]
    hit = f"skill://{skill}" in args
    if hit and trig is None: trig = i
    print(f"{i:>3} {status:<7} {tool:<6} {args}" + ("   <== SKILL READ" if hit else ""))
st = [c[2] for c in calls.values()]
print(f"\ntrigger: {'call ' + str(trig) if trig else 'NO'} | calls: {len(st)} | blocked: {st.count('BLOCKED')} | errors: {st.count('error')} | cost: ${cost:.3f}")
print("\nFINAL MESSAGE:\n" + final)
PY
```

To grade many runs, save the script body with the `write` tool as `$L/grade.py` and run `python3 "$L/grade.py" "$L/run-N.jsonl" "$name"`; `printf ... > file` is blocked on an underground host.

Quick checks with `jq` alone:

```bash
jq -r 'select(.type=="tool_execution_start") | "\(.toolName) \(.args|tostring|.[0:160])"' "$L/run-1.jsonl"
jq -s '[.[] | select(.type=="tool_execution_end" and .isError) | (.result.content // [])[] | .text // "" | select(test("is blocked|underground guard|: blocked"))] | length' "$L/run-1.jsonl"
```

Grade each rubric line as pass or fail, with the call number or the quoted text as evidence. A blocked call that the skill told the model to run is a skill bug, even when the model recovered. Count a call as blocked only when `isError` is true: a read of a skill or log that merely mentions "is blocked" is not a block.

## 6. Fix and run again

| what failed | fix in the skill |
|---|---|
| no `skill://<name>` read | Lead the description with the exact phrases users type; omp shows a shortened description in the skill list. For skills about actions, start it with "Read this before you run any <X> command". |
| a command the skill gives was blocked | Replace it with the tool or form the host allows (see the table in `../scratch-proof/SKILL.md`). |
| "fix it" was taken as approval, or a change ran in the same call as a check | Put hard rules at the top: what needs a yes, and "one check per call, no change in the same call". |
| template parts missing | Mark the template as required and add "check the draft against it before you send". |
| stray files outside the fixture | Say where scratch files may go. |

After each edit to the source: `trash "$L/skills/$name" && cp -R "$src" "$L/skills/$name"`. Rebuild the fixture when the run changed it, then run again with the next number. Keep the prompt the same unless the rubric tests a second prompt (for example a "just fix it" one).

## 7. Cross-check with sonnet

Run once with `--model anthropic/claude-sonnet-5-5` on a fresh fixture. When sonnet fails where haiku passed, the skill is unclear, not the model weak.

## 8. Report, then clean up

Every part is required. Check the draft against it before you send.

```
skill: <path> (<n> lines)
verdict: works | works partly | does not work, in one sentence
| run | model | skill version | trigger | steps | result | blocked calls | forbidden actions |
changes: <run n -> what changed in the skill and why>
planted flaws found: <each, with call number or quoted text>
weaknesses: <what no run tested, what still fails>
cleanup: trash <lab> -> exit=<n>, dir gone
```

Write the report, then trash the lab in the same turn, then send the report as your reply:

```bash
trash "$L"; echo "exit=$?"; ls "$L" 2>&1
```

## Common mistakes

- `rsync -a --delete` or `shutil.rmtree` to re-copy the skill: the guard blocks both. Use `trash` then `cp -R`.
- Editing the skill and forgetting to re-copy it: the next run tests the old version.
- Running sonnet on a fixture that a haiku run already changed: that run is not valid. Rebuild first.
- A prompt that names the skill or says "use the skill": the trigger is not tested.
- Writing the rubric after run 1: the grade bends to the output.
- Grading only the final text: it hides blocked calls and checks that ran a change in the same call.
- Calling the trigger reliable after one pass: report it as n of N runs.
- Leaving the lab behind after a block or a failed run.
- Turning planted comments in a lab fixture into string literals after the `write` tool rejected them: the fixture no longer tests the real case. Only for fixture files inside the lab, write them with `printf | tee`.

On an underground host: `cat > file`, `echo > file`, `grep` and `rm` in bash are blocked; the snippets above avoid them. Without omp, use your harness's headless mode with JSON output and change the event names in the grader to match its log.
