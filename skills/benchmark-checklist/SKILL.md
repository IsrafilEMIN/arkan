---
name: benchmark-checklist
description: "Vet a performance measurement (limiter, tuning, limits, errors, repeatability, relevance, and whether the work happened) before you report or act on it. Use when you run a benchmark or report a speedup or regression you measured."
---

# Benchmark checklist

Use this when you produce a performance number: a pull request's before and after, a regression claim, a harness for repeated tuning, or a choice between libraries or settings. Answer each question with evidence from a run, not a guess about the code. It is the working form of **explain the number** (`arkan-mode/principles/verification.md`).

For a quick ballpark the person asked for, one run is enough. Still check questions 4 and 7, and say it is one run. Skip the rest unless that run looks wrong. A choice between options is never a ballpark.

## Before you run anything

- Write down the claim you expect to make, in the words you would ship ("export is 30% faster at p50 on the 60k-row dataset"). The questions test that sentence.
- Read the measurement script. Note what it times, counts and ignores.
- Check the load with `uptime` and the core count (`nproc` on linux, `sysctl -n hw.ncpu` on macos). If the machine is busy, find out what is running. If you cannot stop it, interleave the sides so both see the same noise, and say so in the report.
- Under underground's sandbox, a profiler or tracer may be refused; run it where the person can (a plain terminal), and say which numbers came from where.

## The questions

1. **Why not double?** Name the limiter. Profile in a run you do not report, because profilers and tracers slow the work down. Use cpu per process (`top`, `pidstat`), a runtime profiler (`node --cpu-prof`, `py-spy`, `perf`), i/o wait, and syscall counts (`strace -c` on linux), then map the hot spot to source. Watch the load generator too: if it saturates first, you measured the load generator. If a change did not move the number, the limiter explains why; find it before you call the change useless.
2. **Was it tuned?** Run every side the way production runs it: release builds, production flags and env, batching and transaction settings, connection pools, caches as warm or cold as production sees them, the same versions and data. If one side runs on defaults, you compared configurations, not implementations. A limiter that is a setting (a commit per row, a debug build, a missing index) means that side is untuned: tune it and measure again before you pick a winner. If you cannot tune it, do not pick a winner from that run. When the person is choosing what to adopt, narrowing the claim to the code as it ships today does not fix this, because they adopt the option, not today's settings.
3. **Did it break limits?** Do the arithmetic. Compare bytes per second with disk and network bandwidth, operations per second times cost per operation with your cores, and the time saved with the time the changed piece took. Removing a piece that takes 10% of the run can make the run at most about 11% faster. A result past a limit measured something other than the work: a cache, a no-op, or a bug.
4. **Did it error?** Count failures and non-success responses, and check that outputs are correct, not just present. Rejections are often fast; timeouts and retries are slow. If the script does not count errors, add the count.
5. **Does it reproduce?** Run each side at least 5 times, alternating (A, B, A, B…) so warmup, lazy setup, caches and drift favor neither. Report the median and range. A gap smaller than the run-to-run variation is no measurable difference. When the call is close, use a rank-sum test or the harness's own statistics.
6. **Does it matter?** Next to any micro result, measure the end-to-end path a user waits on, with realistic data sizes and concurrency, and report the micro result as a share of the whole. A helper that takes 1% of a request can make the request at most 1% faster, however fast the helper gets.
7. **Did it even happen?** Confirm the work ran inside the timed region: the request reached the server, the rows were written, the bytes were read, and the code used the result. Lazy code (generators nobody iterates, promises nobody awaits, results the jit can discard) and timeouts produce numbers for work that never happened.

## Report

- Lead with the verdict: faster, slower, no measurable difference, or inconclusive.
- Give the number with its unit, the run count, the range and the limiter. For example: "p50 41 ms → 33 ms, median of 7 runs per side, range 32 to 35 ms after, bound by json parsing on one core."
- Call the verdict inconclusive when you claim a difference but cannot name the limiter, when a side ran untuned, or when you could not check questions 4 and 7. Name the gap.
- Keep a pull request body to one primary number, in its evidence section (the `pr` skill's template). Put the runs, range and limiter evidence in a linked file or notes.
- When a later change is judged against this number, keep the harness frozen and have it print error and work counts, so each keep-or-revert checks questions 4 and 7 for free.
