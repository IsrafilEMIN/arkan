# Source playbooks

The why skill spawns one investigator per available evidence category, each reading a single playbook.

| Category | Playbook |
|---|---|
| Source control history | [`code-archaeology.md`](./sources/code-archaeology.md) (git, `gh`) |
| The repo's local markdown tracker | [`code-archaeology.md`](./sources/code-archaeology.md) (`grep` under `.scratch/`) |
| Any other category, through a connector | the connector search steps below |

## Connector search steps

Use these for an issue tracker, long-form documents, team chat, infrastructure observability, error tracking or an analytics warehouse reached through a connector (mcp server).

1. **Orient.** Read the connector's instructions and tool list. Find its search, read and list tools, and the scope it covers (workspace, project, channel, service, dataset).
2. **Search wide.** Query the key symbols, file and module names, feature names, ticket ids and pull request numbers from the code anchor. Bound by time: the weeks around the commits that added or changed the target.
3. **Read whole items.** Open each hit in full: the ticket with its comments and sub-issues, the doc with its history, the thread with its replies, the monitor or error with its timeline.
4. **Follow links inside the source.** Parent and sibling tickets, linked docs, the incident a monitor fired for. Record links to other sources as leads.
5. **Cite precisely.** A permalink, ticket id, doc url, monitor or issue id, or query text, with author and date.

Cross-cutting:

- [`incident-postmortem.md`](./sources/incident-postmortem.md). Add this if the target code looks defensive (null checks, retry, timeout, rate limit, feature flag, egress guard, OOM handler).

## Read the evidence

These rules hold for every source.

- **Access failure is a gap.** If a connector fails to authenticate, or an item is private, stop and report that source as unsearchable. Never guess what it held.
- **No data in the window is a gap, not a null result.** Retention limits, deleted or renamed metrics, and tables created after the change all return nothing. Name the gap so the synthesizer does not read "no results" as "no activity".
- **Timing is suggestive, not proof.** A spike before a pull request and stabilization after is suggestive, not definitive. Other changes may have landed in the same window. Check the neighbouring pull requests.
- **Instrumented is not caused.** A metric, event or monitor shows that someone cared enough to measure a thing. It does not show the code exists because of it. Pair it with a pull request or commit citation before you claim causation.
- **A threshold is often the answer.** For "why is this clamped at N?", compare the code constant with monitor thresholds and with the p99 of the measured value in the weeks before the change. A match suggests the number came from data.
- **Check the timing against the ship date.** For an error or a usage signal, record first seen, last seen and the affected releases. Say whether the signal stops, starts or steps at the target's ship date.
- **Specs go stale.** Specs are often written before implementation and not updated. Check the doc's dates against the ship date, flag where the spec and the code differ, and read a ticket's full history for scope changes.
- **Boilerplate and banter are not evidence.** A generic "why" ("improve user experience") is not an answer. A casual chat message is not a decision. Look for specific, considered wording.
- **Confirm a table exists before you report from it.** Schemas differ per company. Probe the schema first.
- **A tool's AI analysis is inference.** Treat a connector's generated root-cause analysis as a hypothesis. The events and stack traces are the evidence.
