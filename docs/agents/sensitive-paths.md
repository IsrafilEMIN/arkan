# Sensitive paths

A pull request that touches one of these paths always needs the person's review (`docs/agents/approvals.md`). Codeowners and the agent guard read the same list. One glob per line in the block below; `#` starts a comment.

```text
.github/workflows/**
.github/CODEOWNERS
docs/agents/sensitive-paths.md
docs/agents/approvals.md
REVIEW.md
AGENTS.md
CLAUDE.md
# arkan's own merge path and its checks
ci/**
scripts/check.sh
scripts/check-seam.sh
docs/seam.md
# what pre-setup installs in other repos
skills/pre-setup/scripts/**
skills/pre-setup/references/**
```
