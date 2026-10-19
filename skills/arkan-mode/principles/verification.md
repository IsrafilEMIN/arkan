# verification principles

## prove it works

check every result against the real thing. do not trust a proxy, a self-report or "it compiles".

- check that a process is alive directly, not through a file it wrote.
- read the actual value, not a cached or derived copy.
- when a check fails, suspect the way you observed it before you suspect the system.
- the strongest proof is a script that runs the same comparison again. write it, run it, and keep its output where a reviewer can rerun it.
- a subagent's "done" is not proof. read its diff and run its check yourself.

## fix root causes

when you debug, do not fix the symptom. trace each problem to its cause and fix it there.

- reproduce first.
- ask "why" until you reach the cause.
- do not add a guard that hides the crash (a null check that silences an error is a symptom fix).
- if a workaround needs a paragraph of comment to justify it, the code is wrong. fix the code.
- fix the pattern, not only this instance. search for the same pattern and fix every copy.
- when stuck, add logs or a debugger and read the real values. do not guess.
- **"fails after restart"**: suspect stale saved state first (config, cache, lock files, serialized state).

## sequence verifiable units

order work as small units. each unit ends in a state you can check. do not start the next unit while the current one is red.

- **while you work:** each unit is known-good state, one change, run the check, then go on. a break found at the unit that caused it is cheap to find. a break found after a batch is buried.
- **when you deliver:** order commits so they prove the work. the classic order is the failing test first, then the fix. other good orders: removal before the reshape, a baseline before the change, scaffold before the feature.

## test behavior, not implementation

the full text is the `principle-test-behavior-not-implementation` skill (`../../principle-test-behavior-not-implementation/SKILL.md`). read it before you write, change or keep a test.

## explain the number

before you trust, report or act on a number you measured (a speedup, a latency, a regression, an eval score):

- **ask "why not double?"** name what limits the result: a core, a lock, the disk, the network, the load generator. get it from a profile or counters taken during the run. a guess from reading code is not a limit.
- **list what else the number could measure,** and rule out each one with evidence: errors, cached or skipped work, code that never ran, a side left on default settings, noise, a piece too small to matter.
- **keep the evidence with the number:** how many runs, the spread, and the limit.

if your evidence has no run count, no spread or no named limit, you skipped this.
