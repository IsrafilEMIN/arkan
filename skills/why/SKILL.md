---
name: why
description: "Use for 'why does X work this way', 'why we picked Y', design rationale, regressions, postmortems, or data-backed thresholds. Searches every evidence source the run can reach (source control, the issue tracker, docs, chat, observability, error tracking, analytics) in parallel, then returns a cited read on decisions and tradeoffs. Use how for runtime behavior."
---

# Why

Investigate the motivation and intent behind code. `how` answers what the code does; `why` answers what forces gave it its shape. `architect`, `teach`, `recall`, `blast-radius` and `no-comments` call it.

**Subagents.** Investigators suit a fast model; the synthesizer suits your strongest one, where the harness lets you pick. Investigators may use the run's connectors (mcp tools) but never write anything.

## Operating posture

Be a careful, cautious and precise investigator. Be honest about what you know versus what you infer. Read [`references/epistemics.md`](references/epistemics.md) for the confidence framework and phrasing; the synthesizer must follow it.

## Step 1. Understand the target and the question

The **target** is usually a chunk of code, a pattern, a feature or a named design decision. The **question** is usually a design rationale, a tradeoff, a motivating edge case, an outside constraint, dead code, or a broad history sweep.

If the target is vague ("why do we do it this way?"), make your best guess from the conversation (open files, recent edits, what was just discussed). State your reading briefly so the person can redirect, then go on.

## Step 2. Establish the code anchor

Before spawning investigators, build the seed context yourself: file paths and line ranges, key symbols, the last commits touching the target, pull request numbers from merge commits (`(#1234)` in the subject, or "Merge pull request #1234"), and linked ticket ids. Run `git blame -L <start>,<end> <file>`, `git log --follow -p -- <file>`, `git log --oneline -20 -- <file>`, and `git log -1 --format=%B <commit>`. Then pull the pull request bodies and discussion for each substantive commit: `gh pr view <n> --json title,body,author,createdAt,mergedAt,labels,closingIssuesReferences,comments,reviews`, or on the broker route `agent-gh pr-status` (arkan-mode's forge). This anchor goes to every investigator and to the synthesizer.

## Step 3. Spawn parallel investigators

**Default to the full parallel investigation.** The goal is a complete coverage map. Document the null; don't skip the search.

### Discovery

List the connectors (mcp servers) this run can call: in claude code, the tools named `mcp__<server>__*`; in other harnesses, their own tool list. Map each to one evidence category:

1. source control history
2. issue / ticket tracker
3. long-form documents
4. real-time team chat
5. infrastructure observability
6. error / exception tracking
7. product analytics warehouse

Source control is always available through `git` (and `gh` or the broker). The repo's own tracker is always available too: read `docs/agents/issue-tracker.md`; for a local markdown tracker, the tickets and their `## Comments` and `## Answer` sections under `.scratch/` are category 2, searchable with `grep`. For the other categories, classify by the connector's name, instructions and tools. If one could fit two categories, pick its main evidence and note the ambiguity in the coverage map.

Spawn one investigator per category that has a source, all at once, each owning exactly one source. Don't ask one agent to cover several.

Each investigator's prompt is [`references/investigator-prompt.md`](references/investigator-prompt.md) filled in, plus:

- the category playbook from `references/sources/<source>.md` for the selected source, adapted from the examples in [`references/source-playbook.md`](references/source-playbook.md) (`code-archaeology.md` for source control and a local tracker);
- `references/sources/incident-postmortem.md` **if the target code looks defensive** (null checks, retry logic, timeouts, rate limits, feature flags, egress guards, out-of-memory handlers);
- the code anchor and the person's original question.

### What each category is best at

1. **Source control** (git history, pull requests, code comments, tests). Always spawn. Best at the rationale captured during review.
2. **Issue tracker** (the repo's tracker; Linear, Jira, GitHub Issues and the like). Best at the product or business forcing function.
3. **Long-form documents** (Notion, Confluence, Google Docs; the repo's `docs/adr/`). Best at long-form design rationale written before the code.
4. **Real-time chat** (Slack, Discord, Teams). Best at deliberation that never reached a doc.
5. **Infrastructure observability** (Datadog, Grafana, Honeycomb). Best at the runtime reality behind timeouts, retries, rate limits and circuit breakers.
6. **Error tracking** (Sentry, Rollbar, Bugsnag). Best at the exceptions that motivated defensive or corrective code.
7. **Analytics warehouse** (Databricks, Snowflake, BigQuery). Best at the product and data reality behind flags, experiments, migrations and magic numbers.

### When to skip an investigator

Only with an explicit, written reason, which goes in the final sources consulted:

- **No source is available for that category** in this run. Call it a gap, not a choice: "real-time chat skipped: no chat connector in this run, so the conversational record was not searchable."
- **The source is provably irrelevant**, not just probably: "error tracking skipped: the target is a build-time script with no runtime path."

If the target is a single trivial commit whose pull request body already holds the whole answer, you may answer inline, but only after confirming every available category search would be redundant. Say so explicitly. This should be rare.

## Step 4. Synthesize

Spawn one synthesizer. It gets: the investigators' findings (null results and justified skips included), the code anchor, the person's question, [`references/epistemics.md`](references/epistemics.md), and [`references/synthesizer-prompt.md`](references/synthesizer-prompt.md).

## Step 5. Present

Present the synthesizer's output. You may lightly edit for clarity or add context from the conversation, but **do not rewrite the confidence language**.

## Output format

The structure in `references/synthesizer-prompt.md`: the question, the code in question, what we found, what we can reasonably infer, competing hypotheses, what we don't know, sources consulted, confidence summary. Adapt as needed, but keep the confidence separation, and keep sources consulted as one line per investigator, including those that returned nothing or were skipped, with the reason.

If the question is a step before changing this code, turn the findings into a **preserve / change / avoid / risk** set for planning the change. A decision with lasting effect that the investigation surfaces, and that no adr records, is worth an adr through `domain-modeling`.

## Common failure modes

- **Recency bias.** Assuming the latest commit is authoritative. The current shape is often many earlier decisions piled up. Trace back.
