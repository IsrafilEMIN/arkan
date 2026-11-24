#!/usr/bin/env python3
import argparse
import glob
import json
import os
import re
import time

p = argparse.ArgumentParser(
    description="Show each tool result that matches a regex, with the call that caused it, the thinking "
    "before that call (the plan and belief), the call the agent made next and the thinking after the "
    "result (the reaction). Use it to see how and why agents recover from one kind of waste. Read-only. "
    "Thinking can hold private data: paraphrase it, never paste it into a skill."
)
p.add_argument("match", help="regex searched in tool result text, e.g. 'underground guard'")
p.add_argument("--days", type=float, default=7)
p.add_argument("--project", default="", help="substring of the session cwd")
p.add_argument("--all", action="store_true", help="also match results that are not errors")
p.add_argument("--limit", type=int, default=20)
p.add_argument("--no-think", action="store_true", help="hide the thinking lines")
p.add_argument("--chars", type=int, default=300, help="trim each thinking line to this many characters")
p.add_argument("--root", default=os.path.expanduser("~/.omp/agent/sessions"))
a = p.parse_args()

rx = re.compile(a.match, re.I)
since = time.time() - a.days * 86400
files = sorted((f for f in glob.glob(os.path.join(a.root, "**", "*.jsonl"), recursive=True)
                if os.path.getmtime(f) >= since and not os.path.basename(f).startswith("__")),
               key=os.path.getmtime, reverse=True)


def text_of(content):
    if isinstance(content, str):
        return content
    return " ".join(c.get("text", "") for c in content or [] if isinstance(c, dict))


def short(call):
    if not call:
        return "(none)"
    name, args = call[0], call[1]
    arg = args.get("command") or args.get("code") or args.get("path") or json.dumps(args)
    return f"{name}: " + " ".join(str(arg).split())[:200]


def trim(text, n):
    s = " ".join(text.split())
    if not s:
        return "(none)"
    return s if len(s) <= n else s[:n // 2] + " ... " + s[-(n // 2):]


hits = 0
next_names = {}
for f in files:
    calls, order, cwd, project_ok = {}, [], "", True
    for line in open(f, errors="ignore"):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("type") == "session":
            cwd = r.get("cwd", "")
            project_ok = a.project in cwd
        if not project_ok or r.get("type") != "message":
            continue
        m = r["message"]
        if m.get("role") == "assistant":
            content = [c for c in m.get("content") or [] if isinstance(c, dict)]
            think = " ".join(c.get("thinking", "") for c in content if c.get("type") == "thinking")
            order.append(("think", think))
            for c in content:
                if c.get("type") == "toolCall":
                    calls[c.get("id")] = (c.get("name"), c.get("arguments") or {}, think)
                    order.append(c.get("id"))
        elif m.get("role") == "toolResult":
            body = text_of(m.get("content"))
            if (a.all or m.get("isError")) and rx.search(body):
                order.append(("hit", m.get("toolCallId"), body))
    for i, item in enumerate(order):
        if not (isinstance(item, tuple) and item[0] == "hit"):
            continue
        _, cid, body = item
        rest = order[i + 1:]
        nxt = next((calls[x] for x in rest if not isinstance(x, tuple)), None)
        after = next((x[1] for x in rest if isinstance(x, tuple) and x[0] == "think"), "")
        hits += 1
        if nxt:
            next_names[nxt[0]] = next_names.get(nxt[0], 0) + 1
        if hits <= a.limit:
            call = calls.get(cid)
            print(f"## {os.path.basename(f)[:40]}  cwd={cwd}")
            if not a.no_think:
                print(f"thought before: {trim(call[2] if call else '', a.chars)}")
            print(f"call:   {short(call)}")
            print(f"result: {' '.join(body.split())[:200]}")
            if not a.no_think:
                print(f"thought after:  {trim(after, a.chars)}")
            print(f"next:   {short(nxt)}\n")
print(f"{hits} matching results; next call by tool: {next_names}")
