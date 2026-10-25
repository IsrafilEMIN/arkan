# 60: one copy of each workflow arkan installs

**Role:** ready-for-agent
**Closed:** no
**Priority:** 69
**Blocked by:** 59

**What to build:** `check.yml`, `arkan-review.yml` and `arkan-risk.yml` exist twice, in `ci/github/` and in `.github/workflows/`, byte for byte. keep the copy github runs, `.github/workflows/`, and delete the three from `ci/github/`. `ci/github/` keeps only the templates arkan does not run: `arkan-merge.yml` and `arkan-post-merge.yml`.

- [ ] `skills/pre-setup/scripts/setup.sh` copies `ci-check`, `ci-review` and `ci-risk` from `<arkan>/.github/workflows/`, and still from `ci/github/` for `ci-merge` and `ci-post-merge`. this works from a checkout and from the claude plugin cache (check that the cache holds `.github/workflows/`)
- [ ] `ci/review-eval.sh`, `scripts/check-seam.sh`, `ci/README.md`, `README.md`, `AGENTS.md`, `REVIEW.md`, `docs/agents/approvals.md`, `docs/agents/review-evals/README.md`, `skills/post-merge/SKILL.md`, `eval/scenarios/README.md` and `eval/scenarios/build.sh` name the remaining path
- [ ] `docs/seam.md` row 6 names the new path. if underground's `docs/adr/0002-repo-seam.md` names the old path, file the matching underground change in the same change
- [ ] in a temporary repo, `setup.sh apply ci-review` writes a workflow equal to arkan's plus the `# arkan-copy:` stamp, and `setup.sh check` reads `ok`
- [ ] `bash scripts/check.sh` prints `check: ok`

## Comments

- 2026-10-21, owner: agreed (simplify the setup without losing a capability).
