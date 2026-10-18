---
name: deal-hunt
description: Find live listings for a product at the best landed price, with seller trust and fit for the user's need.
---

# Deal hunt

The deliverable is a ranked table of listings the user can buy today. A list of places to look is not a result.

## Before searching

1. Pin the actual need: what problem the product solves, and if a different or cheaper product solves it better.
2. Pin the exact item: model, variant, size or capacity, and condition (new, used, refurbished).
3. Pin compatibility: what the item must work with, fit into, or connect to.
4. Pin the constraints: budget, financing, delivery or local pickup, deadline.
5. Check the community: reviews, forums, and subreddits for the recommended pick, variants to avoid, and fair used prices. Link the sources.

Ask the user only for what the conversation does not already state.

## Searching

- The user is in Ontario, Canada (GTA). Search Canadian sellers first, then foreign sellers that ship to Canada. Add the stores and marketplaces that fit the product category, and any the user names.
- Open each listing. Confirm it is live, in stock, and ships to Canada or is local pickup in the GTA.
- If a page needs a login or blocks the fetch, say so and give the exact query the user can run.
- Never invent a price, stock status, or spec. If a listing does not state a spec, write "not stated".

## Landed price

Item price + shipping + tax (13% HST) + duties or brokerage if imported, in CAD at today's rate. State the date of the check.

## Trust

Seller feedback score and count, return window, listing age, photos of the actual item, and red flags: stock photos only, price far below market, new account.

## Output

| # | listing (link) | condition | landed CAD | ships / pickup | seller trust | community note | fit |

Rank by the user's priority: price, trust, or value. Then give one recommendation and the one risk to check before buying.

If the user asks for a different approach, answer that question. Do not optimize the current pick by a few dollars.
