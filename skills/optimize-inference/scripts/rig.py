#!/usr/bin/env python3
import copy, difflib, glob, json, math, os, re, shutil, statistics, subprocess, sys, threading, time
from datetime import datetime

USAGE = """Rig safety checks, machine state, run-time sampler and noise bars for the hill-climb harness. Standard library only.

  python3 scripts/rig.py detect [--out rig.json] [--force]
  python3 scripts/rig.py check  [--rig rig.json] [--cards 0,1] [--allow-pids PID,PID]
  python3 scripts/rig.py state  [--rig rig.json]
  python3 scripts/rig.py noise  [--ledger ledger.jsonl] [--rig rig.json] [--json]

detect  Probe the platform (GPU vendor and tool, RAM, CPUs, cgroup memory limit, I/O schedulers) and write rig.json
        with default checks, scopes and noise parameters. An existing file is never overwritten without --force;
        instead the diff of the detected "platform"/"collectors" against the stored ones is printed.
        GPU tools tried: nvidia-smi, amd-smi, rocm-smi, xpu-smi; macOS uses ioreg/sysctl/pmset/vm_stat.
        Host: /proc on Linux, sysctl/vm_stat on macOS. A missing tool gives collector "none", never an error.
        The build scope uses systemd-run --user --scope (MemoryHigh = RAM minus the floor, CPUWeight=10) when it
        works, then nice; ionice is added only with the bfq/cfq I/O scheduler (with "none" it has no effect).
        macOS: nice (taskpolicy -b is stronger: background QoS, much slower builds).
check   One line per check: `name status level detail`. status: pass | fail | na (not available: never blocks).
        level (rig.json "checks"): block | warn | off. Exit 1 if a check with level "block" failed, else 0.
          cards_idle      no other compute process on the cards (--cards limits it; --allow-pids ignores these PIDs
                          and their descendants, e.g. the server the harness left running)
          host_ram_floor  available host RAM >= floor_gib (null: max(6 GiB, 10% of RAM))
          no_build        no process whose exact name is in "names" (compilers, build tools)
          on_ac           on mains power (na on machines without power-supply information)
          host_busy       1-min load per CPU <= load_per_cpu
          hook:<name>     each rig.json "hooks" entry: cmd must exit 0 within timeout_s (default 30); a missing
                          command fails (the user asked for that daemon to stay alive)
state   JSON machine-state snapshot (clocks, power and limit, temperature, throttle reasons, utilisation, VRAM,
        persistence per GPU; host available RAM, swap, load; AC power). Fields a platform lacks are null.
noise   Pooled SD per config_hash x metric from ledger schema-2 rows with ok=true, over the last noise.window loads
        (rig.json, default 20) of each config: within-load SD pools the per-pass values (metrics_passes) of each
        load; between-load SD is the SD of the per-load means. Schema-1 rows are skipped and counted.

rig.json keys: schema, platform, collectors, checks, hooks [{"name", "cmd": [...], "level", "timeout_s"}],
scope {"build": [...], "load": [...]} (command prefixes), watchdog {"no_progress_s"}, cache_bypass, noise
{"k", "floor_pct", "window", "min_samples", "min_tokens", "min_loads", "min_df"}, settings {"protected", "accepted"},
microbench.
checks.host_busy also takes "disk_busy_pct" (default 50) for the sampler's disk flag.

Import API (bench.py imports this file from the same directory; nothing runs at import):
  load(path="rig.json") -> dict           missing file: detected defaults in memory, "_source": "detected"
  detect() -> dict                        detected rig dict; runs probes, writes nothing
  preflight(rig, cards=None, allow_pids=None) -> [{"check", "status", "level", "detail"}]
  blocking(results) -> list               failed checks whose level is "block"
  state(rig) -> dict                      {"gpus": [...], "host": {...}, "on_ac": bool|None, "time": iso}
  floor_gib(rig) -> float                 host-RAM floor in GiB
  scope_cmd(rig, kind) -> list            command prefix for "build" or "load" ([] when none)
  noise(ledger="ledger.jsonl", window=20) -> {"rows_used", "schema1_skipped", "configs": {hash: {"names", "loads",
      "metrics": {metric: {"mean", "sd_within", "df_within", "sd_between", "loads", "passes_mean",
      "sd_within_pct", "sd_between_pct"}}}}}
  s = Sampler(rig, out_path, interval_s=1.0, on_floor=None)
  s.start(); s.phase("c1"); ...; summary = s.stop()
      Writes one JSON line per sample to out_path: {"t": epoch_s, "phase", <host keys>, "on_ac",
      "gpu<i>_<field>", "swapin_mib_s", "disk_busy_pct"}. stop() returns {"phases": {name: {metric: median}},
      "host_ram_min_gib", "host_busy", "host_busy_detail"}. on_floor() is called once when available host RAM
      drops below the floor (the watchdog stops the run there). host_busy compares each phase's median load per
      CPU and disk busy % against the first sample (the idle baseline); phases named start, launch, load,
      startup, stop, drain or idle are not timed and are ignored. Engines that use CPU threads raise the load
      by design: raise load_per_cpu or set host_busy to "off" on such rigs."""

GIB = 2**30
DEFAULTS = {
    "schema": 1,
    "checks": {
        "cards_idle": {"level": "block"},
        "host_ram_floor": {"level": "block", "floor_gib": None},
        "no_build": {"level": "warn", "names": ["nvcc", "cicc", "ptxas", "ninja", "make", "cargo", "cc1plus"]},
        "on_ac": {"level": "block"},
        "host_busy": {"level": "warn", "load_per_cpu": 0.5, "disk_busy_pct": 50},
    },
    "hooks": [],
    "scope": {"build": [], "load": []},
    "watchdog": {"no_progress_s": 600},
    "cache_bypass": {"mode": "none", "request_field": None, "flush_cmd": None},
    "noise": {"k": 2.5, "floor_pct": 0.3, "window": 20, "min_samples": 6, "min_tokens": 64, "min_loads": 3,
              "min_df": 4},
    "settings": {"protected": [], "accepted": []},
    "microbench": {"bw_gbs_by_read_mib": {}, "chain_node_us": None, "link_gbs": None, "peak_tflops_at_cap": None},
}
GPU_FIELDS = ("clock_sm_mhz", "clock_mem_mhz", "power_w", "power_limit_w", "temp_c", "throttle", "util_pct",
              "mem_used_mib", "persistence")
UNTIMED_PHASES = {"start", "launch", "load", "startup", "stop", "drain", "idle"}
NV_REASONS = {0x1: "gpu_idle", 0x2: "app_clocks", 0x4: "sw_power_cap", 0x8: "hw_slowdown", 0x10: "sync_boost",
              0x20: "sw_thermal", 0x40: "hw_thermal", 0x80: "hw_power_brake", 0x100: "display_clocks"}
SKIP_DISKS = ("loop", "ram", "zram")


def _run(cmd, timeout=10):
    if not shutil.which(cmd[0]):
        return None
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    return p.stdout if p.returncode == 0 else None


def _num(v):
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    m = re.search(r"-?\d+(?:\.\d+)?", str(v))
    return float(m.group()) if m else None


def _json(out):
    try:
        return json.loads(out) if out else None
    except ValueError:
        return None


def _leaves(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _leaves(v, f"{path}.{k}".lower() if path else str(k).lower())
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _leaves(v, f"{path}.{i}")
    else:
        yield path, obj


def _pick(leaves, need, avoid=()):
    for p, v in leaves:
        if all(n in p for n in need) and not any(a in p for a in avoid) and _num(v) is not None:
            return _num(v)
    return None


def _items(data):
    if isinstance(data, dict):
        data = next((v for v in data.values() if isinstance(v, list)), [data])
    return [d for d in (data or []) if isinstance(d, dict)]


def _os():
    return "darwin" if sys.platform == "darwin" else "linux" if sys.platform.startswith("linux") else sys.platform


def _now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _merge(base, over):
    out = copy.deepcopy(base)
    for k, v in over.items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


def _gib(b):
    return None if b is None else round(b / GIB, 2)


def _finite(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _meminfo():
    try:
        with open("/proc/meminfo") as f:
            return {l.split(":")[0]: int(l.split()[1]) * 1024 for l in f if len(l.split()) >= 2}
    except (OSError, ValueError):
        return {}


def _ram_bytes():
    if _os() == "darwin":
        return _num(_run(["sysctl", "-n", "hw.memsize"]))
    return _meminfo().get("MemTotal")


def _cgroup_mem():
    try:
        with open("/proc/self/cgroup") as f:
            rel = next((l[3:].strip() for l in f if l.startswith("0::")), None)
    except OSError:
        return None
    if rel is None:
        return None
    d, best = os.path.normpath("/sys/fs/cgroup" + rel), None
    while d.startswith("/sys/fs/cgroup"):
        try:
            with open(os.path.join(d, "memory.max")) as f:
                lim = f.read().strip()
            if lim.isdigit():
                with open(os.path.join(d, "memory.current")) as f:
                    cur = int(f.read().strip())
                if best is None or int(lim) - cur < best[0] - best[1]:
                    best = (int(lim), cur)
        except (OSError, ValueError):
            pass
        if d == "/sys/fs/cgroup":
            break
        d = os.path.dirname(d)
    return best


def _io_schedulers():
    out = {}
    for p in glob.glob("/sys/block/*/queue/scheduler"):
        dev = p.split("/")[3]
        if dev.startswith(SKIP_DISKS):
            continue
        try:
            with open(p) as f:
                m = re.search(r"\[(\S+)\]", f.read())
            out[dev] = m.group(1) if m else "none"
        except OSError:
            pass
    return out


def _detect_gpu(osn):
    out = _run(["nvidia-smi", "--query-gpu=index,name,memory.total", "--format=csv,noheader,nounits"])
    if out:
        gpus = []
        for line in out.strip().splitlines():
            f = [x.strip() for x in line.split(",")]
            if len(f) >= 3 and f[0].isdigit():
                mib = _num(f[2])
                gpus.append({"index": int(f[0]), "name": f[1], "memory_gib": round(mib / 1024, 1) if mib else None})
        return "nvidia", "nvidia-smi", gpus
    if osn == "darwin":
        chip = (_run(["sysctl", "-n", "machdep.cpu.brand_string"]) or "").strip()
        if chip.startswith("Apple"):
            return "apple", "macos", [{"index": 0, "name": f"{chip} GPU", "memory_gib": _gib(_ram_bytes())}]
        disp = _json(_run(["system_profiler", "SPDisplaysDataType", "-json"], timeout=20)) or {}
        gpus, vendor = [], "none"
        for i, d in enumerate(disp.get("SPDisplaysDataType", [])):
            gpus.append({"index": i, "name": d.get("sppci_model"), "memory_gib": None})
            v = str(d.get("spdisplays_vendor", "")).lower()
            if "amd" in v or "ati" in v:
                vendor = "amd"
            elif "intel" in v and vendor == "none":
                vendor = "intel"
        return vendor, "macos", gpus
    data = _items(_json(_run(["amd-smi", "static", "--asic", "--vram", "--json"], timeout=20)))
    if data:
        gpus = []
        for i, d in enumerate(data):
            lv = list(_leaves(d))
            name = next((v for p, v in lv if "market_name" in p), None)
            mb = _pick(lv, ("vram", "size"), ("unit",))
            gpus.append({"index": int(d.get("gpu", i)), "name": name, "memory_gib": round(mb / 1024, 1) if mb else None})
        return "amd", "amd-smi", gpus
    data = _json(_run(["rocm-smi", "--showproductname", "--showmeminfo", "vram", "--json"], timeout=20))
    if isinstance(data, dict) and any(k.startswith("card") for k in data):
        gpus = []
        for card, d in sorted(data.items()):
            if not card.startswith("card") or _num(card) is None:
                continue
            lv = list(_leaves(d))
            name = next((v for p, v in lv if "card series" in p or "card model" in p), None)
            gpus.append({"index": int(_num(card)), "name": name, "memory_gib": _gib(_pick(lv, ("vram total memory",)))})
        return "amd", "rocm-smi", gpus
    data = _json(_run(["xpu-smi", "discovery", "-j"], timeout=20))
    if isinstance(data, dict) and data.get("device_list"):
        gpus = []
        for d in data["device_list"]:
            gpus.append({"index": int(d.get("device_id", len(gpus))), "name": d.get("device_name"),
                         "memory_gib": _gib(_num(d.get("memory_physical_size_byte")))})
        return "intel", "xpu-smi", gpus
    vendors = {"0x10de": "nvidia", "0x1002": "amd", "0x8086": "intel"}
    gpus, vendor = [], "none"
    for p in sorted(glob.glob("/sys/class/drm/card[0-9]*/device/vendor")):
        if "-" in p.split("/")[4]:
            continue
        try:
            with open(p) as f:
                v = vendors.get(f.read().strip())
        except OSError:
            continue
        if v:
            vendor = vendor if vendor != "none" else v
            gpus.append({"index": len(gpus), "name": f"{v} (no tool found)", "memory_gib": None})
    return vendor, "none", gpus


def floor_gib(rig):
    f = rig.get("checks", {}).get("host_ram_floor", {}).get("floor_gib")
    if f is not None:
        return float(f)
    return max(6.0, 0.1 * (rig.get("platform", {}).get("ram_gib") or 0))


def _default_scope(osn, ram_gib, cg_gib, scheds):
    if osn != "linux":
        return {"build": ["nice", "-n", "19"], "load": []}
    prefix = []
    if _run(["systemd-run", "--user", "--scope", "-q", "true"], timeout=15) is not None:
        sizes = [x for x in (ram_gib, cg_gib) if x]
        eff = min(sizes) if sizes else None
        high = max(1, int(eff - max(6.0, 0.1 * eff))) if eff else None
        prefix = ["systemd-run", "--user", "--scope", "-q"] + (["-p", f"MemoryHigh={high}G"] if high else []) \
            + ["-p", "CPUWeight=10"]
    prefix += ["nice", "-n", "19"]
    if shutil.which("ionice") and any(s in ("bfq", "cfq") for s in scheds.values()):
        prefix += ["ionice", "-c", "3"]
    return {"build": prefix, "load": []}


def detect():
    osn = _os()
    vendor, gcoll, gpus = _detect_gpu(osn)
    ram = _gib(_ram_bytes())
    plat = {"os": osn, "gpu_vendor": vendor, "gpus": gpus, "ram_gib": ram, "cpus": os.cpu_count()}
    cg = _cgroup_mem() if osn == "linux" else None
    if cg and (ram is None or cg[0] / GIB < ram):
        plat["cgroup_mem_gib"] = _gib(cg[0])
    scheds = _io_schedulers() if osn == "linux" else {}
    if scheds:
        plat["io_schedulers"] = scheds
    hcoll = "linux-proc" if os.path.exists("/proc/meminfo") else "macos" if osn == "darwin" else "none"
    rig = copy.deepcopy(DEFAULTS)
    rig["platform"], rig["collectors"] = plat, {"gpu": gcoll, "host": hcoll}
    rig["scope"] = _default_scope(osn, ram, plat.get("cgroup_mem_gib"), scheds)
    return rig


def load(path="rig.json"):
    if not os.path.exists(path):
        rig = detect()
        rig["_source"] = "detected"
        return rig
    with open(path) as f:
        stored = json.load(f)
    rig = _merge(DEFAULTS, stored)
    if "platform" not in stored or "collectors" not in stored:
        d = detect()
        rig.setdefault("platform", d["platform"])
        rig.setdefault("collectors", d["collectors"])
    rig["_source"] = path
    return rig


def scope_cmd(rig, kind):
    return list((rig.get("scope") or {}).get(kind) or [])


def _null_gpus(rig, idx=None):
    if idx is None:
        idx = [g.get("index", i) for i, g in enumerate(rig.get("platform", {}).get("gpus", []))]
    return [dict({"index": i}, **{k: None for k in GPU_FIELDS}) for i in idx]


_NV_QUERY = []


def _nvidia_state(rig):
    base = "index,clocks.sm,clocks.mem,power.draw,power.limit,temperature.gpu,utilization.gpu,memory.used,persistence_mode"
    out = None
    for extra in (_NV_QUERY or [",clocks_event_reasons.active", ",clocks_throttle_reasons.active", ""]):
        out = _run(["nvidia-smi", f"--query-gpu={base}{extra}", "--format=csv,noheader,nounits"])
        if out:
            _NV_QUERY[:] = [extra]
            break
    if not out:
        return _null_gpus(rig)
    rows = []
    for line in out.strip().splitlines():
        f = [x.strip() for x in line.split(",")]
        if len(f) < 9 or not f[0].isdigit():
            continue
        thr = None
        if len(f) > 9:
            try:
                mask = int(f[9], 16)
                thr = [n for b, n in NV_REASONS.items() if mask & b]
            except ValueError:
                pass
        rows.append({"index": int(f[0]), "clock_sm_mhz": _num(f[1]), "clock_mem_mhz": _num(f[2]), "power_w": _num(f[3]),
                     "power_limit_w": _num(f[4]), "temp_c": _num(f[5]), "throttle": thr, "util_pct": _num(f[6]),
                     "mem_used_mib": _num(f[7]), "persistence": None if "N/A" in f[8] else f[8]})
    return rows


def _first(*vals):
    return next((v for v in vals if v is not None), None)


def _amd_fields(lv, mem_scale):
    used = _first(_pick(lv, ("used_vram",)), _pick(lv, ("vram total used memory",)))
    clk_avoid = ("min", "max", "lock", "sleep")
    return {"clock_sm_mhz": _first(_pick(lv, ("clock", "gfx", "clk"), clk_avoid), _pick(lv, ("sclk",))),
            "clock_mem_mhz": _first(_pick(lv, ("clock", "mem", "clk"), clk_avoid), _pick(lv, ("mclk",))),
            "power_w": _first(_pick(lv, ("socket_power",)), _pick(lv, ("package power",), ("max",))),
            "power_limit_w": _first(_pick(lv, ("power_limit",)), _pick(lv, ("max graphics package power",))),
            "temp_c": _first(_pick(lv, ("temperature", "edge")), _pick(lv, ("temperature", "hotspot")),
                             _pick(lv, ("temperature",))),
            "throttle": None,
            "util_pct": _first(_pick(lv, ("gfx_activity",)), _pick(lv, ("gpu use",))),
            "mem_used_mib": None if used is None else round(used * mem_scale, 1), "persistence": None}


def _amd_smi_state(rig):
    data = _items(_json(_run(["amd-smi", "metric", "--json"], timeout=20)))
    if not data:
        return _null_gpus(rig)
    return [dict({"index": int(d.get("gpu", i))}, **_amd_fields(list(_leaves(d)), 1.0)) for i, d in enumerate(data)]


def _rocm_smi_state(rig):
    data = _json(_run(["rocm-smi", "--showuse", "--showtemp", "--showpower", "--showmaxpower", "--showclocks",
                       "--showmeminfo", "vram", "--json"], timeout=20))
    if not isinstance(data, dict):
        return _null_gpus(rig)
    return [dict({"index": int(_num(c))}, **_amd_fields(list(_leaves(d)), 1 / 2**20))
            for c, d in sorted(data.items()) if c.startswith("card") and _num(c) is not None]


def _xpu_state(rig):
    rows = []
    for g in _null_gpus(rig) or _null_gpus(rig, [0]):
        out = _run(["xpu-smi", "dump", "-d", str(g["index"]), "-m", "0,1,2,3,18", "-n", "1"], timeout=8)
        lines = [l for l in (out or "").splitlines() if "," in l]
        if len(lines) >= 2:
            row = dict(zip([h.strip().lower() for h in lines[0].split(",")], lines[-1].split(",")))
            for h, v in row.items():
                key = ("util_pct" if "utilization" in h and "memory" not in h else "power_w" if "power" in h
                       else "clock_sm_mhz" if "frequency" in h else "temp_c" if "core temperature" in h
                       else "mem_used_mib" if "memory used" in h else None)
                if key:
                    g[key] = _num(v)
        rows.append(g)
    return rows


def _macos_gpu_state(rig):
    g = (_null_gpus(rig) or _null_gpus(rig, [0]))[0]
    out = _run(["ioreg", "-r", "-d", "1", "-c", "IOAccelerator"]) or ""
    m = re.search(r'"Device Utilization %"=(\d+)', out)
    g["util_pct"] = float(m.group(1)) if m else None
    m = re.search(r'"In use system memory"=(\d+)', out)
    g["mem_used_mib"] = round(int(m.group(1)) / 2**20, 1) if m else None
    return [g]


GPU_STATE = {"nvidia-smi": _nvidia_state, "amd-smi": _amd_smi_state, "rocm-smi": _rocm_smi_state,
             "xpu-smi": _xpu_state, "macos": _macos_gpu_state}


def _host_state():
    h = {"mem_avail_gib": None, "swap_used_gib": None, "load1": None, "cpus": os.cpu_count()}
    try:
        h["load1"] = round(os.getloadavg()[0], 2)
    except OSError:
        pass
    if _os() == "darwin":
        out = _run(["vm_stat"]) or ""
        m = re.search(r"page size of (\d+)", out)
        pages = {k.strip(): _num(v) for k, v in (l.split(":", 1) for l in out.splitlines()[1:] if ":" in l)}
        free = [pages.get(k) for k in ("Pages free", "Pages inactive", "Pages speculative")]
        if m and all(x is not None for x in free):
            h["mem_avail_gib"] = _gib(sum(free) * int(m.group(1)))
        m = re.search(r"used = ([\d.]+)M", _run(["sysctl", "-n", "vm.swapusage"]) or "")
        h["swap_used_gib"] = round(float(m.group(1)) / 1024, 2) if m else None
        return h
    mi = _meminfo()
    h["mem_avail_gib"] = _gib(mi.get("MemAvailable"))
    if "SwapTotal" in mi and "SwapFree" in mi:
        h["swap_used_gib"] = _gib(mi["SwapTotal"] - mi["SwapFree"])
    cg = _cgroup_mem()
    if cg:
        h["cgroup_avail_gib"] = _gib(cg[0] - cg[1])
    return h


def _read(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None


def _on_ac():
    if _os() == "darwin":
        out = _run(["pmset", "-g", "batt"])
        return None if out is None else "AC Power" in out
    mains = battery = False
    for d in glob.glob("/sys/class/power_supply/*"):
        kind = _read(os.path.join(d, "type")) or ""
        if kind == "Battery":
            st = _read(os.path.join(d, "status"))
            if st == "Discharging":
                return False
            battery = battery or st is not None
        elif (kind == "Mains" or kind.startswith("USB")) and _read(os.path.join(d, "online")) == "1":
            mains = True
    return True if mains or battery else None


def state(rig):
    fn = GPU_STATE.get(rig.get("collectors", {}).get("gpu"))
    return {"gpus": fn(rig) if fn else _null_gpus(rig), "host": _host_state(), "on_ac": _on_ac(), "time": _now()}


def _ppids():
    m = {}
    if os.path.isdir("/proc/self"):
        for d in os.listdir("/proc"):
            if d.isdigit():
                s = _read(f"/proc/{d}/stat")
                try:
                    m[int(d)] = int(s.rsplit(")", 1)[1].split()[1])
                except (AttributeError, ValueError, IndexError):
                    pass
        return m
    for line in (_run(["ps", "-axo", "pid=,ppid="]) or "").splitlines():
        f = line.split()
        if len(f) == 2 and f[0].isdigit() and f[1].isdigit():
            m[int(f[0])] = int(f[1])
    return m


def _descendants(roots):
    kids = {}
    for p, pp in _ppids().items():
        kids.setdefault(pp, []).append(p)
    seen, stack = set(), list(roots)
    while stack:
        p = stack.pop()
        if p not in seen:
            seen.add(p)
            stack += kids.get(p, [])
    return seen


def _proc_names():
    if os.path.isdir("/proc/self"):
        out = []
        for d in os.listdir("/proc"):
            if d.isdigit():
                n = _read(f"/proc/{d}/comm")
                if n is not None:
                    out.append((int(d), n))
        return out
    ps = _run(["ps", "-axo", "pid=,comm="])
    if ps is None:
        return None
    out = []
    for line in ps.splitlines():
        f = line.strip().split(None, 1)
        if len(f) == 2 and f[0].isdigit():
            out.append((int(f[0]), os.path.basename(f[1])))
    return out


def _gpu_procs(rig):
    coll = rig.get("collectors", {}).get("gpu")
    if coll == "nvidia-smi":
        uu = _run(["nvidia-smi", "--query-gpu=index,uuid", "--format=csv,noheader"])
        apps = _run(["nvidia-smi", "--query-compute-apps=pid,gpu_uuid,used_memory,process_name",
                     "--format=csv,noheader,nounits"])
        if uu is None or apps is None:
            return None, "nvidia-smi not found or failed"
        idx = {u.strip(): int(i) for i, u in (l.split(",", 1) for l in uu.strip().splitlines() if "," in l)}
        procs = []
        for line in apps.strip().splitlines():
            f = [x.strip() for x in line.split(",", 3)]
            if len(f) == 4 and f[0].isdigit():
                procs.append((int(f[0]), idx.get(f[1]), f"{os.path.basename(f[3])} {f[2]} MiB"))
        return procs, None
    if coll == "amd-smi":
        data = _json(_run(["amd-smi", "process", "--json"], timeout=20))
        if data is None:
            return None, "amd-smi not found or failed"
        procs = []
        for i, d in enumerate(_items(data)):
            for p, v in _leaves(d):
                if p.endswith(".pid") and _num(v):
                    procs.append((int(_num(v)), int(d.get("gpu", i)), ""))
        return procs, None
    if coll == "rocm-smi":
        data = _json(_run(["rocm-smi", "--showpids", "--json"], timeout=20))
        if not isinstance(data, dict):
            return None, "rocm-smi not found or failed"
        procs = [(int(k[3:]), None, str(v).split(",")[0]) for k, v in (data.get("system") or {}).items()
                 if k.startswith("PID") and k[3:].isdigit()]
        return procs, None
    if coll == "xpu-smi":
        out = _run(["xpu-smi", "ps"], timeout=20)
        if out is None:
            return None, "xpu-smi not found or failed"
        procs = []
        for line in out.splitlines():
            m = re.match(r"\s*(\d+)\s+(.*?)\s+(\d+)\s+\S+\s+\S+\s*$", line)
            if m:
                procs.append((int(m.group(1)), int(m.group(3)), m.group(2)))
            elif re.match(r"\s*\d+\s", line):
                procs.append((int(line.split()[0]), None, line.strip()[:60]))
        return procs, None
    return None, f"no per-process GPU accounting with collector {coll or 'none'}"


def _check_cards(rig, cards, allow_pids):
    procs, why = _gpu_procs(rig)
    if procs is None:
        return "na", why
    allowed = _descendants(allow_pids or []) | {os.getpid()}
    busy = [f"pid {p} gpu {'?' if g is None else g} {d}".strip() for p, g, d in procs
            if p not in allowed and (cards is None or g is None or g in cards)]
    return ("fail", "; ".join(busy)) if busy else ("pass", "no other compute process")


def _check_floor(rig):
    avail, floor = _host_state()["mem_avail_gib"], floor_gib(rig)
    if avail is None:
        return "na", "available host RAM not readable"
    return ("pass" if avail >= floor else "fail"), f"available {avail} GiB, floor {floor:g} GiB"


def _check_build(names):
    procs = _proc_names()
    if procs is None:
        return "na", "process list not readable"
    want = set(names) | {n[:15] for n in names}
    hits = [f"{n}({p})" for p, n in procs if n in want and p != os.getpid()]
    return ("fail", " ".join(hits[:10])) if hits else ("pass", "none running")


def _check_ac():
    v = _on_ac()
    if v is None:
        return "na", "no power-supply information"
    return ("pass", "on AC") if v else ("fail", "on battery")


def _check_busy(c):
    h = _host_state()
    if h["load1"] is None or not h["cpus"]:
        return "na", "load average not readable"
    per, lim = h["load1"] / h["cpus"], c.get("load_per_cpu", 0.5)
    return ("pass" if per <= lim else "fail"), f"load1 {h['load1']} on {h['cpus']} CPUs ({per:.2f}/CPU, limit {lim})"


def _check_hook(h):
    t = h.get("timeout_s", 30)
    try:
        p = subprocess.run(h["cmd"], capture_output=True, text=True, timeout=t)
    except FileNotFoundError:
        return "fail", f"command not found: {h['cmd'][0]}"
    except subprocess.TimeoutExpired:
        return "fail", f"timed out after {t} s"
    tail = (p.stdout + p.stderr).strip().replace("\n", " ")[-120:]
    return ("pass" if p.returncode == 0 else "fail"), f"rc {p.returncode} {tail}".strip()


def preflight(rig, cards=None, allow_pids=None):
    checks = _merge(DEFAULTS["checks"], rig.get("checks") or {})
    probes = [("cards_idle", checks["cards_idle"], lambda: _check_cards(rig, cards, allow_pids)),
              ("host_ram_floor", checks["host_ram_floor"], lambda: _check_floor(rig)),
              ("no_build", checks["no_build"], lambda: _check_build(checks["no_build"].get("names") or [])),
              ("on_ac", checks["on_ac"], _check_ac),
              ("host_busy", checks["host_busy"], lambda: _check_busy(checks["host_busy"]))]
    for i, h in enumerate(rig.get("hooks") or []):
        probes.append((f"hook:{h.get('name', i)}", h, (lambda h: lambda: _check_hook(h))(h)))
    out = []
    for name, c, fn in probes:
        level = c.get("level", "block")
        if level == "off":
            out.append({"check": name, "status": "na", "level": level, "detail": "off in rig.json"})
            continue
        try:
            status, detail = fn()
        except Exception as e:
            status, detail = "na", f"probe error: {e!r}"
        out.append({"check": name, "status": status, "level": level, "detail": detail})
    return out


def blocking(results):
    return [r for r in results if r["status"] == "fail" and r["level"] == "block"]


def _counters():
    swapin = ticks = None
    try:
        with open("/proc/vmstat") as f:
            swapin = next((int(l.split()[1]) for l in f if l.startswith("pswpin ")), None)
        disks = {os.path.basename(p) for p in glob.glob("/sys/block/*")
                 if not os.path.basename(p).startswith(SKIP_DISKS)}
        with open("/proc/diskstats") as f:
            ticks = {x[2]: int(x[12]) for x in (l.split() for l in f) if len(x) > 12 and x[2] in disks}
    except (OSError, ValueError):
        pass
    return swapin, ticks


class Sampler:
    def __init__(self, rig, out_path, interval_s=1.0, on_floor=None):
        self.rig, self.out_path, self.interval_s, self.on_floor = rig, out_path, interval_s, on_floor
        self.floor = floor_gib(rig)
        self._phase, self._rows, self._fired = "start", [], False
        self._ev = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def start(self):
        self._thread.start()
        return self

    def phase(self, name):
        self._phase = name

    def _sample(self, prev):
        st = state(self.rig)
        row = {"t": round(time.time(), 3), "phase": self._phase, **st["host"], "on_ac": st["on_ac"]}
        for g in st["gpus"]:
            for k, v in g.items():
                if k != "index":
                    row[f"gpu{g['index']}_{k}"] = v
        swapin, ticks = _counters()
        row["swapin_mib_s"] = row["disk_busy_pct"] = None
        if prev is not None:
            dt = row["t"] - prev[0]
            if dt > 0 and swapin is not None and prev[1] is not None:
                row["swapin_mib_s"] = round((swapin - prev[1]) * os.sysconf("SC_PAGE_SIZE") / 2**20 / dt, 2)
            if dt > 0 and ticks and prev[2]:
                row["disk_busy_pct"] = round(max((ticks[d] - prev[2].get(d, ticks[d])) / (dt * 10) for d in ticks), 1)
        return row, (row["t"], swapin, ticks)

    def _loop(self):
        prev = None
        with open(self.out_path, "a") as f:
            while True:
                t0 = time.time()
                try:
                    row, prev = self._sample(prev)
                except Exception as e:
                    row = {"t": round(t0, 3), "phase": self._phase, "error": repr(e)}
                self._rows.append(row)
                f.write(json.dumps(row) + "\n")
                f.flush()
                avail = row.get("mem_avail_gib")
                if avail is not None and avail < self.floor and not self._fired:
                    self._fired = True
                    if self.on_floor:
                        try:
                            self.on_floor()
                        except Exception as e:
                            print(f"rig.Sampler: on_floor callback failed: {e!r}", file=sys.stderr)
                if self._ev.wait(max(0.0, self.interval_s - (time.time() - t0))):
                    return

    def stop(self):
        self._ev.set()
        if self._thread.is_alive():
            self._thread.join(timeout=60 + self.interval_s)
        rows = list(self._rows)
        phases = {}
        for r in rows:
            p = phases.setdefault(r["phase"], {})
            for k, v in r.items():
                if k != "t" and _finite(v):
                    p.setdefault(k, []).append(v)
        med = {ph: {k: round(statistics.median(v), 3) for k, v in m.items()} for ph, m in phases.items()}
        avail = [r["mem_avail_gib"] for r in rows if r.get("mem_avail_gib") is not None]
        busy, detail = self._busy(rows, med)
        return {"phases": med, "host_ram_min_gib": min(avail) if avail else None,
                "host_busy": busy, "host_busy_detail": detail}

    def _busy(self, rows, med):
        c = _merge(DEFAULTS["checks"]["host_busy"], (self.rig.get("checks") or {}).get("host_busy") or {})
        if c.get("level") == "off" or not rows:
            return False, None
        cpus = rows[0].get("cpus") or os.cpu_count() or 1
        base_load = (rows[0].get("load1") or 0) / cpus
        base_disk = next((r["disk_busy_pct"] for r in rows if r.get("disk_busy_pct") is not None), 0)
        hits = []
        for ph, m in med.items():
            if ph in UNTIMED_PHASES:
                continue
            if "load1" in m and m["load1"] / cpus - base_load > c.get("load_per_cpu", 0.5):
                hits.append(f"{ph}: load {m['load1'] / cpus:.2f}/CPU vs idle {base_load:.2f}")
            if "disk_busy_pct" in m and m["disk_busy_pct"] - base_disk > c.get("disk_busy_pct", 50):
                hits.append(f"{ph}: disk busy {m['disk_busy_pct']:.0f}% vs idle {base_disk:.0f}%")
        return bool(hits), "; ".join(hits) or None


def noise(ledger="ledger.jsonl", window=20):
    by, skipped, used = {}, 0, 0
    with open(ledger) as f:
        for line in f:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if not isinstance(r, dict) or (r.get("schema") or 1) < 2:
                skipped += 1
                continue
            if r.get("ok") and r.get("config_hash"):
                by.setdefault(r["config_hash"], []).append(r)
    configs = {}
    for h, rs in by.items():
        rs = rs[-window:]
        used += len(rs)
        keys = sorted({k for r in rs for k in list(r.get("metrics_passes") or {}) + list(r.get("metrics") or {})})
        out = {}
        for m in keys:
            ss, df, means, npass = 0.0, 0, [], []
            for r in rs:
                vals = [float(v) for v in (r.get("metrics_passes") or {}).get(m) or [] if _finite(v)]
                if len(vals) >= 2:
                    ss += statistics.variance(vals) * (len(vals) - 1)
                    df += len(vals) - 1
                if vals:
                    means.append(statistics.fmean(vals))
                    npass.append(len(vals))
                elif _finite((r.get("metrics") or {}).get(m)):
                    means.append(float(r["metrics"][m]))
                    npass.append(1)
            if not means:
                continue
            mean = statistics.fmean(means)
            sdw = math.sqrt(ss / df) if df else None
            sdb = statistics.stdev(means) if len(means) >= 2 else None

            def pct(s):
                return None if s is None or not mean else round(100 * s / abs(mean), 3)

            out[m] = {"mean": round(mean, 4), "sd_within": None if sdw is None else round(sdw, 4), "df_within": df,
                      "sd_between": None if sdb is None else round(sdb, 4), "loads": len(means),
                      "passes_mean": round(statistics.fmean(npass), 2), "sd_within_pct": pct(sdw),
                      "sd_between_pct": pct(sdb)}
        configs[h] = {"names": sorted({str(r.get("name")) for r in rs}), "loads": len(rs), "metrics": out}
    return {"rows_used": used, "schema1_skipped": skipped, "configs": configs}


def _opt(args, name, default=None):
    if name not in args:
        return default
    i = args.index(name)
    if i + 1 >= len(args):
        sys.exit(USAGE)
    return args[i + 1]


def _ints(s):
    try:
        return [int(x) for x in s.split(",") if x.strip()] if s else None
    except ValueError:
        sys.exit(USAGE)


def _sd(s, p):
    if s is None:
        return "-"
    return f"{s:.4g} ({p:.2f}%)" if p is not None else f"{s:.4g}"


def _detect_cli(args):
    out, rig = _opt(args, "--out", "rig.json"), detect()
    if os.path.exists(out) and "--force" not in args:
        with open(out) as f:
            stored = json.load(f)

        def view(d):
            return json.dumps({k: d.get(k) for k in ("platform", "collectors")}, indent=2, sort_keys=True).splitlines()

        diff = list(difflib.unified_diff(view(stored), view(rig), out, "detected", lineterm=""))
        print("\n".join(diff) if diff else f"{out}: platform and collectors match detection")
        print(f"{out} exists: not overwritten (use --force)")
        return 0
    with open(out, "w") as f:
        json.dump(rig, f, indent=2)
        f.write("\n")
    p, c = rig["platform"], rig["collectors"]
    print(f"wrote {out}: {p['os']}, {p['gpu_vendor']} x{len(p['gpus'])} via {c['gpu']}, host via {c['host']}, "
          f"{p['ram_gib']} GiB RAM, {p['cpus']} CPUs, RAM floor {floor_gib(rig):g} GiB")
    print('next: put the safety daemons that must stay alive into "hooks" and the settings not to touch into '
          '"settings.protected"')
    return 0


def _noise_cli(args, rig_path):
    window = 20
    if os.path.exists(rig_path):
        with open(rig_path) as f:
            window = int((json.load(f).get("noise") or {}).get("window") or 20)
    ledger = _opt(args, "--ledger", "ledger.jsonl")
    if not os.path.exists(ledger):
        sys.exit(f"{ledger} not found")
    res = noise(ledger, window)
    if "--json" in args:
        print(json.dumps(res, indent=2))
        return 0
    print(f"{res['rows_used']} ok schema-2 rows used (window {window} loads per config), "
          f"{res['schema1_skipped']} schema-1 rows skipped")
    print(f"{'config_hash':12}  {'metric':24} {'loads':>5} {'passes':>6} {'mean':>11} {'sd_within':>18} "
          f"{'sd_between':>18}  names")
    for h, c in res["configs"].items():
        for m, v in c["metrics"].items():
            print(f"{h[:12]:12}  {m:24} {v['loads']:>5} {v['passes_mean']:>6} {v['mean']:>11.4g} "
                  f"{_sd(v['sd_within'], v['sd_within_pct']):>18} {_sd(v['sd_between'], v['sd_between_pct']):>18}"
                  f"  {','.join(c['names'])}")
    return 0


def main(argv):
    if not argv or argv[0] not in ("detect", "check", "state", "noise") or "-h" in argv or "--help" in argv:
        sys.exit(USAGE)
    cmd, args = argv[0], argv[1:]
    if cmd == "detect":
        return _detect_cli(args)
    rig_path = _opt(args, "--rig", "rig.json")
    if cmd == "noise":
        return _noise_cli(args, rig_path)
    rig = load(rig_path)
    if rig.get("_source") == "detected":
        print(f"note: {rig_path} not found; using detected defaults (write it with: python3 scripts/rig.py detect)",
              file=sys.stderr)
    if cmd == "state":
        print(json.dumps(state(rig), indent=2))
        return 0
    res = preflight(rig, _ints(_opt(args, "--cards")), _ints(_opt(args, "--allow-pids")))
    for r in res:
        print(f"{r['check']} {r['status']} {r['level']} {r['detail']}")
    return 1 if blocking(res) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
