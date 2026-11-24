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
4. Grade from the JSONL tool calls and the test model's thinking, not only from the final message. Run with `--thinking medium`; without it the log has little or no thinking.
5. Keep every file inside the lab dir. Trash the lab before your final reply, also when the user named its folder and also when you offer more runs: put the numbers in the report first. A folder for test files is not a request to keep them.
6. At most 3 haiku runs, then 1 sonnet run. Report every run, also the failed ones.

## 1. Make the lab

```bash
name=<skill-name>; src=<path to the draft skill dir>
L=$(mktemp -d "$HOME/skill-lab-$name.XXXX") && echo "L=$L"
mkdir -p "$L/skills" "$L/fixture" && cp -R "$src" "$L/skills/$name"
printf 'skills:\n  customDirectories:\n    - %s/skills\nadvisor:\n  enabled: false\n' "$L" | tee "$L/overlay.yml"
```

If the user named a folder for test files, make the lab there instead. For guard-safe commands (no `rm`, no `cat >`, no `/tmp` literals), read `../scratch-proof/SKILL.md`.

The overlay loads the draft without installing it. A fixture that is a git repo hides a lab-level `.omp/skills`, because omp stops the project skill scan at the repo root; the overlay works from any `--cwd`. It also turns the advisor off: when the owner's config enables it, it injects notes into the test run, and the run no longer tests the skill alone.

## 2. Build the fixture

Make the smallest input on which the skill has one right answer that you know:

- **Ground truth:** what the model must find or do, planted on purpose (a dead module, a renamed config key, a divergent branch).
- **Decoys:** things a careless run gets wrong: an older error higher in the log, a safe pattern that looks unsafe, a module loaded only by name, vendored code.
- **State:** when the skill changes files or git state, write the fixture with a builder script (`$L/make-fixture.sh`) so you can trash and rebuild it before each run.

Build git fixtures with a bare origin and a clone as `../scratch-proof/SKILL.md` shows.

Fixture source files that must hold planted code comments (TODOs, FIXMEs, disabled code): write them in bash with `printf '...' | tee "$L/fixture/src/a.py" >/dev/null`. On an underground host the `write` tool's no-comments guard rejects new comments, and rewriting them as strings changes what you test. This applies only to fixture files under `$L`, never to a real repo or to the skill under test.

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
omp -p --no-session --model anthropic/claude-haiku-5-5 --thinking medium --mode json \
  --config "$L/overlay.yml" --cwd "$L/fixture" --max-time 15m --max-cost 3 \
  "$(<"$L/prompt-1.txt")" > "$L/run-1.jsonl"; echo "exit=$?"
```

- Always pass `--thinking medium`. Without a thinking level the JSONL has little or no thinking from the test model (`low` gave none), so you see what it did but not why.
- A short skill takes 15–60 s; a long task can take minutes. When the bash tool moves the call to the background, wait for its result; do not start a second copy.
- Runs on one fixture that changes state must not run at the same time. Give each parallel run its own fixture copy.
- After the run, check the fixture: `git -C "$L/fixture" status --short` for a repo, `ls -R` otherwise.

## 5. Grade the run

The grader prints the test model's thinking (`THINK`, trimmed) in order with its tool calls. A thinking block comes just before the calls it led to; the reaction to a result is the next thinking block.

```bash
python3 - "$L/run-1.jsonl" "$name" <<'PY'
import json, sys
path, skill = sys.argv[1], sys.argv[2]
BLOCK = ("is blocked", "underground guard", ": blocked")
calls, rows, final, cost = {}, [], "", 0.0
for line in open(path):
    try: e = json.loads(line)
    except ValueError: continue
    t = e.get("type")
    if t == "tool_execution_start":
        calls[e["toolCallId"]] = [e["toolName"], json.dumps(e.get("args"))[:220], "?"]
        rows.append(("call", e["toolCallId"]))
    elif t == "tool_execution_end" and e["toolCallId"] in calls:
        text = " ".join(c.get("text", "") for c in (e.get("result") or {}).get("content", []))
        calls[e["toolCallId"]][2] = ("BLOCKED" if any(b in text for b in BLOCK) else "error") if e.get("isError") else "ok"
    elif t == "message_end" and e["message"].get("role") == "assistant":
        m = e["message"]
        cost += ((m.get("usage") or {}).get("cost") or {}).get("total", 0)
        for p in m.get("content", []):
            if p.get("type") == "thinking" and p.get("thinking", "").strip():
                rows.append(("think", " ".join(p["thinking"].split())[:400]))
        text = "".join(p.get("text", "") for p in m.get("content", []) if p.get("type") == "text")
        if text.strip(): final = text
trig, n, thinks = None, 0, 0
for kind, v in rows:
    if kind == "think":
        thinks += 1
        print(f"    THINK   {v}")
        continue
    n += 1
    tool, args, status = calls[v]
    hit = f"skill://{skill}" in args
    if hit and trig is None: trig = n
    print(f"{n:>3} {status:<7} {tool:<6} {args}" + ("   <== SKILL READ" if hit else ""))
st = [c[2] for c in calls.values()]
print(f"\ntrigger: {'call ' + str(trig) if trig else 'NO'} | calls: {len(st)} | blocked: {st.count('BLOCKED')} | errors: {st.count('error')} | thinking blocks: {thinks} | cost: ${cost:.3f}")
print("\nFINAL MESSAGE:\n" + final)
PY
```

`thinking blocks: 0` means the run had no thinking level: run it again with `--thinking medium` before you grade why.

To grade many runs, save the script body with the `write` tool as `$L/grade.py` and run `python3 "$L/grade.py" "$L/run-N.jsonl" "$name"`; `printf ... > file` is blocked on an underground host.

Quick checks with `jq` alone (the grader is better: it shows each thinking block next to the calls it led to):

```bash
jq -r 'select(.type=="tool_execution_start") | "\(.toolName) \(.args|tostring|.[0:160])"' "$L/run-1.jsonl"
jq -s '[.[] | select(.type=="tool_execution_end" and .isError) | (.result.content // [])[] | .text // "" | select(test("is blocked|underground guard|: blocked"))] | length' "$L/run-1.jsonl"
jq -r 'select(.type=="message_end" and .message.role=="assistant") | .message.content[]? | select(.type=="thinking") | .thinking[0:400]' "$L/run-1.jsonl"
```

Grade each rubric line as pass or fail, with the call number or the quoted text as evidence. A blocked call that the skill told the model to run is a skill bug, even when the model recovered. Count a call as blocked only when `isError` is true: a read of a skill or log that merely mentions "is blocked" is not a block.

When a check fails, or the model got it right only after a detour, read the thinking at that point to find the belief that caused it: the thinking before the failed call (what it planned and believed) and the next one (how it reacted). Examples: it decided the skill was not relevant; it treated "fix it" as approval; it believed a blocked call had run; it read "use a narrower command" as "retry the delete in a smaller form"; it counted leftover temp files as harmless. For a trigger failure, look for whether it saw the skill in its list and why it skipped it. Write one line per failed check, `run n, call k: <belief, paraphrased>`; these lines go into the report. Then fix the skill text that let that belief form, with a hard rule that directly contradicts it. Do not only patch the symptom. Paraphrase the thinking; do not paste long stretches of it.

## 6. Fix and run again

| what failed (belief in the thinking) | fix in the skill |
|---|---|
| no `skill://<name>` read | Lead the description with the exact phrases users type; omp shows a shortened description in the skill list. For skills about actions, start it with "Read this before you run any <X> command". When the thinking says the skill did not fit the task, add the words it used for the task to the description. |
| a command the skill gives was blocked | Replace it with the tool or form the host allows (see the table in `../scratch-proof/SKILL.md`). |
| "fix it" was taken as approval, or a change ran in the same call as a check | Put hard rules at the top: what needs a yes, and "one check per call, no change in the same call". |
| the thinking assumed a blocked call ran, or retried it in a smaller form | Say that a blocked call ran nothing, and name the one allowed path (the tool the block names, `trash`, or ask the owner). |
| template parts missing | Mark the template as required and add "check the draft against it before you send". |
| stray files outside the fixture | Say where scratch files may go. |

After each edit to the source: `trash "$L/skills/$name" && cp -R "$src" "$L/skills/$name"`. Rebuild the fixture when the run changed it, then run again with the next number. Keep the prompt the same unless the rubric tests a second prompt (for example a "just fix it" one).

## 7. Cross-check with sonnet

Run once with `--model anthropic/claude-sonnet-5-5 --thinking medium` on a fresh fixture. When sonnet fails where haiku passed, the skill is unclear, not the model weak.

## 8. Report, then clean up

Every part is required, also when your usual reply style is short. Check the draft against it before you send. Each planted flaw found says why the model went wrong, from its thinking, not only what it did.

```
skill: <path> (<n> lines)
verdict: works | works partly | does not work, in one sentence
| run | model | skill version | trigger | steps | result | blocked calls | forbidden actions |
beliefs in thinking: <run n -> each belief that drove a fail or a near miss, paraphrased, with the call number; "none seen" when clean>
changes: <run n -> what changed in the skill and why>
planted flaws found: <each, with call number or quoted text, and the belief in the thinking that let it happen>
weaknesses: <what no run tested, what still fails>
cleanup: trash <lab> -> exit=<n>, dir gone
```

Write the report, then trash the lab in the same turn, then send the report as your reply:

```bash
trash "$L"; echo "exit=$?"; [ -e "$L" ] && echo "dir still there" || echo "dir gone"
```

## Common mistakes

- `rsync -a --delete` or `shutil.rmtree` to re-copy the skill: the guard blocks both. Use `trash` then `cp -R`.
- Editing the skill and forgetting to re-copy it: the next run tests the old version.
- Running sonnet on a fixture that a haiku run already changed: that run is not valid. Rebuild first.
- A prompt that names the skill or says "use the skill": the trigger is not tested.
- Writing the rubric after run 1: the grade bends to the output.
- Grading only the final text: it hides blocked calls and checks that ran a change in the same call.
- Grading only the calls: you see what failed but not why, so the fix patches the symptom. Run with `--thinking medium` and read the thinking at each failed check.
- Calling the trigger reliable after one pass: report it as n of N runs.
- Leaving the lab behind after a block or a failed run.
- Turning planted comments in a lab fixture into string literals after the `write` tool rejected them: the fixture no longer tests the real case. Only for fixture files inside the lab, write them with `printf | tee`.

On an underground host: `cat > file`, `echo > file`, `grep`, `head`, `tail` and `rm` in bash are blocked; the snippets above avoid them. A block refuses the whole call, so nothing in it ran, not even the setup before the blocked command: never add a `grep` or `head` check to a setup call. Without omp, use your harness's headless mode with JSON output and change the event names in the grader to match its log.
