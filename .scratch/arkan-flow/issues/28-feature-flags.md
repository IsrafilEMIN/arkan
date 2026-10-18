# 28: feature flags in the flow

**Role:** needs-info
**Closed:** no
**Priority:** 19

**What to build:** small slices can merge before a feature is done, behind a flag that is off, so branches stay short. `to-tickets` marks a slice users would see half-built as "behind flag `<name>`" and adds a "remove flag `<name>`" ticket for each new flag. the feature playbook uses the repo's flag mechanism, or a plain config or env switch when it has none. `pre-setup` records how the repo does flags.

**Blocked by:** None (can start immediately). needs the owner's go on the shape.

- [ ] `to-tickets`, the feature playbook and `pre-setup` carry the rules above
- [ ] proof: a spec with a user-facing feature split in three gives flagged slices and one remove-flag ticket
