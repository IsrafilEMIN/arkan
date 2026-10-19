---
name: principle-migrate-callers-then-delete-legacy-apis
description: "Apply when introducing a new internal API while old callers still exist. Migrate callers and delete the old API in the same wave instead of preserving compatibility layers."
disable-model-invocation: true
---

# Migrate Callers Then Delete Legacy APIs

When you decide a new internal API is right, move every caller and delete the old API in the same change. Do not keep both.

- List the callers, move them, and delete the old path.
- Update tests to assert the new contract, and delete tests that only protect pre-refactor implementation details.
- A temporary adapter is an exception with an end date, not the default.
- Two paths for one job make the code harder to change and teach the next agent the wrong way.

**When this applies:**
- No external users depend on backward compatibility
- The project can absorb coordinated breaking changes
- The new API is part of a simplification or refactor initiative
