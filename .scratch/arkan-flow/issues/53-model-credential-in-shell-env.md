# 53: The model keeps its key in the shell environment

**Role:** ready-for-human
**Closed:** no
**Priority:** 62

**What to build:** every workflow that runs the agent headless passes its model credential to the harness process, and the harness's shell tool inherits the process environment. With network access, content that reaches the prompt can exfiltrate the credential. Ticket 21 confines the write token and the file system; this exposure stays.

- [ ] the model process holds no long-lived credential that its shell can read
- [ ] a run with planted prompt-injection content cannot read or send the credential
- [ ] proof: a probe in the prompt tries to print the credential and reaches nothing

**Blocked by:** None for a choice. the build needs a runtime control: a scoped proxy, a short-lived per-run credential, or a harness that scrubs its environment.

## Comments

- 2026-10-19, filed from ticket 21 review rounds 2 and 3 (`ci/github/arkan-post-merge.yml:147,177`), the same shape as the review job. `claude-code-action` exports its token to the cli, so a workflow edit cannot close it. The owner picks the runtime control.
