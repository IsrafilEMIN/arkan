# 56: on the direct route, an agent verdict is a comment, not a review

**Role:** ready-for-agent
**Closed:** no
**Priority:** 65
**Blocked by:** None (can start immediately).

**What to build:** on the direct route, the verifier posts `PASS` as a pull request review with the person's own `gh` token (`skills/arkan-mode/playbooks/shipping.md:5`, `skills/arkan-mode/playbooks/opening-a-pr.md:34`). only the broker adds `<!-- arkan:verifier -->`, so that review has no mark. a repo's `arkan-merge` gate counts an unmarked `PASS` as the person's (`ci/github/arkan-merge.yml:92-97`), so an agent verdict can merge a `manual` pr. no session posts a review whose body starts with `PASS` outside the broker. on the direct route the verifier posts its verdict as a plain pr comment, which neither merge path reads, and the person posts the `PASS` review.

- [ ] `shipping.md` step 1 and step 4, `opening-a-pr.md` (the review call under **Forge without GraphQL**) and the forge section of `skills/arkan-mode/SKILL.md` say: on the direct route the verdict is a pr comment (`issues/<n>/comments`), never a review; only the broker posts an agent's verdict as a review
- [ ] they say what the person does on the direct route: read the comment, then post their own `PASS` review on the head
- [ ] they say the cost: without the broker, an `auto` pr does not merge on an agent verdict alone
- [ ] `docs/seam.md` row 6 is unchanged: the rule is the same; only who may post a review changes
- [ ] `bash scripts/check.sh` prints `check: ok`

## Comments

- 2026-10-21, owner: agreed. source: the full review, finding A1.
