---
name: blast-radius
description: "Map what a change could break somewhere else before it ships, beyond the diff, and prove the one fact it is safe because of by running real code instead of writing it up. Use for 'blast radius of X', 'what could this break', or a small diff you don't trust."
---

# Blast radius

Find what a change breaks somewhere else, before it ships. Use for "blast radius of X", "what could this break", or a small diff you don't trust yet.

A companion to `how` and `why`: `how` says what the code does, `why` says why it is shaped that way, blast radius says what it breaks elsewhere.

Listing the callers is not the job: grep does that in a second. The job is the breakage grep won't show you.

## Don't trust your own writeup

A blast-radius writeup that sounds right is worthless: it reads as convincing whether or not it is true. So don't hand back the writeup alone. Find the one or two facts the whole thing depends on and prove them by running code.

### How sure are you

For each fact the change's safety depends on, take it as far down this list as is cheap, and say where it stopped.

1. You said so. Worthless on its own.
2. You pointed at the line: a real `file:line`, or the library's own source.
3. You showed the bad case cannot happen: you walked the failure step by step and it does not reach.
4. You ran it: a script or test that calls the real code and fails loud if you are wrong.
5. You reproduced it in the running app (the repo's verify skill, if it has one).

Step 4 is usually one small script that imports the same library the app ships and calls the exact function you are worried about.

## Steps

1. **Read the change.** The diff, the symbols it adds, changes and deletes, and what it now does differently, including the part the diff doesn't spell out. Use `why` step 2 to pull the pull request and its commits.
2. **Find the one fact it is safe because of.** Most changes that look risky are safe because of a single fact, like "this call only drops cache entries that are already dead". Find that fact. If it holds, most risky cases clear at once. Spend your time here, not on a long list of maybes.
3. **Look where grep stops.** Read the source of the library you call, and check its pinned version and any local patch. Work out when things run: microtasks, unmount and teardown, framework lifecycles. Follow what a symbol search misses: the json an api returns, a database column, a wire format, another language reading the same bytes, a feature flag, code three hops downstream, another repo that reads the same strings or files.
4. **Be honest about each risk.** Give it a real chance of happening and a real cost if it does. Keep the risks you confirmed; list the ones you checked and cleared separately. Cite a real `file:line`; a search that finds nothing is still an answer; never invent a caller or an api.
5. **Prove the one fact.** Write a script or test that runs the real code, run it, and paste what happened.
6. **For a big or wide change, run it as an `arena`:** ask more than one model the same question and merge the answers. Different models catch different real bugs.

## What to hand back

- **What it does.** What changed, including the part that isn't obvious.
- **The one fact it is safe because of.** State it, say which step you took it to, and show the proof. If you could not prove it, write "unproven".
- **Risks.** Each names how it breaks, the `file:line`, how likely and how bad, and how to check. Paste the proof for the ones that matter.
- **Cleared.** What you checked and why it is fine.
- **Before you merge.** The cheapest test or repro that catches the real bug, including the script you wrote.

Write it per `unslop`, cite real code, and strip anything private before it goes anywhere public (a pull request comment is public to everyone who can read the repo).
