#!/usr/bin/env python3
import hashlib, re, shlex, shutil, subprocess, sys

USAGE = "\n".join([
    'ISA diff per function: proves the default path of a custom engine build is unchanged.',
    '',
    '  python3 scripts/isa_diff.py OLD NEW [--tool auto|cuobjdump|llvm-objdump] [--cmd "TEMPLATE {file}"]',
    '',
    'OLD, NEW: executables, shared libraries (.so), .cubin or .o files of the same tree, before and after the change.',
    'Compare against a FRESH compile of the same tree: stale objects in reused build dirs cause false diffs.',
    '',
    'Tools (OLD picks the tool under auto; NEW uses the same one):',
    '  cuobjdump     NVIDIA: cuobjdump -sass per kernel and arch, plus cuobjdump -res-usage (REG, STACK, SHARED,',
    '                LOCAL per kernel; a change counts as a difference).',
    '  llvm-objdump  llvm-objdump -d --no-show-raw-insn (auto falls back to GNU objdump when llvm-objdump is missing).',
    '  --cmd         any disassembler that prints to stdout, e.g. --cmd "llvm-objdump -d --offloading {file}" or a',
    '                vendor tool; {file} is replaced by the path (appended when absent). Output may use either the',
    '                cuobjdump "Function : NAME" headers or the objdump "ADDR <NAME>:" headers.',
    '',
    'Normalization before hashing each function: drop instruction addresses/offsets and encodings (/*0040*/,',
    '/* 0x... */, leading "ADDR:" and raw bytes), comments (//, " # ", ";" after the instruction), whitespace and',
    'column padding; absolute addresses before <symbol> and %rip displacements become ADDR; per-file hashes and',
    'anonymous-namespace path parts in mangled names (_INTERNAL_<hash>_<len>_<file>_<hash>, __nv_static_..,',
    '_GLOBAL__N__<len>_<file>_<hash>, ..._ii_<hash>; <hash> = 8 or more hex digits, either case) become fixed tokens.',
    '',
    'Output: one verdict line, counts of identical / differ / new / removed functions, then each differing',
    'function with instruction counts and FMA-type instruction counts old -> new (FMA contraction breaks bit',
    'identity), resource changes, and removed names. New functions are allowed.',
    'Exit: 0 when no existing function differs or is removed, 1 otherwise, 2 usage or tool error.',
])

SASS_HEAD = re.compile(r"^\s*Function\s*:\s*(\S+)\s*$")
SASS_ARCH = re.compile(r"^\s*(?:code for|arch\s*=)\s*(sm_\w+)")
SASS_INSN = re.compile(r"^\s*/\*[0-9a-fA-F]{4,}\*/")
SASS_LABEL = re.compile(r"^\s*(\.L_x_\d+:)")
OBJ_HEAD = re.compile(r"^([0-9a-fA-F]+) <(.+)>:\s*$")
OBJ_INSN = re.compile(r"^\s*[0-9a-fA-F]+:\s*(.*)$")
BLOCK_COMMENT = re.compile(r"/\*.*?\*/")
RAW_BYTES = re.compile(r"^(?:[0-9a-fA-F]{2}\s|[0-9a-fA-F]{8}\s)+$")
LINE_COMMENT = [re.compile(r"\s+#\s.*$"), re.compile(r"\s*//.*$"), re.compile(r"\s*;.*$")]
ADDR_SYM = re.compile(r"\b(?:0x)?[0-9a-fA-F]+(?=\s*<)")
RIP = re.compile(r"-?0x[0-9a-fA-F]+(?=\(%rip\))")
NAME_RULES = [
    (re.compile(r"\d*_INTERNAL_[0-9A-Fa-f]{8,}_\d+_[A-Za-z0-9_]+?_[0-9A-Fa-f]{8,}"), "_INTERNAL_"),
    (re.compile(r"\d*__nv_static_\d+__[0-9A-Fa-f]{8,}_\d+_[A-Za-z0-9_]+?_[0-9A-Fa-f]{8,}_*"), "__nv_static__"),
    (re.compile(r"_GLOBAL__N__\d+_[A-Za-z0-9_]+?_[0-9A-Fa-f]{8,}"), "_GLOBAL__N_"),
    (re.compile(r"(?<=_ii_)[0-9A-Fa-f]{8,}"), "H"),
]
FMA = re.compile(r"\b(?:FFMA\w*|DFMA\w*|HFMA2?\w*|v_fma\w*|v_fmac\w*|v_mad\w*|vfn?m(?:add|sub)\w*|"
                 r"fn?m(?:add|sub)|fml[as])\b")
RES_HEAD = re.compile(r"^\s*Function\s+(\S+?):\s*$")
RES_PAIR = re.compile(r"\b(REG|STACK|SHARED|LOCAL):(\d+)")
RES_KEYS = ("REG", "STACK", "SHARED", "LOCAL")


class ToolError(Exception):
    pass


def normalize_name(text):
    for rx, rep in NAME_RULES:
        text = rx.sub(rep, text)
    return text


def squeeze(text):
    return " ".join(text.split())


def normalize_sass(line):
    text = BLOCK_COMMENT.sub(" ", line).strip()
    return squeeze(normalize_name(text.rstrip(";").rstrip()))


def normalize_obj(body):
    parts = body.split("\t")
    if len(parts) > 1 and RAW_BYTES.match(parts[0].strip() + " "):
        body = "\t".join(parts[1:])
    for rx in LINE_COMMENT:
        body = rx.sub("", body)
    body = RIP.sub("ADDR", ADDR_SYM.sub("ADDR", body))
    return squeeze(normalize_name(body))


def add(funcs, name, lines):
    key, n = name, 2
    while key in funcs:
        key = f"{name}#{n}"
        n += 1
    funcs[key] = lines


def parse_sass(text):
    funcs, arch, name, lines = {}, "", None, []
    for line in text.splitlines():
        m = SASS_HEAD.match(line)
        if m:
            if name is not None:
                add(funcs, name, lines)
            name, lines = f"{arch}:{normalize_name(m.group(1))}" if arch else normalize_name(m.group(1)), []
            continue
        m = SASS_ARCH.match(line)
        if m:
            if name is not None:
                add(funcs, name, lines)
                name = None
            arch = m.group(1)
            continue
        if name is None:
            continue
        m = SASS_LABEL.match(line)
        if m:
            lines.append(m.group(1))
        elif SASS_INSN.match(line):
            insn = normalize_sass(line)
            if insn:
                lines.append(insn)
    if name is not None:
        add(funcs, name, lines)
    return funcs


def parse_objdump(text):
    funcs, name, lines = {}, None, []
    for line in text.splitlines():
        m = OBJ_HEAD.match(line)
        if m:
            if name is not None:
                add(funcs, name, lines)
            name, lines = normalize_name(m.group(2)), []
            continue
        if name is None:
            continue
        if not line.strip():
            add(funcs, name, lines)
            name = None
            continue
        m = OBJ_INSN.match(line)
        if m:
            insn = normalize_obj(m.group(1))
            if insn:
                lines.append(insn)
    if name is not None:
        add(funcs, name, lines)
    return funcs


def parse(text):
    if any(SASS_HEAD.match(line) for line in text.splitlines()):
        return parse_sass(text)
    return parse_objdump(text)


def fingerprint(lines):
    return {"sha": hashlib.sha256("\n".join(lines).encode()).hexdigest(), "insns": len(lines),
            "fma": sum(1 for l in lines if FMA.search(l))}


def parse_res_usage(text):
    out, arch, name = {}, "", None
    for line in text.splitlines():
        m = SASS_ARCH.match(line)
        if m:
            arch = m.group(1)
            continue
        m = RES_HEAD.match(line)
        if m:
            name = f"{arch}:{normalize_name(m.group(1))}" if arch else normalize_name(m.group(1))
            continue
        pairs = RES_PAIR.findall(line)
        if name is not None and pairs:
            key, n = name, 2
            while key in out:
                key = f"{name}#{n}"
                n += 1
            out[key] = {k: int(v) for k, v in pairs if k in RES_KEYS}
            name = None
    return out


def run(cmd):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    except OSError as e:
        raise ToolError(f"cannot run {cmd[0]}: {e}")
    if p.returncode != 0:
        raise ToolError(f"{' '.join(cmd)} exited {p.returncode}: {p.stderr.strip()[:300]}")
    return p.stdout


def template_cmd(template, path):
    args = shlex.split(template)
    if not any("{file}" in a for a in args):
        return args + [path]
    return [a.replace("{file}", path) for a in args]


def objdump_tool():
    for name in ("llvm-objdump", "objdump"):
        if shutil.which(name):
            return name
    raise ToolError("neither llvm-objdump nor objdump found; use --cmd")


def disassemble(path, tool, template=None):
    if template:
        return "cmd", run(template_cmd(template, path))
    if tool in ("auto", "cuobjdump") and shutil.which("cuobjdump"):
        try:
            text = run(["cuobjdump", "-sass", path])
        except ToolError:
            if tool == "cuobjdump":
                raise
            text = ""
        if any(SASS_HEAD.match(l) for l in text.splitlines()):
            return "cuobjdump", text
        if tool == "cuobjdump":
            raise ToolError(f"cuobjdump found no SASS functions in {path}")
    elif tool == "cuobjdump":
        raise ToolError("cuobjdump not found")
    name = objdump_tool() if tool == "auto" else tool
    return name, run([name, "-d", "--no-show-raw-insn", path])


def functions(path, tool, template):
    used, text = disassemble(path, tool, template)
    funcs = {k: fingerprint(v) for k, v in parse(text).items()}
    if not funcs:
        raise ToolError(f"no functions parsed from {path} ({used})")
    res = parse_res_usage(run(["cuobjdump", "-res-usage", path])) if used == "cuobjdump" else None
    return used, funcs, res


def compare(old, new, res_old=None, res_new=None):
    out = {"identical": [], "differ": [], "new": sorted(k for k in new if k not in old),
           "removed": sorted(k for k in old if k not in new), "res_differ": {}}
    for k in sorted(old):
        if k in new:
            out["identical" if old[k]["sha"] == new[k]["sha"] else "differ"].append(k)
    if res_old is not None and res_new is not None:
        for k in sorted(res_old):
            if k in res_new and res_old[k] != res_new[k]:
                out["res_differ"][k] = (res_old[k], res_new[k])
    return out


def res_text(a, b):
    return " ".join(f"{k} {a.get(k)}->{b.get(k)}" for k in RES_KEYS if a.get(k) != b.get(k))


def report(c, old, new, res_available):
    changed = sorted(set(c["differ"]) | set(c["res_differ"]))
    ok = not changed and not c["removed"]
    word = "PASS" if ok else "FAIL"
    detail = "no existing function differs" if ok else f"{len(changed)} differ, {len(c['removed'])} removed"
    print(f"{word} isa_diff: {detail}")
    print(f"identical {len(c['identical'])}  differ {len(c['differ'])}  new {len(c['new'])}  "
          f"removed {len(c['removed'])}  resource-diff {len(c['res_differ']) if res_available else 'n/a'}")
    for k in changed:
        line = f"DIFFER {k}"
        if k in c["differ"]:
            line += f"  insns {old[k]['insns']}->{new[k]['insns']}  fma {old[k]['fma']}->{new[k]['fma']}"
        if k in c["res_differ"]:
            line += "  " + res_text(*c["res_differ"][k])
        print(line)
    for k in c["removed"]:
        print(f"REMOVED {k}")
    for k in c["new"][:50]:
        print(f"NEW {k}")
    if len(c["new"]) > 50:
        print(f"NEW ... {len(c['new']) - 50} more")
    return 0 if ok else 1


def parse_args(argv):
    pos, tool, template, i = [], "auto", None, 0
    while i < len(argv):
        a = argv[i]
        if a in ("--tool", "--cmd"):
            if i + 1 >= len(argv):
                raise ValueError(f"{a} needs a value")
            if a == "--tool":
                tool = argv[i + 1]
            else:
                template = argv[i + 1]
            i += 2
        elif a.startswith("--"):
            raise ValueError(f"unknown flag {a}")
        else:
            pos.append(a)
            i += 1
    if len(pos) != 2:
        raise ValueError("need OLD and NEW")
    if tool not in ("auto", "cuobjdump", "llvm-objdump"):
        raise ValueError(f"--tool {tool}: use auto, cuobjdump or llvm-objdump")
    return pos[0], pos[1], tool, template


def main(argv):
    if any(a in ("-h", "--help") for a in argv):
        print(USAGE)
        return 0
    try:
        old_path, new_path, tool, template = parse_args(argv)
    except ValueError as e:
        print(f"{USAGE}\n\nerror: {e}", file=sys.stderr)
        return 2
    try:
        used, old, res_old = functions(old_path, tool, template)
        _, new, res_new = functions(new_path, used if used != "cmd" else tool, template)
    except ToolError as e:
        print(f"tool error: {e}", file=sys.stderr)
        return 2
    c = compare(old, new, res_old, res_new)
    return report(c, old, new, res_old is not None and res_new is not None)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
