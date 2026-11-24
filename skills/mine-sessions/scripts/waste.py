#!/usr/bin/env python3
import argparse
import collections
import glob
import json
import os
import re
import shlex
import time

p = argparse.ArgumentParser(
    description="Measure agent waste in omp session logs. Read-only, stdlib only. "
    "Prints markdown: failed and blocked calls by message, missing commands, bash sequences "
    "repeated across sessions, user corrections, advisor notes, and how the next thinking "
    "reacted to failed calls. Output can hold private data."
)
p.add_argument("--days", type=float, default=7)
p.add_argument("--project", default="", help="substring of the session cwd")
p.add_argument("--top", type=int, default=15)
p.add_argument("--count", default="", help="comma list of bash commands to count by session, e.g. 'mktemp,git init,trash'")
p.add_argument("--root", default=os.path.expanduser("~/.omp/agent/sessions"))
a = p.parse_args()

since = time.time() - a.days * 86400
files = [f for f in glob.glob(os.path.join(a.root, "**", "*.jsonl"), recursive=True)
         if os.path.getmtime(f) >= since and not os.path.basename(f).startswith("__")]

ENV = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=\S*$")
TWO_WORD = {"git", "gh", "omp", "npm", "pnpm", "yarn", "cargo", "go", "docker", "brew", "uv", "pip", "python3", "trash"}
NOT_FOUND = re.compile(r"(?:command not found: ?([\w.-]+)|([\w.-]+): command not found)")
GLUE = {"echo", "printf", "grep", "rg", "head", "tail", "cat", "ls", "cd", "wc", "sed", "awk", "sort", "uniq",
        "cut", "tr", "xargs", "jq", "true", "false", "sleep", "test", "pwd", "date", "basename", "dirname", "exit"}
CORRECTION = re.compile(r"\b(no|nope|don'?t|stop|wrong|not what|i said|i told|instead|why did you|again|useless|dude|revert|undo)\b", re.I)
KINDS = [("underground guard", "guard block"), ("blocked by tool policy", "tool-policy block")]
REACTIONS = [
    ("use trash", r"\btrash\b"),
    ("ask the owner", r"\b(ask|tell|give)\b.{0,25}\b(user|owner|parent|main agent)\b|exact command"
     r"|(won'?t|not|never) (try to )?(work|get|go) around"),
    ("unsure it ran", r"(not sure|unsure|unclear|don'?t know|no idea)\b.{0,50}\b(ran|run|executed|happened|created|succeeded)"
     r"|\bnothing (ran|happened)\b|never ran"),
    ("retry narrower", r"narrow|one (file )?at a time|per file|each file|individual|without -[rf]\b|git r[m]\b"
     r"|update-ref|\bREM\b|u[n]link|r[m]dir|r[m]tree"),
    ("leave files behind", r"\bleave (it|them|the|this|that|those)\b|left (in place|behind)|(isn'?t|not) a concern|harmless"
     r"|skip(ping)? (the )?clean|no need to clean|fine to leave|(in|under) \$?TMPDIR"),
    ("give up verification", r"verif\w* (is |are )?left|leave (the )?verif|(can'?t|cannot|unable to) (verify|test|run (the )?tests)"
     r"|main agent (will|to|can|should) (verify|run|test)|skip(ping)? (the )?(verif|tests)"),
    ("hunt for the binary", r"common locations|\bnvm\b|homebrew|\bmise\b|which (node|bun)|(find|locate|search for) (node|bun)"),
    ("switch tool or form", r"\b(use|using|switch to)\b.{0,20}\b(read|grep|glob|write|edit|find) tool|tool instead"
     r"|instead of (cat|grep|head|tail|rg|find|echo)|\b(awk|sed -n|python3?)\b"),
]
REACTIONS = [(n, re.compile(rx, re.I)) for n, rx in REACTIONS]
AGAIN = re.compile(r"\b(again|another)\b", re.I)


def kind_of(body):
    for needle, name in KINDS:
        if needle in body:
            return name
    return "command not found" if NOT_FOUND.search(body) else "other error"


def reaction(think):
    if not think.strip():
        return "no thinking"
    return next((n for n, rx in REACTIONS if rx.search(think)), "other (back to the task)")


def norm(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if lines and lines[0].startswith("Traceback"):
        lines = lines[-1:]
    s = " | ".join(lines[:2])
    s = re.sub(r"(?<![\w.])(~|/)[^\s'\"`:,)]+", "<path>", s)
    s = re.sub(r"\b[0-9a-f]{7,}\b|\d+", "N", s)
    s = re.sub(r"(['\"])[^'\"\s]{13,}\1", "<q>", s)
    return s[:110]


HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n.*?\n\s*\1\b", re.S)
WORD = re.compile(r"^[A-Za-z][\w.+-]*$")


def heads(cmd):
    out = []
    for part in re.split(r"\n|;|&&|\|\||\||\$\(|`", HEREDOC.sub("", cmd)):
        try:
            words = shlex.split(part, comments=True)
        except ValueError:
            words = part.split()
        while words and (ENV.match(words[0]) or words[0] in ("sudo", "time", "env", "then", "do", "else", "!")):
            words = words[1:]
        if not words:
            continue
        w = os.path.basename(words[0])
        if not WORD.match(w) or w in ("if", "fi", "done", "for", "while", "case", "esac", "in", "EOF"):
            continue
        if w in TWO_WORD and len(words) > 1 and WORD.match(words[1]):
            w += " " + words[1]
        out.append(w)
    return out


def text_of(content):
    if isinstance(content, str):
        return content
    return " ".join(c.get("text", "") for c in content or [] if isinstance(c, dict))


err = collections.Counter()
err_sessions = collections.defaultdict(set)
err_example = {}
err_next_failed = collections.Counter()
missing = collections.Counter()
missing_sessions = collections.defaultdict(set)
head_sessions = collections.defaultdict(set)
tri_sessions = collections.defaultdict(set)
corrections = {}
advice = []
react = collections.defaultdict(collections.Counter)
react_again = collections.Counter()
calls_total = errors_total = 0

for f in files:
    top_level = not re.match(r"\d{4}-\d\d-\d\dT", os.path.basename(os.path.dirname(f)))
    calls, pending, seq, user_turns, waiting = {}, None, [], 0, []
    for line in open(f, errors="ignore"):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        t = r.get("type")
        if t == "session" and a.project and a.project not in r.get("cwd", ""):
            break
        if t == "custom_message" and r.get("customType") == "advisor":
            for body in re.findall(r"<advisory[^>]*>(.*?)</advisory>", text_of(r.get("content")), re.S):
                advice.append(" ".join(body.split())[:200])
        if t != "message":
            continue
        m = r["message"]
        role = m.get("role")
        if role == "assistant":
            think = " ".join(c.get("thinking", "") for c in m.get("content") or []
                             if isinstance(c, dict) and c.get("type") == "thinking")
            for k in waiting:
                react[k][reaction(think)] += 1
                react_again[k] += bool(AGAIN.search(think))
            waiting = []
            for c in m.get("content") or []:
                if isinstance(c, dict) and c.get("type") == "toolCall":
                    calls_total += 1
                    args = c.get("arguments") or {}
                    calls[c.get("id")] = args
                    if c.get("name") == "bash" and isinstance(args.get("command"), str):
                        hs = heads(args["command"])
                        for h in hs:
                            head_sessions[h].add(f)
                        seq += [h for h in hs if h not in GLUE]
        elif role == "toolResult":
            body = text_of(m.get("content"))
            for x, y in NOT_FOUND.findall(body):
                name = x or y
                if re.search(r"[A-Za-z]", name) and name not in ("error", "line"):
                    missing[name] += 1
                    missing_sessions[name].add(f)
            if pending:
                if m.get("isError"):
                    err_next_failed[pending] += 1
                pending = None
            if m.get("isError"):
                errors_total += 1
                key = f"{m.get('toolName')}: {norm(body)}"
                err[key] += 1
                err_sessions[key].add(f)
                args = calls.get(m.get("toolCallId"), {})
                arg = args.get("command") or args.get("code") or args.get("path") or json.dumps(args)[:200]
                err_example.setdefault(key, " ".join(str(arg).split())[:120])
                pending = key
                waiting.append(kind_of(body))
        elif role == "user" and top_level:
            user_turns += 1
            msg = re.sub(r"<([\w-]+)[^>]*>.*?</\1>", "", text_of(m.get("content")), flags=re.S).strip()
            if user_turns > 1 and msg and len(msg) < 600 and CORRECTION.search(msg):
                corrections[" ".join(msg.split())[:160]] = None
    for i in range(len(seq) - 2):
        tri_sessions[" > ".join(seq[i:i + 3])].add(f)

T = a.top
subagents = sum(bool(re.match(r"\d{4}-\d\d-\d\dT", os.path.basename(os.path.dirname(f)))) for f in files)
print(f"# Agent waste, last {a.days:g} days: {len(files)} session files ({subagents} are subagent runs, counted as real work), "
      f"{calls_total} tool calls, {errors_total} failed or blocked\n")
print("## 1. Failed or blocked calls by message (each call is a wasted turn)\n")
print("| calls | sessions | next call failed too | tool: message | example input |\n|---|---|---|---|---|")
for k, n in err.most_common(T):
    ex = err_example[k].replace("|", "/").replace("`", "'")
    print(f"| {n} | {len(err_sessions[k])} | {err_next_failed[k]} | {k.replace('|', '/')} | `{ex}` |")
print("\n## 2. Missing commands\n")
for k, n in missing.most_common(T):
    print(f"- {k}: {n} times in {len(missing_sessions[k])} sessions")
print("\n## 3. Bash sequences repeated across sessions (manual procedures)\n")
for k, s in sorted(tri_sessions.items(), key=lambda kv: -len(kv[1]))[:T]:
    print(f"- {len(s)} sessions: {k}")
print("\n## 4. Bash commands by number of sessions that used them\n")
print(", ".join(f"{k} {len(s)}" for k, s in sorted(head_sessions.items(), key=lambda kv: -len(kv[1]))[:T * 2]))
if a.count:
    print("\nAsked for: " + ", ".join(f"{k} {len(head_sessions.get(k, ()))}" for k in a.count.split(",")))
print(f"\n## 5. Possible user corrections ({len(corrections)}; many are false hits, read them)\n")
for c in list(corrections)[-T:]:
    print(f"- {c}")
print(f"\n## 6. Advisor notes ({len(advice)}; recurring ones point at repeated mistakes)\n")
for c in advice[-T:]:
    print(f"- {c}")
print("\n## 7. Reaction in the next thinking after a failed or blocked call\n")
print("Rough regex classes, first match wins. They show which belief to look for; read the thinking with drill.py.\n")
print("| kind | failed calls | reactions | next thinking says again/another |\n|---|---|---|---|")
for k, c in sorted(react.items(), key=lambda kv: -sum(kv[1].values())):
    print(f"| {k} | {sum(c.values())} | {', '.join(f'{n} {v}' for n, v in c.most_common())} | {react_again[k]} |")
