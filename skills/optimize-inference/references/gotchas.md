# Engine and hardware gotchas

These were found the hard way. Versions matter; re-check on newer releases.

## General

- **A second engine on the same GPU,** or a stray benchmark still running, silently halves results or crashes both. Lock the GPU (`scripts/queue.sh`) and check that the cards are idle before each run (`scripts/rig.py check`, `rig.md`).
- **Correlate "device lost" crashes with the kernel log before blaming code.** Arc Pro B70 crashes turned out to be PCIe link drops: AER replay timeouts, then link down, 8 times in 3 days. They also spread to other devices on the same root complex.
- **Forced container stops during a long prefill** caused an Intel xe GPU page fault (`SKILL.md` rule 7).
- **Very large images can crash vision encoders.** Cap the longest edge.
- **Gateway or proxy timeouts** (often 600 s) cut off long-context tests. Test against the engine directly. Retry only on dropped connections, never on timeouts.
- **Shells and agents:** `pkill -f pattern` can kill the shell that runs it, and `pgrep -f` matches its own command line, so a wait on it never ends. Kill by PID. What to wait on: `rig.md`, Six invariants.
- **Agent restarts** kill child processes. Detach long jobs and make them resumable:
  - macOS: use the `python3` `os.setsid()` form in `scripts/queue.sh`. macOS has no `setsid`, and its `nohup` fails without a console session.
  - Linux: `setsid nohup … & disown`.

## Multi-GPU

- **The driver's peer-access flag can lie.** `cudaDeviceCanAccessPeer` (or the vendor equivalent) can report P2P as available while copies fail, fall back to host staging, or corrupt data. Measure a real peer copy: check its bandwidth and compare the data. Check the kernel log for IOMMU faults (for example `AMD-Vi` or `DMAR` page-fault lines) during the copy; an IOMMU in translated mode can block or slow P2P.
- **For overlapped collectives, prefer copy engines over spinning kernels.** A kernel that spin-waits for a peer's flag holds SMs that the overlapped compute needs, and hangs under tools that serialize kernels. An async peer copy runs on a copy engine and leaves the SMs free.

## Builds and code generation

- FMA contraction, a cold instruction cache and stale build objects: `kernel-work.md`, custom engines.

## vLLM

- Prefix caching may be off by default for hybrid (SSM/GDN) models. Enable it and check `cached_tokens`.
- On Intel XPU, only `FULL_DECODE_ONLY` graphs worked. Piecewise capture failed with `UR_RESULT_ERROR_OUT_OF_RESOURCES`, and so did dynamic per-batch draft length, which forces piecewise graphs.
- On unified memory, `gpu_memory_utilization` is compared against free host RAM, and values near 0.985 are refused.

## SGLang

- **Hybrid models need `--max-mamba-cache-size`** large enough for N requests plus speculative state. Otherwise concurrency silently stays at 1. A value of 4 was too small for even one request with speculation.
- **The XPU backend (0.5.x) had several bugs, patched in a plugin:**
  - verify was greedy-only at any temperature;
  - a stale GDN wrapper;
  - CUDA-only guards on mamba scatter;
  - missing fp8 descale in extend;
  - an fp8 Q cast in decode.
  - Prefill graphs are not supported by the XPU attention backend.
- **`--num-continuous-decode-steps` had no effect** with speculative decoding on.
- **Shared-expert fusion** is only enabled for some backends.
- **Large prefill-graph captures (2,048 tokens) used 6.3 GB and crashed;** capture up to 256–512.

## llama.cpp / GGML

- Quantized KV (q8_0) and MTP/draft slowdowns: measured in `levers.md`, Decode.
- Check work-group sizes in backend kernels: a work-group of 1 in a SYCL copy kernel cost 7.8×.

## ExLlama / TabbyAPI

- On ROCm, HIP graphs leaked until crash. Disabling them was stable at 115.6 tok/s.

## Hardware

- **Intel Xe (Arc), PyTorch XPU:**
  - `torch.topk` segfaulted on wide inputs (above about 2–8K). Use staged top-k or Gumbel-max with `multinomial`.
  - `UR_RESULT_ERROR_OUT_OF_RESOURCES` means too-large or piecewise graphs.
- **Intel integrated GPUs and other unified-memory devices:** GPU memory is invisible to cgroups; see `methodology.md`, Memory.
- **Apple silicon:** the GPU wired-memory limit (`iogpu.wired_limit_mb`) caps usable memory. Speculation on bandwidth-poor chips: `levers.md`, Decode.
- **Hybrid GDN/SSM state dtype:** fp16 state produced `!!!` garbage on one SGLang XPU build, while another engine stored it in fp16 without issue. Verify output after changing the state dtype.

## Older NVIDIA cards: Volta (sm_70) and Turing (sm_75)

Unlike the sections above, these notes come from reading headers, tool output and NVIDIA documentation, not from a hill-climb. The source of each is given. Confirm on your own card and toolkit.

- **Much kernel advice assumes Ampere or newer.** Volta has none of the following:
  - bf16 tensor cores;
  - TF32;
  - FP8;
  - `cp.async` async copies;
  - TMA or `wgmma`.

  Skip advice that relies on them: "use TF32 matmuls", bf16 tensor-core GEMMs, FP8 KV with native math, async-copy pipelines.
- **bf16 storage is cheap to convert; bf16 math is not native.** In CUDA 12.8's `cuda_bf16.hpp`, bf16 → fp32 below sm_90 is one `mov.b32` (sm_90 uses `cvt.f32.bf16`). So bf16 weights with FP32 accumulation cost loads, not conversion. Other bf16 arithmetic on these cards can go through FP32 emulation; read the SASS.
- **Tensor-core shapes differ.** Volta `mma.sync` is m8n8k4 and `wmma` is 16×16×16 for fp16. Tile rules written for Ampere's m16n8k16 do not carry over (PTX ISA guide).
- **Toolkit support:** NVIDIA's CUDA 13 release notes remove Volta and older cards as compile targets, so pin a CUDA 12.x toolkit for sm_70 work. Docs and skills written against CUDA 13 can describe APIs you cannot build for these cards.
- **Profiling:** nsys GPU metrics sampling refuses these cards. On two Tesla V100-PCIE-32GB with nsys 2024.6.2, `nsys profile --gpu-metrics-devices=help` printed "Unsupported architecture" for both. Use kernel traces, NVTX ranges and ncu instead (`profiling.md`).
- **Turing (sm_75) also has no bf16 tensor cores.** Some guides say "T4 does not support BF16". That holds for tensor-core math, not for bf16 storage with FP32 math.

## Profilers

- **ncu clock locking, kernel replay, spin-wait hangs, nsys trace memory, profiler-only gaps, DRAM throughput targets and `ERR_NVGPUCTRPERM`:** `profiling.md`. Ask before changing driver options.
- **`nsys recipe …` needs extra Python packages** that a toolkit install may not have. With nsys 2024.6.2 in CUDA 12.8 it failed with `No module named 'psutil'` (`profiling.md`). `nsys stats -r …` reports work without them.
