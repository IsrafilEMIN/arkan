---
name: mine-sessions
description: "Measure what slows agents down in past omp sessions (blocked and failed tool calls, retry loops, missing commands, repeated manual procedures, user corrections, advisor notes) and turn the costliest item into a skill that removes it. Use for 'what slows agents down', 'go through my sessions', 'mine my sessions for skills', 'turn past sessions into skills', 'what skills should we make', or any review of agent history from the last N days. Read this before you open any session log."
---

# Mine sessions

Find the work agents waste on this setup, measure it, and fix the costliest item with a skill. A good skill removes wasted calls, dead ends and repeated manual steps. A skill that teaches what a model already knows is useless, however often the topic comes up.

## Rules

1. Measure, never list topics. Every candidate needs a number from the logs: wasted calls, sessions hit, retries.
2. Session logs are read-only. Never edit, move or delete them.
3. Stop after the report and ask the user which candidate to build. Do not write a skill, a file in a skill folder, or a plan file before they answer.
4. Keep the logs' private data (names, home paths, hosts, tokens, repo names) out of any skill you write.
5. Scratch output goes under `$TMPDIR` (or the folder the user names), never in the repo or `/tmp`. Send script output to a file there and open it with the `read` tool. Never pipe it into `head`, `tail`, `grep` or `cat`: the interceptor blocks the whole bash call.

## 1. Measure the waste

The scripts sit in `scripts/` next to this SKILL.md. The header of the `read` that loaded this skill shows its path. Run with python 3, stdlib only, read-only. Add `--project <cwd text>` to narrow the window to one project:

```bash
python3 <skill-dir>/scripts/waste.py --days 3
```

It prints six sections: failed or blocked calls grouped by message (calls, sessions, how often the next call failed too, an example input), missing commands, bash sequences that repeat across sessions, bash commands by session count, possible user corrections, and advisor notes. Three days runs in a few seconds; 30 days takes about 1.5 minutes. Use its counts as they are. Do not write your own counter to check them; drill into a row instead.

Then see how agents recover from each top row. The next call shows whether they found the fix or wasted more turns:

```bash
python3 <skill-dir>/scripts/drill.py 'underground guard' --days 3 --limit 10
```

`drill.py` takes a regex over error results (`--all` adds non-error results) and prints the call, the result and the next call, then counts the next call by tool.

For titles, recaps and the user's own prompts, use eval's `archive`. All methods are async. `sessions` gives id, file, project, title and recap; `search` matches user and assistant text only, not tool calls; `session` gives prompts, recap and file:

```python
s = await archive.sessions(project="*", limit=50)
hits = await archive.search("none of these are useful", project="*")
one = await archive.session(s[0]["id"])
```

Without `archive`, the files are `~/.omp/agent/sessions/<project-slug>/<time>_<id>.jsonl`. Subagent runs sit in a folder with the parent's name and are named after the agent (`Main.jsonl`, `Scout.jsonl`). They are real work by the same agents: count them, never drop them as test runs. Each row is JSON: `type` `session` (has `cwd`), `message` (`message.role` is `user`, `assistant` with `toolCall` items, or `toolResult` with `toolName`, `isError`, `content[].text`), and `custom_message` with `customType` `advisor`.

## 2. Turn rows into candidates

For each top row, write one line: what the agent did, what it cost, and what it should have done. Group rows with one cause. Count waste as calls plus the follow-up calls that also failed.

Then group by task, not only by message. The `call` lines from `drill.py` show what the agents were doing when they hit the wall. When many blocks come from one kind of task (building a throwaway repo to prove a behavior, testing a skill, cleaning up temp files), a skill for that task removes those blocks and the task's other manual steps too. Count how many sessions did that task by hand with `waste.py --count 'mktemp,git init,trash'` (any commands, comma-separated). Never put a delete command name in the list: on an underground host the guard blocks the whole call. The guard rows in section 1 already count deletes.

Sort the candidates by measured cost. Then decide for each where the fix belongs:

| fix | when |
|---|---|
| skill | the agent picks the wrong tool, command or method in a task it can name ("prove this in a temp repo", "test this skill"), and the right method is known and exact |
| always-on rule | a one-line fix every session needs, whatever the task (for example "use the read tool, not cat"); a skill loads only when its description matches, so suggest an AGENTS.md line |
| config or hook | a tool is missing, a guard message is unclear, a default is wrong; tell the user, do not write a skill |
| nothing | one bad session, or the cost is small |

## 3. Reject generic candidates

For each skill candidate ask: would a strong model with no skill already do this right on this host? If yes, reject it. Reject also:

- topics that come up often but cost no wasted calls (git triage, ssh debugging, code review, "map a codebase");
- anything an existing skill covers (list the installed skills first);
- advice without exact commands for this host.

Worked example from this setup. A first batch of 11 topic skills (git triage, ssh debugging, machine health, backup check, branch triage, codebase map, secrets audit and others) was rejected by the user: "none of are useful skills". A second pass measured instead: 683 bash calls blocked by the tool-policy interceptor, 284 deletes blocked by the guard, 77 `node`/`bun: command not found`, 162 sessions that built throwaway repos by hand, and after a blocked delete the next call used `trash` 2 times in about 190. Those numbers gave skills that remove the waste (a throwaway-proof recipe, a skill test harness), not skills about topics.

## 4. Report and stop (required)

Send this, then stop and wait for the user's pick:

```
Window: <N days, M session files, C tool calls, E failed or blocked>

| # | candidate | waste (calls / sessions) | evidence | fix type |
|---|---|---|---|---|
| 1 | ... | 175 / 135 | temp-file delete blocked by guard; next call used trash 2 times in 190 | skill |

Rejected: <candidate> — <reason: generic know-how / no measured waste / covered by <skill> / config fix>
Question: which candidate should I build?
```

Check before you send: every row has a number from the script; the rejected list is there; no skill file was written.

## 5. Build, test, clean up (after the user picks)

1. Write the skill in the repo's style. Open with hard rules from the waste you measured, give the exact commands that work on this host, and put host-only facts in "On an underground host:" notes with a plain fallback.
2. Test it with a weak model as in [test-skill](../test-skill/SKILL.md). Build fixtures and throwaway repos as in [scratch-proof](../scratch-proof/SKILL.md). Plant the waste you measured in the fixture, and add "blocked or failed calls" to the rubric, so the run shows whether the skill removes it.
3. Trash all test material: `trash "$lab"` and any `$TMPDIR` output. Report what you trashed.

## On an underground host

- The bash interceptor blocks the whole call when any command in it starts with `cat`, `head`, `tail`, `grep`, `rg`, `find -name`, or an `echo`/`printf` redirect. Read script output with the `read` tool or print it from python.
- The guard matches text, not intent: an eval cell or bash call is blocked when it only mentions a recursive delete, even inside a regex or a string. To find guard blocks in logs, match the guard's own message (`underground guard`), not the command text. Delete with `trash <path>`.
- `node` and `bun` are not on PATH. Run TS with `BUN_BE_BUN=1 omp file.ts`.

## Common mistakes

- Ranking by how often a topic appears. Frequency of `git log` says nothing; blocked and retried calls do.
- Writing the skill before the user picks. The first batch was 11 skills nobody wanted.
- Counting the current session. Its own analysis output matches every pattern; skip it or use `--days` to frame the window.
- Pasting raw log lines into a public skill. Rewrite them without names, paths or hosts.
- Leaving the lab, fixtures or `$TMPDIR` output behind after testing.
