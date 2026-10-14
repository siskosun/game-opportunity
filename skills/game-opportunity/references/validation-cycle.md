# Validation cycle v1: preregister -> observe -> assess -> decide

This protocol applies when the developer is ready to evaluate *actual player behavior*, not for every opportunity brainstorm. It is independent of game-exp's protected Manifest, Evaluation Profile, Candidate, trusted evaluation and human Review.

## 1. Before the real test: lock a single decisive question

Use `scripts/validation_cycle.py plan --help` to construct **one** local JSON plan from a completed opportunity card. Record:

- A specific unique-player action metric and its **custom numerator/denominator definitions** (not AI-guessed success rates).
- Target population and segment; start/end dates; recruitment/sampling method and actual limitations.
- Minimum number of eligible unique players, a lower **stop signal**, a strictly higher **continue signal**, and a reason grounded in the next investment decision.
- The resulting SHA-256 digest **before observing any outcomes**. Save that digest with an actual, independent pre-test timestamp in authorized private storage if proving timing matters. A local file timestamp or operator-supplied SHA alone **cannot prove preregistration happened before the test**.

Supported metrics: `qualified_interest` (attention), `voluntary_start` and `actual_purchase` (choice), `first_session_completion`, `voluntary_return`, `voluntary_invitation`, and `finite_game_completion` (experience). Count **unique eligible players**, never mixed impressions, raw taps, sessions or invitation events. When a platform supplies only page views/sessions rather than distinct eligible players, use a separate qualitative note or a different authorized measurement; do not rename page views as players.

Plans belong in local or independently authorized *private* research storage. The public source repository is never the default destination. Do not send identifying logs, minors' data, credentials or sensitive product data into a public Skill or GitHub repository.

## 2. Actually obtain observed evidence

With consent and necessary platform permissions, the operator conducts a real test or legitimately accesses authorized aggregated analytics. A concept survey can support expressed interest, not actual replay. A H5/Godot machine test can establish mechanics, not human preference. A small recruited sample cannot establish population-level demand or a causal lift over the market.

Export a single UTF-8 CSV or JSON **aggregate** record containing only these fields, in English or Chinese (use the aliases listed in the example):

`plan_id, metric, numerator, denominator, population, segment, window_start, window_end, unit, sampling_method, source_kind`

`unit` must equal `unique_players`. `source_kind` is `playtest`, `platform_dashboard`, `manual_aggregate`, or `other`. Keep raw logs and access-controlled source files separate. The script rejects extra columns (including raw review text, player IDs or phone numbers) and will not concatenate conflicting cohorts, time windows, source snapshots or variants. If several independent arms/snapshots exist, **create separate, preregistered plans and assessments**; do not sum or average by default.

## 3. Assess observations without granting authority

Run `scripts/validation_cycle.py assess` with the preserved `--expected-plan-sha256`. It checks the exact plan file bytes, denominator, source, metric, population, segment, window and sampling method. It can produce:

| Signal | Meaning |
|---|---|
| `MEETS_DECLARED_CONTINUE_SIGNAL_NOT_A_DECISION` | Observed rate reaches the declared continue bound with sufficient declared denominator and matching plan hash |
| `MEETS_DECLARED_STOP_SIGNAL_NOT_A_DECISION` | Observed rate meets the declared stop bound under the same conditions |
| `INCONCLUSIVE_BETWEEN_PREDECLARED_BOUNDS` | Sample meets minimum, but outcome lies between bounds |
| `INCONCLUSIVE_BELOW_PREDECLARED_MINIMUM` | Insufficient eligible-player denominator |
| `DESCRIPTIVE_ONLY_NO_PRETEST_DIGEST` | A pretest digest was not provided; **no threshold decision signal** |

The output explicitly says that both plan and aggregate are ordinary, operator-reported research. Hash matching proves byte identity, **not** pretest timing or data truth. The code does not calculate population confidence, causal lift, ROI, commercial profitability, or a game-exp decision. An actual player quote or aggregate from the wrong target audience is not corrected by sample size.

## 4. Link, reflect, choose

For an actually observed result, use existing `scripts/link_result.py` to append a dated observation, analysis pointer/digest, limitations and actual H5 PROBE / game-exp EXP / Candidate identities **only when genuinely known**. Do not silently edit the earlier plan or hypothesis; create a new plan ID for changed metrics, conditions or cohorts.

If the result motivates a playable, use `scripts/handoff_bundle.py` and the existing game-exp `game_exp_experiment_template` / Bind workflow; do not add fields to the protected Manifest. If a bound Candidate has been tested, game-exp human Review/PROMISING/SELECTED/REJECTED remains explicit and independent. A market 'stop' **never** submits game-exp `REJECTED` and does not create a fake FAIL Review. Do not leak local research evidence into a public game-exp project or public repository.

## Complete synthetic-only example (repo root)

The repository contains `examples/synthetic-behavior-aggregate.csv`, wholly invented for teaching the data contract. To try it, first use the existing card tool to create and complete `OPP-20261014-buddy-play` (do **not** use an unfinished card), then:

```powershell
python skills/game-opportunity/scripts/validation_cycle.py plan --card opportunities/OPP-20261014-buddy-play.md --plan-id VAL-20261014-invitation-v1 --metric voluntary_invitation --numerator-definition "Unique eligible players voluntarily sending an invite" --denominator-definition "Unique players actually offered an invite action" --population "China adult cooperative players" --segment "first-time-invitation" --window-start 2026-10-14 --window-end 2026-10-21 --sampling-method convenience --sampling-notes "Synthetic opt-in sample; not representative" --min-denominator 30 --continue-at-least 0.30 --stop-at-most 0.10 --threshold-reason "Only a strong voluntary invite signal justifies building a multiplayer slice"
```

Copy the **actual SHA** printed by this command and, after a real test, use:

```powershell
python skills/game-opportunity/scripts/validation_cycle.py assess --plan local-evidence/VAL-20261014-invitation-v1.plan.json --input examples/synthetic-behavior-aggregate.csv --expected-plan-sha256 <actual-sha-from-plan>
```

The second command with the synthetic CSV is for **tool smoke testing only**; it is not real playtest evidence. The CLI never uploads, recruits, advertises, calls the game-exp MCP or applies an experiment outcome.
