### Bug fix

**You own this task. Plan, review, verify.** Delegate investigation and the fix to subagents, stay in the lead. Match each subagent's model to the job, per **Subagents** in `SKILL.md`.

Be scientific. Every shipped line traces to runtime evidence. Belt-and-suspenders that "might help" is a hypothesis, not a fix. It does not ship. When evidence refutes a hypothesis, revert what it motivated. The smallest change the evidence justifies ships, nothing more.

Skip a step only with a stated reason. For a simple bug, steps 2 to 4 can be one short pass, but the loop in step 1 still comes first.

**Redact.** This playbook has you show commands, outputs and captured artifacts. Redact every secret first: write `<REDACTED>` in its place. Build loops against env vars, so the credential stays in the environment, not in what you show. Captured artifacts carry auth headers: quote only the lines that carry the signal. If the redacted output is not enough to diagnose the bug, say so and ask the user.

1. **Build a feedback loop and reproduce.** This is the core of the work. With a tight pass/fail signal that goes red on _this_ bug, you will find the cause: bisection, hypotheses and instrumentation all consume it. Without one, no amount of reading code will save you. Spend disproportionate effort here. Be aggressive and creative.
   Reproduce it yourself on the matching surface: the repo's verify skill if it has one, else drive the app, CLI, or API with your harness's own tools. Do this even when a debug or instrumentation protocol says to ask the user to reproduce. Ask the user only with a stated, specific reason your tools cannot reach the target, and only after driving them as far as they go. If it won't reproduce directly, synthesize the trigger, tighten conditions, or instrument until it fires.
   Ways to build the loop, in rough order:
   1. A failing test at whatever seam reaches the bug: unit, integration, e2e.
   2. A curl or HTTP script against a running dev server.
   3. A CLI call with a fixture input, diffing stdout against a known-good snapshot.
   4. A headless browser script (Playwright, Puppeteer) that drives the UI and asserts on DOM, console or network.
   5. Replay a captured trace: save a real request, payload or event log to disk and replay it through the code path alone.
   6. A throwaway harness: a minimal subset of the system (one service, mocked deps) that hits the bug path with one function call.
   7. A property or fuzz loop: for "sometimes wrong output", run 1000 random inputs and look for the failure.
   8. A bisection harness: when the bug appeared between two known states (commit, dataset, version), automate "boot at state X, check" so you can `git bisect run` it.
   9. A differential loop: run the same input through the old and new version (or two configs) and diff the outputs.
   10. A human-in-the-loop script, last resort. If a person must click, drive _them_ with [`../scripts/hitl-loop.template.sh`](../scripts/hitl-loop.template.sh) so the loop stays structured. Its captured output feeds back to you.

   Tighten the loop once you have one. Make it faster (cache setup, skip unrelated init, narrow the test scope). Make the signal sharper (assert the specific symptom, not "didn't crash"). Make it deterministic (pin time, seed the RNG, isolate the filesystem, freeze the network). A 30-second flaky loop is barely better than none; a 2-second deterministic one is a superpower.
   For a non-deterministic bug, the goal is a higher reproduction rate, not a clean repro. Loop the trigger 100 times, parallelise, add stress, narrow timing windows, inject sleeps. A 50% flake is debuggable; 1% is not, so keep raising the rate.
   If you truly cannot build a loop, stop and say so. List what you tried. Ask the user for access to an environment that reproduces it, a redacted captured artifact (HAR file, log dump, core dump, screen recording with timestamps), or permission to add temporary production instrumentation. Do not form hypotheses without a loop.
   Step 1 is done when you can name **one command** (a script path, a test call, a curl) that you have already run at least once, with its redacted invocation and output shown, and that is:
   - **red-capable**: it drives the real bug path and asserts the user's exact symptom, so it goes red on this bug and green once fixed. "Runs without erroring" does not count.
   - **deterministic**: the same verdict every run (for a flaky bug, a pinned, high reproduction rate).
   - **fast**: seconds, not minutes.
   - **agent-runnable**: you run it unattended; a person in the loop only through the HITL script.

   Run it and watch it go red. Confirm it shows the failure the **user** described, not a nearby one (wrong bug, wrong fix), that it repeats across runs, and capture the exact symptom (error message, wrong output, timing) to check the fix against later. If you catch yourself reading code to build a theory before this command exists, stop: that jump is the failure this step prevents.
2. **Minimise.** Shrink the repro to the smallest scenario that still goes red. Cut inputs, callers, config, data and steps one at a time, re-running the loop after each cut, and keep only what the failure needs. A minimal repro shrinks the hypothesis space and becomes the regression test in step 6. Done when every remaining element is load-bearing: removing any one makes the loop go green.
3. **Form hypotheses.** Seed them by reading the affected subsystem and its history (`git log`, `git blame`); read `GLOSSARY.md` if it exists and the ADRs in the area. Write **3 to 5 ranked hypotheses** before testing any; one hypothesis anchors on the first plausible idea. Each must be falsifiable, so state its prediction: "If <X> is the cause, then <changing Y> makes the bug disappear, or <changing Z> makes it worse." A hypothesis with no prediction is a vibe: sharpen it or drop it. Show the ranked list to the user before testing. They often know something that re-ranks it ("we just deployed a change to #3") or have ruled one out. Don't block on it; if the user is away, go on with your ranking.
4. **Binary-search the cause.** Rule hypotheses out until one survives. Each pass, take the split that cuts the most remaining problem space, get runtime evidence, eliminate. Each probe maps to one prediction from step 3. Change one variable at a time. When program state is unclear, prefer a debugger or REPL (one breakpoint beats ten logs), then targeted logs at the boundaries that split hypotheses. Never "log everything and grep". Don't guess. Tag every debug log with a unique prefix, e.g. `[DEBUG-a4f2]`, so cleanup is one grep. For a performance regression, logs are usually the wrong tool: take a baseline measurement (timing harness, profiler, query plan), then bisect; a measured slowness with no functional bug is the **Perf issue** playbook. For a long or stubborn hunt, use your harness's loop or wake-up tool if it has one. Confirm the surviving *mechanism* with runtime evidence before you plan the fix.
5. **Plan the fix.** If it crosses a function boundary, sketch the types and signatures with empty bodies first. Delegate implementation to a subagent with a specific scope.
6. **Regression test, then fix.** Write the regression test before the fix, but only at a **correct seam**: one where the test exercises the real bug pattern as it occurs at the call site. A seam that is too shallow (a single-caller test when the bug needs several callers, a unit test that cannot rebuild the chain that triggered it) gives false confidence. If no correct seam exists, that is a finding: the architecture prevents locking the bug down. Note it in the reply and the PR. With a correct seam:
   1. Turn the minimised repro into a failing test at that seam.
   2. Watch it fail. If you forced the red by changing code or a fixture, `diff` against a pristine copy to prove the change landed before you trust it.
   3. Apply the fix and watch the test pass.

   See the `tdd` skill for the failing-test-first cadence when the bug has a cheap local test path. Skip the test when it would be expensive, integration-heavy, or unclear, and say why.
7. **Verify on the same surface.** Re-run the step 1 loop against the original, un-minimised scenario. It now passes. "Inconclusive" or wrong-surface is not a pass. Flag it. Unit tests show branch behavior, not bug absence.
8. **Clean up.** Before you call it done:
   - the original repro no longer reproduces (re-run the step 1 loop);
   - the regression test passes, or the missing seam is written down;
   - every `[DEBUG-...]` line is gone (`grep` the prefix);
   - throwaway prototypes are deleted, or moved to a clearly marked debug location;
   - the commit or PR message states the hypothesis that turned out correct, so the next debugger learns from it.
9. **Stage the commits** so the failing repro lands before the fix in git history. A work branch may carry one red-first commit as evidence; the PR head must be green before the PR opens or updates. CI and the merge check the head, not each commit, so never push a red head.
   This is the **sequence verifiable units** principle (`principle-sequence-verifiable-units`): the failing test first and the fix on top.
10. Run **Opening a PR**.

**Reply:** what was broken, root cause, fix, how you verified. Paste failing-then-passing repro output verbatim.
