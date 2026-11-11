# building effective agent automations

- link: <https://claude.dev/blog/building-effective-agent-automations/>
- authors: lance martin, cj avilla
- published: 2026-10-08

## core claim

a scheduled agent fails quietly: it loses a source or forgets a preference, and nobody notices. six rules prevent that: read from a bookmark, report a failed read, re-check before posting, confirm a post before recording it, re-read preferences each run, and give least access with a spend cap.

## what arkan owns

arkan owns how its skills read sources and report state. the scheduled agent itself is not arkan's.

| item | status | where |
|---|---|---|
| a source you cannot read is reported as unread, never as a quiet day | removed 2026-11-11: skill removed in the pstack-only cleanup | - |
| the same rule for the shared record | done before | `recall` step 4 |
| re-check the live state of each item just before you report it | done before | `recall` this-chat scope and step 5 |
| count an action as done only after you read it back | done before | `arkan-mode/playbooks/shipping.md` |

## what arkan leaves to others

- `underground` or the harness: vaults and scoped credentials, read-only tokens, network allowlists, spend caps per run, cron schedules, memory stores, bookmarks and ledgers for a scheduled agent.
- the person: preferences that the agent reads but cannot edit.
