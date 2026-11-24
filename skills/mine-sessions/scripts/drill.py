#!/usr/bin/env python3
import argparse
import glob
import json
import os
import re
import time

p = argparse.ArgumentParser(
    description="Show each tool result that matches a regex, with the call that caused it and the "
    "call the agent made next. Use it to see how agents recover from one kind of waste. Read-only."
)
p.add_argument("match", help="regex searched in tool result text, e.g. 'underground guard'")
p.add_argument("--days", type=float, default=7)
p.add_argument("--project", default="", help="substring of the session cwd")
p.add_argument("--all", action="store_true", help="also match results that are not errors")
p.add_argument("--limit", type=int, default=20)
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
    name, args = call
    arg = args.get("command") or args.get("code") or args.get("path") or json.dumps(args)
    return f"{name}: " + " ".join(str(arg).split())[:200]


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
            for c in m.get("content") or []:
                if isinstance(c, dict) and c.get("type") == "toolCall":
                    calls[c.get("id")] = (c.get("name"), c.get("arguments") or {})
                    order.append(c.get("id"))
        elif m.get("role") == "toolResult":
            body = text_of(m.get("content"))
            if (a.all or m.get("isError")) and rx.search(body):
                order.append(("hit", m.get("toolCallId"), body))
    for i, item in enumerate(order):
        if not isinstance(item, tuple):
            continue
        _, cid, body = item
        nxt = next((calls[x] for x in order[i + 1:] if not isinstance(x, tuple)), None)
        hits += 1
        if nxt:
            next_names[nxt[0]] = next_names.get(nxt[0], 0) + 1
        if hits <= a.limit:
            print(f"## {os.path.basename(f)[:40]}  cwd={cwd}")
            print(f"call:   {short(calls.get(cid))}")
            print(f"result: {' '.join(body.split())[:200]}")
            print(f"next:   {short(nxt)}\n")
print(f"{hits} matching results; next call by tool: {next_names}")
