#!/bin/bash
set -u

here=$(cd -P "$(dirname "$0")" && pwd -P)
skill=$(dirname "$here")
work=$(mktemp -d "${TMPDIR:-/tmp}/freeze-test.XXXXXX") || exit 1
work=$(cd -P "$work" && pwd -P)
trap 'rm -rf "$work"' EXIT

export HOME="$work/home"
export FREEZE_STATE_DIR="$work/state"
mkdir -p "$HOME/.agents/skills/freeze/scripts" "$work/proj/frozen" "$work/outside"
ln -s "$here/freeze-guard.sh" "$HOME/.agents/skills/freeze/scripts/freeze-guard.sh"
printf 'x\n' >"$work/outside/file"
printf 'x\n' >"$work/proj/frozen/inside"
ln -s "$work/outside/file" "$work/proj/frozen/link"
ln -s ../../outside/file "$work/proj/frozen/rel-link"
ln -s "$work/outside/new" "$work/proj/frozen/dangling"
ln -s "$work/proj/frozen/inside" "$work/proj/frozen/inner-link"
ln -s loop-b "$work/proj/frozen/loop-a"
ln -s loop-a "$work/proj/frozen/loop-b"

guard="$here/freeze-guard.sh"
fail=0

(cd "$work/proj" && "$guard" arm frozen) || { printf 'freeze-test: arm failed\n' >&2; exit 1; }

expect_guard() {
  _want="$1"
  shift
  (cd "$work/proj" && "$guard" "$@" >/dev/null 2>&1)
  _got=$?
  if [ "$_got" = "$_want" ]; then
    printf 'ok   guard %s -> %s\n' "$*" "$_got"
  else
    printf 'FAIL guard %s -> %s, want %s\n' "$*" "$_got" "$_want"
    fail=1
  fi
}

expect_guard 0 write frozen/inside
expect_guard 0 write frozen/new-file
expect_guard 0 write frozen/inner-link
expect_guard 2 write "$work/outside/file"
expect_guard 2 write frozen/link
expect_guard 2 write frozen/rel-link
expect_guard 2 write frozen/dangling
expect_guard 0 write frozen/loop-a

hook_case() {
  _want="$1"
  _payload="$2"
  printf '%s' "$_payload" | (cd "$work/proj" && "$guard" hook >/dev/null 2>&1)
  _got=$?
  if [ "$_got" = "$_want" ]; then
    printf 'ok   hook %s -> %s\n' "$_payload" "$_got"
  else
    printf 'FAIL hook %s -> %s, want %s\n' "$_payload" "$_got" "$_want"
    fail=1
  fi
}

hook_case 2 "{\"tool_name\":\"apply_patch\",\"tool_input\":{\"patch\":\"*** Update File: $work/outside/file\"}}"
hook_case 2 "{\"tool_name\":\"edit\",\"tool_input\":{\"input\":\"*** Begin Patch\\n*** Add File: $work/outside/x\\n+a\\n*** End Patch\"}}"
hook_case 0 "{\"tool_name\":\"edit\",\"tool_input\":{\"input\":\"*** Begin Patch\\n*** Add File: $work/proj/frozen/x\\n+echo a > $work/outside/y\\n*** End Patch\"}}"

command -v node >/dev/null 2>&1 || { printf 'FAIL node not found, adapter cases skipped\n'; exit 1; }
cp "$skill/adapters/freeze.ts" "$work/freeze.mjs"
cat >"$work/run.mjs" <<'EOF'
const mod = await import(process.argv[2]);
const cases = JSON.parse(process.argv[3]);
let handler;
mod.default({ on: (name, fn) => { if (name === "tool_call") handler = fn; } });
let fail = 0;
for (const c of cases) {
	const out = handler({ toolName: c.tool, input: c.input }, { cwd: process.argv[4] });
	const got = out && out.block === true ? "block" : "pass";
	console.log((got === c.want ? "ok   " : "FAIL ") + "adapter " + JSON.stringify({ tool: c.tool, input: c.input }) + " -> " + got + (got === c.want ? "" : ", want " + c.want));
	if (got !== c.want) fail = 1;
}
process.exit(fail);
EOF
out="$work/outside/file"
cases=$(jq -cn --arg out "$out" --arg in "$work/proj/frozen/inside" '[
  {tool:"read", input:{path:$out}, want:"pass"},
  {tool:"grep", input:{pattern:"x", path:$out}, want:"pass"},
  {tool:"find", input:{pattern:"*", path:$out}, want:"pass"},
  {tool:"glob", input:{pattern:"*", path:$out}, want:"pass"},
  {tool:"ls", input:{path:$out}, want:"pass"},
  {tool:"lsp", input:{action:"diagnostics", file:$out}, want:"pass"},
  {tool:"lsp", input:{action:"rename", file:$out, new_name:"y"}, want:"block"},
  {tool:"write", input:{path:$out, content:"y"}, want:"block"},
  {tool:"edit", input:{path:$out, old_string:"x", new_string:"y"}, want:"block"},
  {tool:"write", input:{path:$in, content:"y"}, want:"pass"},
  {tool:"new_write_tool", input:{file_path:$out}, want:"block"},
  {tool:"apply_patch", input:{patch:("*** Update File: " + $out)}, want:"block"},
  {tool:"edit", input:{input:("*** Begin Patch\n*** Update File: " + $out + "\n*** End Patch")}, want:"block"},
  {tool:"edit", input:{input:("*** Begin Patch\n*** Update File: " + $in + "\n*** End Patch")}, want:"pass"},
  {tool:"bash", input:{command:("echo y > " + $out)}, want:"block"}
]')
node "$work/run.mjs" "$work/freeze.mjs" "$cases" "$work/proj" || fail=1

[ "$fail" = 0 ] && printf 'freeze-test: ok\n'
exit "$fail"
