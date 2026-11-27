#!/usr/bin/env python3
import bisect, csv, json, re, sqlite3, sys
from collections import defaultdict

USAGE = """Time budget from a GPU trace: attributed exposed time per kernel family, per device and phase.

  python3 scripts/budget.py summary TRACE [--phases phases.json] [--floors floors.json] [--out BUDGET.md]
  python3 scripts/budget.py diff TRACE_A TRACE_B [--phases phases.json]
  options for both: [--family-regex NAME=REGEX ...] [--steps N] [--top 25]

TRACE is one of:
  - an nsys SQLite export (nsys export --type sqlite -o trace.sqlite report.nsys-rep). Tables used:
    CUPTI_ACTIVITY_KIND_KERNEL, CUPTI_ACTIVITY_KIND_MEMCPY, CUPTI_ACTIVITY_KIND_MEMSET, StringIds, NVTX_EVENTS.
    A missing table is reported as "not available" and skipped.
  - a generic CSV with the header start_ns,end_ns,device,stream,name,kind for other vendors (map rocprof or other
    tools to it yourself). kind: kernel | memcpy | memset; rows with kind nvtx are ranges used for phases.

Family: the kernel name with template arguments, parameter list and return type removed
("void foo::gemm<128, 64>(Params)" -> "foo::gemm"), or the NAME of the first --family-regex that matches the full
name (repeatable, checked in order). Copies are "memcpy HtoD|DtoH|DtoD|PtoP", sets are "memset".

Per device and phase:
  window     total time of the phase windows (the same for every device, so an idle card shows as idle)
  busy       union of all kernels and copies on the device; idle = window - busy
  copy-only  busy time with only copies or sets running and no kernel (copy-only time is not idle time)
  attributed time per family: every slice of time is shared 1/k among the k operations running at once on that
             device, so overlap is not counted twice; families plus (idle) add up to the window.
  per step   time / steps of the phase. Use per-step numbers to compare traces of different length.

phases.json (optional; without it there is one phase "all" over the whole trace with --steps steps, default 1):
  {"nvtx": {"decode": "^decode_step", "prefill": "prefill"},
   "windows": [{"phase": "verify", "start_ns": 1000, "end_ns": 9000, "steps": 4}]}
  Each NVTX range whose text matches the regex is one window and one step of that phase; nested matching ranges
  count twice, so write regexes that match one level. "windows" adds explicit time windows (steps default 1).

floors.json (optional): {"family": floor_us_per_step, "(idle)": 0}. gap = attributed us/step - floor, ranked over all
devices and phases; families without a floor are listed separately (gap unknown, not zero).

diff: both traces with the same phases; per device, phase and family the us/step of A and B and B - A, ranked by
the absolute change, plus busy, idle and copy-only per step. Devices are matched by id.

Output is markdown on stdout (and in --out for summary). Confirm a gap that only shows under the profiler with an
in-engine timer: tracing adds overhead per launch."""

COPY_KIND = {1: "memcpy HtoD", 2: "memcpy DtoH", 8: "memcpy DtoD", 10: "memcpy PtoP"}
OPTS = {"phases", "floors", "out", "family_regex", "steps", "top"}


def parse(argv):
    if not argv or argv[0] not in ("summary", "diff"):
        sys.exit(USAGE)
    sub, pos, o, i = argv[0], [], {"family_regex": []}, 1
    while i < len(argv):
        a = argv[i]
        if a.startswith("--"):
            k = a[2:].replace("-", "_")
            if k not in OPTS or i + 1 >= len(argv):
                sys.exit(USAGE)
            if k == "family_regex":
                o[k].append(argv[i + 1])
            else:
                o[k] = argv[i + 1]
            i += 2
        else:
            pos.append(a)
            i += 1
    if len(pos) != (1 if sub == "summary" else 2) or (sub == "diff" and ("floors" in o or "out" in o)):
        sys.exit(USAGE)
    return sub, pos, o


def normalize(name):
    s = name.replace("(anonymous namespace)", "anon")
    out, depth = [], 0
    for ch in s:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(ch)
    s = "".join(out).split("(", 1)[0].split()
    return s[-1] if s else name


class Families:
    def __init__(self, specs):
        self.rx = []
        for spec in specs:
            if "=" not in spec:
                sys.exit(f"--family-regex needs NAME=REGEX, got {spec!r}")
            n, r = spec.split("=", 1)
            self.rx.append((n, re.compile(r)))
        self.cache = {}

    def __call__(self, name):
        f = self.cache.get(name)
        if f is None:
            f = next((n for n, r in self.rx if r.search(name)), None) or normalize(name)
            self.cache[name] = f
        return f


def load_sqlite(path, fam):
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        tables = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    except sqlite3.Error:
        con = sqlite3.connect(path)
        tables = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    cols = lambda t: {r[1] for r in con.execute(f"pragma table_info({t})")}
    strings = dict(con.execute("select id, value from StringIds")) if "StringIds" in tables else {}
    text = lambda v: strings.get(v, str(v)) if isinstance(v, int) else str(v)
    evs, nvtx, na = [], [], []
    t = "CUPTI_ACTIVITY_KIND_KERNEL"
    if t in tables:
        c = cols(t)
        ncol = next((n for n in ("demangledName", "shortName", "mangledName") if n in c), None)
        dev = "deviceId" if "deviceId" in c else "0"
        for s, e, d, n in con.execute(f"select start, end, {dev}, {ncol or 'NULL'} from {t} where end > start"):
            evs.append((s, e, str(d), "kernel", fam(text(n))))
    else:
        na.append(t)
    t = "CUPTI_ACTIVITY_KIND_MEMCPY"
    if t in tables:
        c = cols(t)
        dev, kind = ("deviceId" if "deviceId" in c else "0"), ("copyKind" if "copyKind" in c else "NULL")
        for s, e, d, k in con.execute(f"select start, end, {dev}, {kind} from {t} where end > start"):
            evs.append((s, e, str(d), "memcpy", COPY_KIND.get(k, "memcpy")))
    else:
        na.append(t)
    t = "CUPTI_ACTIVITY_KIND_MEMSET"
    if t in tables:
        dev = "deviceId" if "deviceId" in cols(t) else "0"
        for s, e, d in con.execute(f"select start, end, {dev} from {t} where end > start"):
            evs.append((s, e, str(d), "memset", "memset"))
    else:
        na.append(t)
    t = "NVTX_EVENTS"
    if t in tables:
        c = cols(t)
        tc = "text" if "text" in c else "NULL"
        tid = "textId" if "textId" in c else "NULL"
        for s, e, tx, ti in con.execute(f"select start, end, {tc}, {tid} from {t} where end is not null and end > start"):
            label = tx if tx is not None else (strings.get(ti) if ti is not None else None)
            if label is not None:
                nvtx.append((s, e, label))
    else:
        na.append(t)
    con.close()
    return evs, nvtx, na


def ns(x):
    try:
        return int(x)
    except ValueError:
        return int(float(x))


def load_csv(path, fam):
    evs, nvtx = [], []
    with open(path, newline="") as f:
        rd = csv.DictReader(f)
        need = {"start_ns", "end_ns", "device", "stream", "name", "kind"}
        if not rd.fieldnames or need - set(rd.fieldnames):
            sys.exit(f"{path}: CSV header must contain {','.join(sorted(need))}")
        for r in rd:
            s, e, k = ns(r["start_ns"]), ns(r["end_ns"]), r["kind"].strip().lower()
            if e <= s:
                continue
            if k == "nvtx":
                nvtx.append((s, e, r["name"]))
            elif k == "kernel":
                evs.append((s, e, r["device"].strip(), "kernel", fam(r["name"])))
            elif k in ("memcpy", "memset"):
                evs.append((s, e, r["device"].strip(), k, r["name"].strip() or k))
    return evs, nvtx, []


def load(path, fam):
    with open(path, "rb") as f:
        head = f.read(16)
    evs, nvtx, na = load_sqlite(path, fam) if head.startswith(b"SQLite format 3") else load_csv(path, fam)
    if not evs:
        sys.exit(f"{path}: no kernels or copies found")
    return evs, nvtx, na


def merge(wins):
    out = []
    for s, e in sorted(wins):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out


def phases(spec, nvtx, steps, t0, t1):
    if not spec:
        return {"all": ([[t0, t1]], steps)}
    raw = defaultdict(lambda: [[], 0])
    for name, rx in (spec.get("nvtx") or {}).items():
        r = re.compile(rx)
        for s, e, label in nvtx:
            if r.search(label):
                raw[name][0].append((s, e))
                raw[name][1] += 1
        if not raw[name][1]:
            print(f"warning: no NVTX range matches phase {name!r} ({rx})", file=sys.stderr)
            del raw[name]
    for w in spec.get("windows") or []:
        raw[w["phase"]][0].append((w["start_ns"], w["end_ns"]))
        raw[w["phase"]][1] += w.get("steps", 1)
    if not raw:
        sys.exit("no phase has any window")
    return {name: (merge(w), n) for name, (w, n) in raw.items()}


def segments(evs):
    pts = []
    for i, e in enumerate(evs):
        pts.append((e[0], 1, i))
        pts.append((e[1], 0, i))
    pts.sort()
    active, prev, segs = {}, None, []
    for t, typ, i in pts:
        if active and t > prev:
            segs.append((prev, t, tuple(active.values())))
        prev = t
        if typ:
            active[i] = evs[i]
        else:
            active.pop(i, None)
    return segs


def attribute(segs, evs, wins):
    fam, launches = defaultdict(float), defaultdict(int)
    busy = copy_only = 0.0
    j = 0
    for t0, t1, act in segs:
        while j < len(wins) and wins[j][1] <= t0:
            j += 1
        ov, k = 0, j
        while k < len(wins) and wins[k][0] < t1:
            ov += min(t1, wins[k][1]) - max(t0, wins[k][0])
            k += 1
        if ov <= 0:
            continue
        busy += ov
        if all(e[3] != "kernel" for e in act):
            copy_only += ov
        share = ov / len(act)
        for e in act:
            fam[e[4]] += share
    starts = [w[0] for w in wins]
    for e in evs:
        i = bisect.bisect_right(starts, e[0]) - 1
        if i >= 0 and e[0] < wins[i][1]:
            launches[e[4]] += 1
    return {"busy": busy, "copy_only": copy_only, "fam": fam, "launches": launches}


def budget(path, o):
    fam = Families(o["family_regex"])
    evs, nvtx, na = load(path, fam)
    spec = json.load(open(o["phases"])) if o.get("phases") else None
    t0, t1 = min(e[0] for e in evs), max(e[1] for e in evs)
    ph = phases(spec, nvtx, int(o.get("steps", 1)), t0, t1)
    by_dev = defaultdict(list)
    for e in evs:
        by_dev[e[2]].append(e)
    res = {}
    for dev in sorted(by_dev, key=lambda d: (len(d), d)):
        segs = segments(by_dev[dev])
        for name, (wins, steps) in ph.items():
            a = attribute(segs, by_dev[dev], wins)
            a["window"] = float(sum(e - s for s, e in wins))
            a["steps"] = max(steps, 1)
            a["fam"]["(idle)"] = a["window"] - a["busy"]
            res[(name, dev)] = a
    return res, na, len(evs)


def ms(ns):
    return f"{ns / 1e6:.3f}"


def us_step(ns, steps):
    return ns / 1e3 / steps


def summary(path, o):
    res, na, n_ev = budget(path, o)
    top = int(o.get("top", 25))
    floors = json.load(open(o["floors"])) if o.get("floors") else None
    lines = [f"# Budget: {path}", "", f"{n_ev} operations; per-step = time / steps of the phase."]
    if na:
        lines.append(f"Not available in this trace: {', '.join(na)}.")
    lines += ["", "| phase | device | steps | window ms | busy % | idle ms | copy-only ms | busy us/step |",
              "|---|---|---|---|---|---|---|---|"]
    for (ph, dev), a in res.items():
        w = a["window"] or 1
        lines.append(f"| {ph} | {dev} | {a['steps']} | {ms(a['window'])} | {100 * a['busy'] / w:.1f} | "
                     f"{ms(a['window'] - a['busy'])} | {ms(a['copy_only'])} | {us_step(a['busy'], a['steps']):.1f} |")
    for (ph, dev), a in res.items():
        w = a["window"] or 1
        lines += ["", f"## {ph}, device {dev}", "",
                  "| family | attributed ms | us/step | % of window | launches/step |", "|---|---|---|---|---|"]
        rows = sorted(a["fam"].items(), key=lambda kv: -kv[1])
        for f, t in rows[:top]:
            lines.append(f"| {f} | {ms(t)} | {us_step(t, a['steps']):.1f} | {100 * t / w:.1f} | "
                         f"{a['launches'].get(f, 0) / a['steps']:.1f} |")
        if len(rows) > top:
            rest = sum(t for _, t in rows[top:])
            lines.append(f"| ({len(rows) - top} more) | {ms(rest)} | {us_step(rest, a['steps']):.1f} | {100 * rest / w:.1f} | |")
    if floors is not None:
        gaps, nofloor = [], []
        for (ph, dev), a in res.items():
            for f, t in a["fam"].items():
                u = us_step(t, a["steps"])
                if f in floors:
                    gaps.append((u - floors[f], ph, dev, f, u, floors[f]))
                else:
                    nofloor.append((u, ph, dev, f))
        gaps.sort(reverse=True)
        lines += ["", "## Gap ranking (attributed us/step - floor)", "",
                  "| rank | phase | device | family | us/step | floor | gap us/step |", "|---|---|---|---|---|---|---|"]
        for i, (g, ph, dev, f, u, fl) in enumerate(gaps, 1):
            lines.append(f"| {i} | {ph} | {dev} | {f} | {u:.1f} | {fl} | {g:.1f} |")
        nofloor.sort(reverse=True)
        if nofloor:
            lines += ["", "No floor given (gap unknown, not zero):", ""]
            lines += [f"- {ph} / {dev} / {f}: {u:.1f} us/step" for u, ph, dev, f in nofloor[:top]]
    text = "\n".join(lines) + "\n"
    print(text, end="")
    if o.get("out"):
        with open(o["out"], "w") as f:
            f.write(text)
        print(f"\nwrote {o['out']}", file=sys.stderr)


def diff(pa, pb, o):
    ra, na_a, _ = budget(pa, o)
    rb, na_b, _ = budget(pb, o)
    top = int(o.get("top", 25))
    lines = [f"# Budget diff: A = {pa}, B = {pb}", ""]
    for p, na in ((pa, na_a), (pb, na_b)):
        if na:
            lines.append(f"Not available in {p}: {', '.join(na)}.")
    lines += ["| phase | device | metric | A us/step | B us/step | B - A |", "|---|---|---|---|---|---|"]
    keys = [k for k in ra if k in rb] + [k for k in rb if k not in ra]
    rows = []
    for k in keys:
        a, b = ra.get(k), rb.get(k)
        if not a or not b:
            lines.append(f"| {k[0]} | {k[1]} | (only in {'A' if a else 'B'}) | | | |")
            continue
        for m in ("busy", "copy_only"):
            x, y = us_step(a[m], a["steps"]), us_step(b[m], b["steps"])
            lines.append(f"| {k[0]} | {k[1]} | {m} | {x:.1f} | {y:.1f} | {y - x:+.1f} |")
        x, y = us_step(a["window"] - a["busy"], a["steps"]), us_step(b["window"] - b["busy"], b["steps"])
        lines.append(f"| {k[0]} | {k[1]} | idle | {x:.1f} | {y:.1f} | {y - x:+.1f} |")
        for f in set(a["fam"]) | set(b["fam"]):
            if f == "(idle)":
                continue
            x, y = us_step(a["fam"].get(f, 0), a["steps"]), us_step(b["fam"].get(f, 0), b["steps"])
            rows.append((abs(y - x), k[0], k[1], f, x, y))
    rows.sort(reverse=True)
    lines += ["", "## Families ranked by |B - A| (attributed us/step)", "",
              "| phase | device | family | A | B | B - A |", "|---|---|---|---|---|---|"]
    lines += [f"| {ph} | {dev} | {f} | {x:.1f} | {y:.1f} | {y - x:+.1f} |" for _, ph, dev, f, x, y in rows[:top]]
    print("\n".join(lines))


def main(argv):
    sub, pos, o = parse(argv)
    summary(pos[0], o) if sub == "summary" else diff(pos[0], pos[1], o)


if __name__ == "__main__":
    main(sys.argv[1:])
