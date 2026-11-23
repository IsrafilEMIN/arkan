# Profiling for the hill-climb

Profiles explain. The A/B with controls decides. Profilers add overhead, and ncu serializes kernels and locks clocks, so never accept or reject a change from profiler times.

The commands below are for NVIDIA tools: nsys for the timeline, ncu for one kernel. The reading rules apply to any vendor's tools.

## Timeline first, then one kernel

- **Start with nsys.** It shows what ran, when, on which stream and on which GPU. ncu explains one kernel. Open it only after the timeline has told you which kernel matters.
- **Profile a warmed step.** Keep startup, JIT and graph capture out of the capture. Choose one of these:
  - Call `cudaProfilerStart()` and `cudaProfilerStop()` around a few steps in the engine, then run `nsys profile -c cudaProfilerApi …`.
  - Put an NVTX range around the steps, then run `nsys profile -c nvtx -p RANGE_NAME …`.
  - As a coarse fallback, use `--delay` and `--duration`.
- **CUDA graphs** show up as one item by default. Use `--cuda-graph-trace=node` to see each kernel inside the graph. It costs more overhead, so do not time with it on.

## Three numbers that are not the same

1. **The sum of kernel durations.**
2. **GPU busy time:** the union of the intervals in which any kernel ran.
3. **Wall time of the step.**

What the differences mean:

- **Sum greater than busy time:** kernels overlap on several streams. A kernel's share of the sum is not time you can remove, and shares do not add up to a speedup.
- **Wall time greater than busy time:** the GPU sits idle. Before blaming kernels, check these causes:
  - host work and scheduling;
  - launch gaps;
  - a synchronisation;
  - waiting for another GPU;
  - dropped trace records. Missing lanes look like idle time.
- **`nsys stats -r cuda_kern_exec_sum report.nsys-rep`** splits each kernel's time into API call, queue and execution. A long queue means the GPU is busy. A short execution with long host gaps means the host is the bottleneck.
- **`nsys stats -r cuda_gpu_kern_sum`** gives totals per kernel. Use it to rank kernels, then check each one's exposed time on the timeline.

## Exposed time and joins

- **What counts is time on the critical path:** the part of a kernel that nothing else overlaps.
- **At a producer → consumer join,** the consumer waits. On GPUs with programmatic dependent launch (Hopper and later), the consumer can start early. Its own duration then includes the wait, which looks like slow arithmetic but is not.
- **Under tensor parallel, every all-reduce is a join across GPUs.** The faster rank's spare time shows up as time inside the collective kernel. Align the per-rank timelines on the collective; the slowest rank sets the step.
- **Check the join before proposing a fusion, an extra stream or split-K:**
  - more blocks can compete with the kernels next to them;
  - fewer launches can leave the same wait in place.

## Stages with NVTX (any engine)

- **Put NVTX ranges around stages in the engine:** attention, MoE, all-reduce, LM head, sampling. This gives the "profile by stage" step in `methodology.md` for a custom engine.
  - NVTX v3 is header-only: `#include <nvtx3/nvToolsExt.h>`, from the CUDA toolkit's `include/nvtx3`. No library link is needed.
- **`nsys stats -r nvtx_gpu_proj_sum report.nsys-rep`** projects the ranges onto GPU time. You get GPU time per stage even though launches are asynchronous.
- **To compare control and candidate,** profile both the same way and compare the per-kernel and per-stage tables.
  - `nsys recipe diff` does this where your nsys version has it (`nsys recipe --help` lists recipes).
  - Recipes need extra Python packages; the error message names the install script. Ask before installing anything.
  - `nsys stats` reports work without those packages.

## ncu, for one kernel

- **Capture one kernel:**

  ```bash
  ncu -k regex:NAME --launch-skip S --launch-count C --set full -o out <app>
  ```

  Add `-lineinfo` to the build to map stalls to source lines.
- **ncu locks the GPU clocks to base by default** (`--clock-control base`). Its durations are therefore longer than serving times. Compare ncu numbers only with other ncu numbers. Use `--clock-control none` to see boost behaviour.
- **ncu replays each kernel several times** to collect counters. Overlap between streams disappears while it runs. Use it to explain a kernel, never to time the step.
- **For a memory-bound kernel,** read `dram__throughput.avg.pct_of_peak_sustained_elapsed` and the achieved bytes per second. Compare them with your *measured* bandwidth (`ceilings.md`), not the spec sheet.
  - High DRAM throughput is the goal here.
  - Low DRAM throughput is good only for a compute-bound kernel that reuses data from cache.
- **Occupancy:** aim for enough to hide latency, not the maximum.
- **Permission error `ERR_NVGPUCTRPERM`:** the NVIDIA driver restricts performance counters to administrators.
  - The fix is the driver option `NVreg_RestrictProfilingToAdminUsers=0` (it takes effect after a module reload or reboot), or running ncu as an administrator.
  - Changing `perf_event_paranoid` does not fix it.
  - Ask the user before changing driver options.

## Tool and hardware limits

- **nsys GPU metrics sampling** (`--gpu-metrics-devices`) does not support every GPU. Run `nsys profile --gpu-metrics-devices=help` to list what your cards support. On two Tesla V100-PCIE-32GB cards with nsys 2024.6.2 it printed "Unsupported architecture" for both.
- **If several nsys or ncu installs exist** (a distro package and the CUDA toolkit), run `--version` on each. Use the one that matches the toolkit you build with.
- **Multi-GPU:** profile every rank in the same capture, or align the captures on a collective. One rank's profile hides the joins.
