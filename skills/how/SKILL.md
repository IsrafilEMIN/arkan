---
name: how
description: "Use for \"how does X work\", code walkthroughs before changing something, and placement / ownership / layering questions (\"where should this live\", \"which package owns this\", \"is this the right layer\"). Explains subsystem architecture, runtime flow, onboarding mental models. Use why for motivation."
---

# How

Explore the codebase to answer "how does X work?". Produce the explanation a senior engineer would give someone joining the subsystem: enough to build a working mental model, not so much that it reads like annotated source.

`architect`, `teach`, `no-comments` and `blast-radius` call this skill. It reads; it never edits.

**Subagents.** Every spawn is read-only, in a fresh context. Explorers suit a fast model; the explainer suits your strongest one, where the harness lets you pick. Where it does not, use the current model and carry on.

## 1. Assess complexity

If the scope is ambiguous, state your reading and explore; the person can redirect.

- **Simple** (one module, a small utility, a narrow question like "how does function X work"): no explorers. Spawn one explainer that explores and explains in one pass, built from [`references/explainer-prompt.md`](references/explainer-prompt.md) without the explorer-findings section. Go to step 4.
- **Complex** (a subsystem across several files or services, a cross-cutting feature, a full architecture overview): go to step 2.

When in doubt, take the simple path.

## 2. Explore (complex only)

Split the question into 2 to 4 angles, each a distinct slice of the subsystem. Spawn all explorers at once, each with [`references/explorer-prompt.md`](references/explorer-prompt.md) and its angle filled in. Give them the repo's `GLOSSARY.md` and the relevant adrs in `docs/adr/`, so they use the repo's own words.

## 3. Synthesize (complex only)

When every explorer has returned, spawn one explainer with `references/explainer-prompt.md` and all the explorers' findings filled in.

## 4. Present

Present the explainer's output. Light edits for clarity, or context from the conversation, are fine. Do not rewrite it substantially.

## Output format

The sections defined in `references/explainer-prompt.md`, dropping any that do not apply: Overview, Key Concepts, How It Works, Where Things Live, Gotchas.
