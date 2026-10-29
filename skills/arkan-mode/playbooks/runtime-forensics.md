### Runtime forensics

**You own the diagnosis. Instrument the live process, don't theorize from source.** The deliverable is a cited diagnosis, not a fix.

1. Capture the live signal on the matching surface: the repo's verify skill if it has one (see `create-verification`), else drive the process with your harness's own tools. A CPU profile for a spinning process, a heap snapshot for a leak, a CDP trace for a visual glitch. A real artifact, not a guess.
2. Reduce the artifact to the smoking gun: the function on the hot path, the retainer chain from the leaked object to a GC root, the loop firing without input. Parse large artifacts in a subagent (**guard the context window**, `principle-guard-the-context-window`), keep the reduced finding in the main thread. Match each subagent's model to the job, per **Subagents** in `SKILL.md`.
3. Prove the mechanism before believing it. Where the runtime supports it, inject instrumentation into the running process (for example a devtools-protocol eval) or hotfix the live code without reloading, to confirm the hypothesis cheaply.
4. Map the finding back to source: file, symbol, the line that allocates or schedules.

**Reply:** the signal captured, the reduced finding, how you proved the mechanism, the source location, artifact paths. No fix unless asked. Hand back to **Bug fix** or **Perf issue** once the cause is known.
