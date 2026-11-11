---
name: principle-encode-lessons-in-structure
description: "Apply when you catch yourself writing the same instruction a second time, or notice a recurring correction. Encode the rule as a lint, metadata flag, runtime check, or script instead of more text."
disable-model-invocation: true
---

# Encode Lessons in Structure

When you catch yourself writing the same instruction a second time, or notice a recurring correction, encode the rule as a lint, metadata flag, runtime check, or script instead of more text.

If the lesson needs judgment and cannot be encoded, make the instruction more prominent and add an example of the failure mode.

The `reflect` skill runs this on one session, started by a person or by `arkan-mode`. The `correct` skill runs it on the whole repo's history and lands the checks.

**Corollary:** If the fix is structural, only use the structural fix. The instruction is the symptom.
