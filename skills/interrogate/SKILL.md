---
name: interrogate
description: "Several reviewers on different models challenge a change from independent angles; you judge their findings. Use for \"interrogate\", \"adversarial review\", \"multi-model review\", \"challenge this\", \"stress test this code\", \"find blind spots\", or \"tear this apart\"."
---

# Interrogate

Spawn one reviewer per model to review a change adversarially. The adversarial signal comes from model diversity, not from assigned personas. The deliverable is a judged verdict. Do not apply changes on your own.

It goes further than `code-review` (one reviewer, the repo's tags and rounds). Use it for a contested design, a change on a sensitive path (auth, billing, installers, release workflows, agent instruction files), or when the person asks; arkan-mode reaches for it on a contested design before shipping.

## Step 1, scope

Find what to review:

- the files or diff the person points at;
- on a work branch, `git diff <base>...HEAD` for the whole change;
- the recent work the person's message refers to.

Package the diff or file contents with the surrounding files a reviewer needs to understand the code.

## Step 2, intent

Before spawning reviewers, state the intent in one paragraph, from the person's message, the commit messages, the pull request body and the code. If you are unsure of the intent, ask the person first.

## Step 3, spawn reviewers

Launch all reviewers at once, read-only, in fresh contexts, labeled Reviewer A, B, and so on. Two is the minimum.

**Models.** Where the harness lets you pick a model per subagent, give each reviewer a different model family (diversity is the point). Where it does not, run every reviewer on the current model in its own fresh context, and say so in the report: the agreement signal is then weaker. If the harness refuses a model, run that seat on the closest model it accepts and say so; never block the review on it.

Fill [`references/reviewer-prompt.md`](references/reviewer-prompt.md) the same way for every reviewer, with the stated intent, the diff or file contents, the rubric from [`references/rubric.md`](references/rubric.md), and the code-quality lens from [`references/code-quality-review.md`](references/code-quality-review.md). Add the repo's `REVIEW.md` and `CODING_STANDARDS.md` when they exist.

## Step 4, synthesize

As results come back, build one picture. Parse every reviewer's findings. Merge findings that describe the same issue in different words, and note which models raised each. Findings two or more models raised on their own are the strongest signal. Read a lone model's finding, but weight it accordingly. Note disagreements: one model flagging something and another saying the opposite is context for the verdict.

## Step 5, lead judgment

You are the lead reviewer, a pragmatic senior engineer, not a neutral aggregator. Read [`references/lead-judgment.md`](references/lead-judgment.md). Put every finding in one of four buckets, with the model(s) that raised it and a one-line reason:

- **Act on.** Real issues of correctness, security or maintainability, given the actual goals. They would block a real pull request.
- **Consider.** Legitimate, but you are not sure they outweigh the cost of fixing them now. Worth the person's attention.
- **Noted.** Technically valid but not actionable: context-dependent, premature, or low impact for now.
- **Dismissed.** Wrong, nitpicky, or missing context, with a short reason.

An **act on** finding in a pre-existing part of the code becomes a ticket on the repo's tracker, not a change in this pull request.

## Output format

### Intent
> [the intent paragraph from step 2]

### Reviewers
- Reviewer [label]: [model], [N findings] (one line each; say "same model, fresh context" where models could not differ)

### Act on
[each: description, which models raised it, why it matters]

### Consider
[each: description, which models raised it, the tradeoff]

### Noted
[a short list]

### Dismissed
[each with a short reason]

### Agreement map
[where models agreed and where they diverged, and what that pattern says]
