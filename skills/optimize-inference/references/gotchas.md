# Engine and hardware gotchas

These were found the hard way. Versions matter; re-check on newer releases.

## General

- **A second engine on the same GPU,** or a stray benchmark still running, silently halves results or crashes both. Lock the GPU (`scripts/queue.sh`).
- **Correlate "device lost" crashes with the kernel log before blaming code.** Arc Pro B70 crashes turned out to be PCIe link drops: AER replay timeouts, then link down, 8 times in 3 days. They also spread to other devices on the same root complex.
- **Forced container stops during a long prefill** caused an Intel xe GPU page fault. Always abort, drain, then stop with a timeout.
- **Very large images can crash vision encoders.** Cap the longest edge.
- **Gateway or proxy timeouts** (often 600 s) cut off long-context tests. Test against the engine directly. Retry only on dropped connections, never on timeouts.
- **Shells and agents:** `pkill -f pattern` can kill the shell that runs it, and `pgrep -f` can wait on itself. Kill by PID.
- **Agent restarts** kill child processes. Detach long jobs (`setsid nohup … & disown`) and make them resumable.

## vLLM

- Prefix caching may be off by default for hybrid (SSM/GDN) models. Enable it and check `cached_tokens`.
- On Intel XPU, only `FULL_DECODE_ONLY` graphs worked. Piecewise capture failed with `UR_RESULT_ERROR_OUT_OF_RESOURCES`, and so did dynamic per-batch draft length, which forces piecewise graphs.
- With MTP, streaming sends several tokens per chunk. Use usage stats for token counts.
- mmap loading can be very slow; use `--safetensors-load-strategy eager`.
- On unified memory, `gpu_memory_utilization` is compared against free host RAM, and values near 0.985 are refused.

## SGLang

- **Speculative-decoding acceptance counters** update only when a request finishes.
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

- Quantized KV (q8_0) can be much slower on models with few KV layers.
- MTP/draft support can fall below the no-draft baseline on hard prompts.
- Check work-group sizes in backend kernels: a work-group of 1 in a SYCL copy kernel cost 7.8×.

## ExLlama / TabbyAPI

- On ROCm, HIP graphs leaked until crash. Disabling them was stable at 115.6 tok/s.
- A busy host CPU costs GPU decode on laptops: 107 → 75 tok/s.

## Hardware

- **Intel Xe (Arc), PyTorch XPU:**
  - `torch.topk` segfaulted on wide inputs (above about 2–8K). Use staged top-k or Gumbel-max with `multinomial`.
  - Split-K partial stores need uncached stores plus a clean fence on Xe3.
  - `UR_RESULT_ERROR_OUT_OF_RESOURCES` means too-large or piecewise graphs.
- **Intel integrated GPUs and other unified-memory devices:** GPU memory is invisible to cgroups; see `methodology.md`. Battery and power profiles move results 8–10%.
- **Apple silicon:** bandwidth-poor chips (base M-series) lose with deep speculation. The GPU wired-memory limit (`iogpu.wired_limit_mb`) caps usable memory.
- **NVIDIA Ampere has no FP8 units;** INT4 (AWQ/GPTQ/EXL) wins when bandwidth-bound.
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

- **ncu locks GPU clocks to base by default** (`--clock-control base`). Its kernel times are slower than serving, so never compare them with nsys or serving times.
- **ncu replays each kernel** to collect counters. Multi-stream overlap disappears under it.
- **A high DRAM throughput percentage is the goal for a memory-bound decode kernel.** Some guides call "DRAM throughput < 50%" healthy. That only holds for compute-bound kernels that reuse data from cache.
- **`ERR_NVGPUCTRPERM` from ncu** is the NVIDIA driver's admin-only counter setting (`NVreg_RestrictProfilingToAdminUsers`). `perf_event_paranoid` does not fix it. Ask before changing driver options.
- **`nsys recipe …` needs extra Python packages** that a toolkit install may not have. With nsys 2024.6.2 in CUDA 12.8 it failed with `No module named 'psutil'` and named the install script. `nsys stats -r …` reports work without them. Ask before installing anything.
- **Several nsys installs** (a distro package and the CUDA toolkit) can differ in version and features. Run `--version` on each and use the one that matches your toolkit.
