---
name: halal-check
description: Give a halal verdict, with evidence, for a food or supplement product.
disable-model-invocation: true
---

# Halal check

Give a verdict per item, with the evidence that decides it. The user acts on these verdicts with money.

Use the Hanafi position as the default, and name other schools where they differ.

Verdicts: halal / doubtful / not halal.

## Food and supplements

1. Check for a halal certification. If one exists, name the certifier and link the proof.
2. If no certification exists, infer the verdict from the composition, and label it "inferred, not certified".
3. Read the full ingredient list from the product page, including "other ingredients" and any capsule or coating. Never infer from the product name.
4. Show the ingredient list with the source page and date.
5. For each ingredient that comes from an animal or alcohol, or whose source is not stated (e.g. gelatin, glycerin, carmine, L-cysteine, enzymes), give its source and the ruling, with proof.
6. For a doubtful source, give the manufacturer's contact route so the user can ask.

## Output

One row per item: verdict, certified or inferred, deciding evidence, source link and date, and a replacement if the item fails.

Close with "confirm with a qualified scholar".
