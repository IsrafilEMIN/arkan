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
