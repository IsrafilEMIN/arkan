# Lessons

A **lesson** teaches a knowledge leaf. In the default form, it is one self-contained HTML file that teaches one tightly-scoped thing, then checks it with a recall quiz. The quiz score is the output KPI. If the leaf is a few facts, teach it in the chat with a short recall quiz, and skip the file.

## The lesson

- Save it to `lessons/NNNN-<dash-case-name>.html`. Scan `lessons/` for the highest number and add one.
- Keep it short and completable in one sitting: working memory is small. Give the user one tangible win that a behavior leaf builds on.
- Teach only the knowledge the leaf needs, tied to the target behavior in `PLAN.md`.
- Back every claim with a citation link from `Sources`. Recommend one primary source to read or watch: the best one you found for this leaf.
- End with a recall quiz that gives feedback at once, ideally automatic. Make every answer option the same number of words, and the same length where possible, so the format gives no clue.
- Link to related lessons and reference documents with HTML anchors.
- Remind the user to ask the agent follow-up questions.
- Make it beautiful: clean typography and layout, in the spirit of Tufte. The user returns to it to review.
- Open the file for the user (`open <file>` on macOS).
- Add a row to `Lessons` in `PLAN.md`, with the quiz score when the user reports it.

## Assets

Build lessons from reusable **components** in `assets/`: stylesheets, quiz widgets, simulators, diagram helpers.

- Before a lesson, read `assets/` and build from what is there.
- The first component is a shared stylesheet that every lesson links, so the lessons read as one course.
- When a lesson needs something a second lesson could reuse, write it as a component in `assets/` and link to it.

## Reference documents

A reference document is the compressed essence of one or more lessons, made for quick lookup: syntax and snippets, algorithms and flowcharts, poses and sequences, routines. Users rarely reread lessons, but they return to reference documents. Save them to `reference/*.html`, designed to print well.

A **glossary** (`reference/glossary.html`) is the canonical language of the plan. Once it exists, every lesson, quiz and plan row uses its terms.

- Add a term only when the user can use it correctly. Writing a tight definition is itself evidence of learning.
- Pick one word per concept, and list the others as aliases to avoid.
- Keep each definition to one or two sentences: what the term IS.
- Use the glossary's own terms inside other definitions.
- If the wider field uses a term loosely, write how this plan uses it.
- Revise a definition in place when understanding deepens.
