---
name: hardware-debug
description: Debug PC hardware step by step, with the user as the hands.
---

# Hardware debug

The user is not a hardware specialist and does the physical work. A wrong instruction can break a part. Accuracy beats speed.

## Before any instruction

1. **Pin the exact parts.** Model numbers for board, CPU, PSU, GPU, cooler, cables. Ask for a photo of labels and connectors when one is unclear. Never assume a cable type from a generic description.
2. **Check the manual and the community.** Read the manual page for the connector or setting in question. Find a report with the same parts and the same symptom, and link it. If none exists, say "no matching case found". Do not call something impossible until you searched for people who did it.
3. **Name the goal.** If a side problem appears, say "this is a secondary problem" and ask before chasing it.

## Safety

- Before the user touches, adds, or removes a part: switch off the PSU and unplug the power cable.
- Tell the user to touch bare metal on the case to ground themselves before handling parts.
- Never power on a CPU without its cooler installed.
- Warn before anything that needs force, can bend the board, or touches mains power.

## Ledger

Keep a running list, and show it when it changes:

- **Done:** steps the user already did, with the result.
- **Ruled out:** causes a test already excluded.
- **Confirmed:** facts about the parts and their state.

Read the list before each answer. Never repeat a step from "done" or a cause from "ruled out" unless new evidence reopens it, and then say what reopened it.

At the end, show the final ledger and the working configuration: slots, cables, BIOS settings, and anything still pending.

## Isolate the cause

Isolate one variable at a time: minimal boot (board, CPU with its cooler, one RAM stick, PSU), then add parts back one at a time. Read the board's status lights (Q-LED, debug code) at each step and record them.

## Each physical step

- One action per step, in plain words: which connector, which side, which slot, what it looks like.
- Say why the step is needed, and if a simpler way gives the same result.
- Say the expected result (fan spins, LED colour, beep, POST screen).
- Never ask the user to remove a part that is hard to remove unless the test needs it.

## Before risky changes

BIOS updates, firmware or VBIOS flashing, CMOS clears and BIOS setting changes:

1. Back up first: the current ROM, the BIOS profile to a USB drive, a photo of every changed setting.
2. Write down the recovery path before starting (BIOS FlashBack, CMOS clear, a second GPU, the backup ROM).
3. Check that the recovery path works on this exact board before running the risky step.

## Missing parts

Give the exact spec from the manufacturer (e.g. "M3 x 6 mm pan head") and the quantity. Use `deal-hunt` to find where to buy it.
