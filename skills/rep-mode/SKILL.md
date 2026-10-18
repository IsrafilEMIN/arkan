---
name: rep-mode
description: Learn a skill or topic over many sessions through measured reps, with short lessons for the knowledge each rep needs.
disable-model-invocation: true
---

# Rep mode

Learning = the same input produces a new behavior.
Example: before, a chess player sees a hanging piece and keeps their plan. After, the same position makes them take the piece.
A **rep** is one attempt at a behavior leaf that the user does and someone can score. Every step below produces observable, measurable behavior. Give steps and measures, never motivation.

The user needs three things, and each has its own tool:

- **Knowledge**: facts from high-trust sources, taught by a **lesson**. Here difficulty is the enemy: it uses the working memory that understanding needs.
- **Skill**: behavior built by reps. Here difficulty is the tool: effortful practice and recall build long-term retention.
- **Wisdom**: contact with real practitioners, found in a **community**.

Aim for **storage strength** (long-term retention), not **fluency** (in-the-moment recall that feels like mastery). Build it with retrieval practice (recall from memory), spacing (practice spread over time) and interleaving (related behavior leaves mixed in one batch).

Treat every performer, including the user, as input → output. Do not model internal states (psychology, "feel", instinct). Copy inputs that correlate with good outputs.

## Plan location

- Default: `~/learning/<skill-slug>/`. Use another location only if the user names one.
- The folder holds `PLAN.md` (format: [PLAN-FORMAT.md](PLAN-FORMAT.md)), and, once needed, `batches/`, `lessons/`, `reference/` and `assets/`.

## Session start

If a plan for this skill exists:

1. Read `Context`, `Learned`, `Notes`, `Reps` and the iteration log.
2. Run the reviews that are due: a leaf or lesson with no practice for 1, 3, 7, then 21 days gets a few reps or quiz items.
3. Continue at the step for the current leaf.

If no plan exists, start at Step 0.

## Step 0: Collect context

Ask these in one message. Skip any the user already answered.
- Why do you want this skill? What changes when you have it?
- What is your current level? What have you already tried?
- Do you have past outputs or data (past work, results, numbers)?
- How much time per week can you practice?
- Any constraints (budget, tools, deadline)?
- What is out of scope for now?

The "why" grounds every later choice. If it stays abstract ("to understand X"), interview the user until it names a concrete outcome ("ship a Rust CLI to my team"). Write the answers to `Context`.

## Step 1: Define the target behavior

- State the skill and the context (the input that triggers it).
- State the current behavior and the target behavior in observable terms.
- If the target is still vague after Step 0, ask one question to make it concrete.

## Step 2: Deconstruct the skill

- Break the skill into sub-skills, then each sub-skill into actionable items.
- Stop when every leaf is a thing the user can practice in one session.
- Tag each leaf `knowledge` (the user must understand it before reps on other leaves can work) or `behavior` (the user gets it by doing).
- Output as a tree (max 3 levels).

## Step 3: Define success from the top 10%

- Identify what top performers DO: their inputs (actions, volume, structure) and their outputs (results).
- Contrast with the bottom 90%: what differs in behavior.
- Only observable behavior. No traits, mindset, or talent claims.
- Find real examples (top performers' actual outputs, interviews, breakdowns) instead of your own memory, and record each in `Sources` with what to use it for.
- Keep `Sources` high-trust: primary sources, recognised experts, peer-reviewed work, strongly moderated communities. Remove a source that turned out wrong, shallow or off-target.
- If no good source exists for an area the plan needs, write it to `Gaps`.
- If you cannot find a source for a claim, mark it `unverified`. Replace unverified claims when the user's own data or a source confirms or refutes them.
- Find 1–3 high-reputation communities (forum, subreddit, class, local group) where the user can test the skill for real. Write them to `Communities`. If the user opts out, write that to `Notes` and stop proposing them.

## Step 4: Pick the leaf

Pick the leaf with the largest gap from the top 10% that the user can still practice at their current level, given `Learned`. The user feels challenged just enough. Pick only in-scope leaves. If a behavior leaf depends on a knowledge leaf the user lacks, pick the knowledge leaf first.

- **Knowledge leaf**: teach it with a lesson and its recall quiz. The quiz score is the output KPI. Read [LESSON.md](LESSON.md).
- **Behavior leaf**: define the rep in Step 5.

## Step 5: Define the rep

A rep optimizes two things together:
- **Input as small as possible:** the least effort and time per rep.
- **Feedback as tight as possible:** the result is visible and scorable soon after the rep.

If the leaf alone produces no observable result, the rep is the smallest complete attempt that contains the leaf (e.g. leaf = wrist snap, rep = one full shot). The leaf stays the thing the user focuses on and changes.

Choose the rep unit yourself, for this skill and this user. A valid rep passes all of these tests:
- **Clear input:** the user knows exactly what they do, and can do it the same way again.
- **Observable output:** each rep leaves a result that someone can see, count, or compare.
- **Tight feedback:** the result arrives soon enough that the user gets many feedback loops in the time from Step 0.
- **Comparable:** after enough reps, the outputs spread so you can separate the best reps from the rest.

If a candidate rep fails a test, change the rep size or pick a different leaf. Add a row to `Reps` with the unit and why it passes.

## Step 6: Measure

- Define 1–3 input KPIs (what the user does, e.g. reps per week).
- Define 1–3 output KPIs (what results, e.g. a score per rep, or a quiz score for a knowledge leaf).
- If the real output KPI is slow (e.g. views after 2 days), also define a fast proxy KPI that scores each rep soon after it (e.g. 5 people say if they keep watching). Check the proxy against the real KPI from time to time, and replace it if they disagree.
- Record a baseline. If no baseline exists, the first batch of reps is the baseline.

## Step 7: Iterate

- Set a rep target (default: 100 reps), in batches of 10 by default.
- Save each batch's reps with their outputs and scores to `batches/<leaf>-<batch>.md`, and link it from the iteration log.
- After each batch, compare the best reps with the rest. Name the behavioral difference. Change one variable for the next batch.
- When a pattern holds across batches, write it to `Findings` as a rule, with the batches that support it. If later data contradicts a finding, mark it `superseded` and write the new rule.
- Mix related behavior leaves in one batch once each one is stable.

## Step 8: Repeat

- When a leaf plateaus, re-run steps 4–7 with the new baseline.
- If the tree no longer fits, re-run steps 2–3 first.

## Record what the user learned

`Learned` steers every later pick, so it holds only evidence. Add a row when:

1. The user shows they can use a non-trivial concept correctly (an answer, an exercise, a rep). Coverage is not learning: wait for evidence.
2. The user states prior knowledge ("I already know X"). Record the depth they claim, so later sessions skip it.
3. A misconception is corrected. These predict stumbling blocks on related leaves.
4. The goal shifts. Confirm with the user first, then update `Context` and add the row.

If a later row contradicts an earlier one, mark the old row `superseded by L<n>`.

## During sessions

- If the user states how they want to learn, write it to `Notes` and follow it.
- If a question needs wisdom (judgment from practice), give your best answer, then point the user to a community from `Communities`.

## Output

Fill in the format from [PLAN-FORMAT.md](PLAN-FORMAT.md) and save it to the plan location.
If the user returns with results, update the iteration log of the existing plan.
