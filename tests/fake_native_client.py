import json
import os
import sys
from pathlib import Path

root = Path(sys.argv[1])
name = Path(sys.argv[2]).name
args = sys.argv[3:]
plan = json.loads((root / f"{name}.plan.json").read_text())
prompt = sys.stdin.read()
home = os.environ.get("CODEX_HOME")
auth = Path(home) / "auth.json" if home else None
entry = {
    "argv": args,
    "env": dict(os.environ),
    "cwd_entries": os.listdir("."),
    "prompt": prompt,
    "home": home,
    "auth": json.loads(auth.read_text()) if auth and auth.exists() else None,
    "auth_mode": auth.stat().st_mode & 0o777 if auth and auth.exists() else None,
}
status_call = args[:2] == ["auth", "status"]
log_name = f"{name}.auth.log" if status_call else f"{name}.log"
with (root / log_name).open("a") as handle:
    handle.write(json.dumps(entry) + "\n")
if status_call:
    status_plan = plan.get("auth", {})
    token = bool(os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"))
    default = {
        "loggedIn": True,
        "authMethod": "oauth_token" if token else "claude.ai",
        "apiProvider": "firstParty",
        "subscriptionType": None if token else "pro",
    }
    sys.stdout.write(status_plan["raw"] if "raw" in status_plan else json.dumps(status_plan.get("status", default)))
    sys.stderr.write(status_plan.get("stderr", ""))
    sys.exit(status_plan.get("code", 0))
tools = json.loads(prompt.split("TOOLS:\n", 1)[1].split("\n\nCONVERSATION:\n", 1)[0])
terminal = tools[-1]["function"]["name"] if tools else ""
message = plan.get("message")
if message is None and terminal in plan.get("replies", {}):
    arguments = json.dumps(plan["replies"][terminal])
    message = {"content": "", "tool_calls": [{"id": "call-1", "type": "function", "function": {"name": terminal, "arguments": arguments}}]}
if name == "codex":
    refresh = plan.get("refresh")
    if isinstance(refresh, str):
        auth.write_text(refresh)
    elif refresh is not None:
        auth.write_text(json.dumps({**json.loads(auth.read_text()), **refresh}))
    for event in plan.get("events", []):
        print(json.dumps(event))
    if message is not None:
        out = Path(args[args.index("--output-last-message") + 1])
        out.write_text(message if isinstance(message, str) else json.dumps(message))
elif "raw" in plan:
    sys.stdout.write(plan["raw"])
else:
    print(json.dumps(plan.get("result") or {"type": "result", "subtype": "success", "is_error": False, "result": "", "structured_output": message}))
sys.stderr.write(plan.get("stderr", ""))
sys.exit(plan.get("code", 0))
