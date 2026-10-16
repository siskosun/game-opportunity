# Cheapest decisive validation

Choose a test because it can change a real development decision, not because it yields convenient positive numbers. Time/cost estimates are planning assumptions, not promises.

| Uncertainty | First practical test | Evidence it cannot prove |
|---|---|---|
| Is the problem recognized or understood? | Transparent concept walkthrough, qualitative interviews | Future retention/revenue |
| Will the audience voluntarily express interest? | Landing-page interest or ethically conducted recruitment | Real sustained play |
| Does the mechanic produce the intended behavior? | One graybox H5 PROBE or minimal Godot kernel | Broad market reach |
| Does the intended experience work? | Real uncoached playtest, observed inputs and failures | Population-level enjoyment |
| Is the player outcome delivered? | For repeatable games, actual voluntary return or invitation; for one-shot games, completion, recommendation or willingness to pay | Incremental causal impact without appropriate comparison |
| Is acquisition plausible? | Small human-approved channel test with matched denominators | Long-term unit economics from click-through alone |

For each recommendation state:
1. Decision the user could change after seeing this evidence.
2. What is actually measured, from whom, over what duration and with which denominators.
3. Operational effort/cost, rights/permissions, and cheaper credible alternatives.
4. Continue, adjust, and stop conditions; avoid arbitrary numeric pass thresholds without a rationale.
5. Failure modes: selection, demand effects, placebo, technical defects, recruitment bias, low signal, and ambiguous results.

When important uncertainty is not cheaply falsifiable, say so and select a stronger appropriate test or stop. Do not build a full product simply to avoid difficult evidence; do not remain in concept testing once only real play can discriminate alternatives.

For an original mechanic, make a small observation of player-experience difference the first goal, without requiring demand documentation as a prior gate.

For several conceptual variants, propose a short list and one decisive discriminating test. Do not silently generate multiple game-exp experiments, independent H5 PROBE histories, or multiple repos.

## Match the next test and recheck point to the signal

For `player_need`, distinguish spontaneous language from **voluntary choice** in the population who made the request. For `played_prototype`, identify the stage the available proof lacks (longer-session usability, next-session return, paid choice or broader audience); never equate a jam rating with a market result. For `supply_gap`, independently examine **demand, alternatives, reach and economics** rather than scoring low supply alone. For `breakout`, test the acquisition path and paid-versus-organic alternative before assuming the game mechanic caused growth. For `platform_change`, confirm official applicability and the actual cost/access change before testing whether players value it.

Choose **one** discriminating uncertainty and one next test even when a candidate has multiple labels. Prefer recruiting where the original claim was observed *if authorized and sufficiently representative*, but also test a contrasting audience when overlap or selection bias threatens the decision. A concept click, public ranking, wishlist or interested comment never by itself proves conversion, continued play or profitable acquisition.

When a signal depends on timing, write a review trigger (dated event or conditional observation), an estimate of the effort **with assumptions**, and what happens if the window closes before a meaningful result. Do not auto-close a card when a generic time-to-live expires. Original/new hypotheses and evidence revisions must remain traceable; actual human Review and game-exp project lifecycle stay separate.

## Prospective decision-value check (maintainer, not a product score)

Use `evals/p0c-case-template.md` for **3–5 actual opportunities**, recording *before* each: what the developer would have done without this triage; how much time or money that choice would require; and what result would disconfirm it. Record the actual next action, time to decision-relevant evidence, costs, misses (including promising ideas prematurely screened out), audience overlap and eventual decision. A different recommendation or faster research alone does not prove improved outcomes, and five uncontrolled cases cannot establish a causal effect. Mark unrun cases `NOT_RUN` and contradictions explicitly; do not announce behavioral "PASS" based on static eval fixtures.

## Players have more choices than attention

Separate **noticed -> voluntarily chosen -> outcome delivered** rather than using one funnel metric as proof of another. Consult `references/player-choice.md` when a proposed game competes with many similar products or its core mechanic can be copied quickly. For a narrative buy-to-play game, value completion and recommendation rather than default D7 retention. If a copycat scenario is central, explicitly test which player-visible advantage survives, or whether a time-bounded novelty launch is itself the intended model.
