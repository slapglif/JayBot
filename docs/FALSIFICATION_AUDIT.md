# JayBot Falsification Audit

## Verdict

**Falsification readiness score: 33/100.**

A score of 100 means the strategy is supported strongly enough to deploy with real capital today under predefined risk limits. At 33, the frozen rule is a **promising synthetic research signal, not a market-ready options strategy**.

We cannot prove that a strategy is free of overfitting or bias. We can only expose it to attempts to falsify it. The rule survived several useful tests on underlying OHLC, but it failed the tests most closely connected to real option pricing and regime portability.

## Frozen hypothesis audited

No parameter was changed to rescue a failed result:

- fixed $500 premium per weekly ETF entry;
- 10% OTM call;
- 84 calendar DTE;
- +500% TP (6× option value);
- if still open at day 21 and down at least 50%, pause that ETF for six weeks;
- integer contracts;
- Black–Scholes over adjusted ETF OHLC with entry-date 20-session realized volatility clipped to 25%–175% and 3% risk-free rate.

## What survived falsification

### Cross-sectional and temporal transfer

The frozen rule was tested on an unseen broad/sector 2× ETF universe that was not used to select the crash-grid winner: SSO, QLD, USD, ROM, UCC, UYG, DDM, MVV, RXL, DIG.

| Sample | Modeled profit | Cumulative premium | Profit/premium | Positive symbols |
|---|---:|---:|---:|---:|
| Current requested ETFs, mature entries only, 2023–2026 | $150,811 | $188,022 | 80.21% | 9/10 |
| Unseen 2× ETFs, 2023–2026 | $148,171 | $318,546 | 46.51% | 8/10 |
| Unseen 2× ETFs, pre-development 2010–2023 | $420,375 | $1,731,296 | 24.28% | 6/10 |

The shared fixed-$500 schedule remained cash-feasible in the unseen runs: minimum cash $62,867 recently and $44,812 in 2010–2023.

### Entry timing was not a single-weekday accident

All five weekly entry-day perturbations remained positive on the unseen recent universe, with profit/premium from 27.50% to 48.86%.

### Nearby parameters formed a plateau

All 27 nearby combinations were positive on the unseen recent universe:

- strike 7.5%, 10%, 12.5%;
- DTE 56, 84, 112;
- TP +300%, +500%, +700%.

The frozen 10%/84/+500% cell ranked 13th of 27, which is healthier than an isolated optimum. It does not erase the earlier 300-cell selection problem.

### Conservative daily target marking survived

Replacing intraday-high target detection with daily-close-only detection remained positive: +$129,773 / 40.74% of cumulative premium.

### Large spread stress alone survived

A deliberately large 5% markup at entry, 5% haircut at exit, and $1 per contract each side remained positive: +$119,921 / 40.54% of premium.

## What failed falsification

### Entry implied-volatility realism failed

Increasing entry volatility 25% above realized-volatility input changed the unseen recent result from +$148,171 to **−$4,065**. The combined adverse case—close-only targets, 25% IV markup, 20% post-entry IV compression, 5% spread each side, and commissions—lost **$10,728**.

This is the most important failure. Leveraged-ETF calls commonly embed implied volatility and volatility risk premium that a realized-volatility Black–Scholes estimate does not reproduce. The strategy is not robust to a modestly more expensive option premium.

### Leave-one-crash-regime-out failed 0/3

Selecting parameters on two crashes and evaluating on the omitted crash lost money every time:

- train on GFC+COVID → 12.5%/84/+500%; held-out dot-com: **−$25,787**;
- train on dot-com+COVID → 17.5%/112/+500%; held-out GFC: **−$9,221**;
- train on dot-com+GFC → 12.5%/28/+250%; held-out COVID: **−$4,579**.

No one of the 300 original parameter combinations was positive in all three crashes.

### Time-series certainty was insufficient

On the continuous unseen 2010–2023 run:

- 9 of 14 entry years were positive;
- 5 were negative;
- best year: +$187,528;
- worst year: −$101,798;
- the best year contributed 44.6% of total profit;
- block-level bootstrap probability of positive mean: 92.1%;
- 95% bootstrap interval for mean annual profit: **−$11,205 to +$72,371**.

Because the interval crosses zero, the available independent-year evidence does not establish a statistically secure positive expectation.

### The simple benchmark was not beaten recently

A static equal-weight investment in the unseen 2× ETF universe ended at $268,812 over 2023–2026, versus $248,171 cash after all frozen modeled option trades matured. The benchmark had a much larger −40.24% drawdown, while a fully comparable option drawdown was not reconstructed for this unseen universe. Therefore the option strategy has not yet established superior risk-adjusted value over simply owning the leveraged underlyings.

### Profit depended on unverified target fills

Independent code review found that 109 synthetic target fills generated +$234,534 while the other 395 trades lost −$62,986. Target fills therefore contributed **136.7% of net profit**.

The engine infers a 6× option fill from the adjusted underlying’s daily high while holding entry volatility static. It does not observe an option bid, ask, trade, spread, depth, skew, or whether the required contract existed.

## Implementation audit findings

1. `optimize_crash_option_variables.py:27-30` uses theoretical option value at underlying daily high and assumes an exact target-price sale. This can create fills that never occurred in the option market.
2. Static entry volatility is retained for the full trade. Actual IV, term structure, skew, and volatility crush are absent.
3. `test_leveraged_etf_options_3y.py` originally allowed entries without a full 84-day forward horizon. Thirty trades were force-closed before modeled expiry, understating option time value by approximately $4,069 under the same static-IV model. The mature-only audit removes these trades; this flaw did not inflate the headline result but made the original terminal treatment invalid.
4. Weekly periods use `W-MON`, a Tuesday–Monday bucket, rather than the conventional Monday–Sunday week. A calendar-week rerun remained strongly positive, so this is specification ambiguity rather than the source of the profit.
5. The original schedule is built independently per symbol and only reconstructed into shared cash later. It happened to remain cash-feasible, but the simulator does not reject unaffordable orders in general.
6. Adjusted OHLC is a total-return-consistent research series, not necessarily the exact tradable underlying path seen by historical option contracts around distributions and corporate actions.

## 33/100 score and every deduction

| Category | Max | Awarded | Deducted | Why points were removed | Required remediation |
|---|---:|---:|---:|---|---|
| Unseen/OOS validation | 15 | 9 | **−6** | Frozen rule transferred to old and cross-sectional samples, but those outcomes are now inspected and option fills remain synthetic. | Freeze current commit and run a prospective holdout beginning 2026-08-06 for at least two years and 100 matured entries, with no changes. Require net positive after costs, PF ≥1.25, DD ≤25%. |
| Parameter multiplicity | 12 | 5 | **−7** | Winner followed 300 crash cells plus earlier PLTR, TSMX, target, risk, pause, and universe searches. No PBO or deflated-statistic correction. | Register the full search family; run CSCV/PBO and deflated Sharpe or block-randomized maximum-statistic test. Require PBO <25% and corrected p<0.05. |
| Universe selection | 10 | 4 | **−6** | Unseen broad ETFs helped, but no point-in-time census includes failed, closed, or delisted products; present universe is hand selected and tech-heavy. | Build dated census of every eligible US long 2× product, include closures and missing-series accounting, and freeze eligibility. Require ≥70% underlying families positive and no family >25% of profit. |
| Historical option-chain validation | 15 | 0 | **−15** | Zero historical option trades, NBBO quotes, IV surfaces, or contract records were replayed. | Obtain point-in-time chain/NBBO data. Map every signal to an existing contract. Require ≥80% executable signals, chain P&L ≥50% of synthetic P&L, PF ≥1.20, DD ≤1.5× synthetic. |
| Execution realism | 10 | 2 | **−8** | Close-only survived, but exact 6× synthetic target fills dominate and no quote depth or next-tick execution exists. | Execute at next available bid after signal, enforce volume/open-interest/depth limits, and reject unavailable contracts. Require positive net P&L with zero same-bar theoretical fills. |
| Costs/slippage | 8 | 4 | **−4** | Large generic spread stress passed, but observed contract-level spreads are unknown and combined adverse test lost money. | Use historical NBBO spread, fees, adverse selection, and missed fills per contract. Require positive results at median and 90th-percentile observed cost scenarios. |
| Walk-forward validation | 8 | 2 | **−6** | Annual diagnostics exist, but there is no pristine nested walk-forward; leave-one-crash-regime-out failed every fold. | Run ≥4 purged walk-forward folds with an 84-day embargo. Require ≥75% profitable folds after costs, median PF ≥1.15, and no fold >50% of profit. |
| Robustness/stress | 10 | 5 | **−5** | Entry-day and parameter neighborhoods passed, but +25% entry IV and combined adverse assumptions were negative. | Replace realized-vol entry pricing with actual historical IV; require profitability at actual IV and under +25% premium / −25% exit-value stress. |
| Concentration/risk | 6 | 2 | **−4** | Cash remained positive, but unseen runs reached 99–117 open positions and the leading recent symbol supplied 39.7% of profit. | Add portfolio-wide premium, positions, family, issuer, and correlation caps. Require ≤20 positions, ≤10% premium at risk, no family >25%, and stress DD ≤25%. |
| Operational/live readiness | 6 | 0 | **−6** | No broker contract mapper, paper shadow history, reconciliation, monitoring, or automated kill switches. | Build contract selection and broker adapter; shadow trade ≥6 months with ≥100 orders. Require ≥95% signal/order reconciliation, no unresolved incidents, and predefined daily/premium/DD kill switches. |
| **Total** | **100** | **33** | **−67** | **Research candidate only** | **Close the chain-data, prospective-holdout, and operational gates before risking capital.** |

## Ordered remediation plan

### Gate 1 — Historical option-chain replay

This is the highest-value next action. All underlying-only testing is downstream of a potentially wrong premium and fill model. Obtain historical chains/NBBO, contract definitions, volume, open interest, and corporate-action records. Re-run the frozen signals without choosing a new parameter set.

**Stop condition:** if net option-chain P&L is negative, fewer than 80% of signals map to tradable contracts, or real-chain P&L is below 50% of synthetic P&L, reject this generation.

### Gate 2 — Prospective immutable holdout

Freeze commit and protocol. Do not adjust strikes, DTE, TP, pauses, universe rules, or model after seeing results. New launches enter only through the predeclared eligibility rule.

**Stop condition:** after two years and at least 100 matured entries, reject if net P&L ≤0, PF <1.25, or DD >25%.

### Gate 3 — Point-in-time universe census

Include every eligible product, including failures and closures. Hold out whole underlying families and issuers.

**Stop condition:** reject if fewer than 70% of families are positive or one family contributes more than 25% of profit.

### Gate 4 — Portfolio risk engine

Integrate cash and marks inside the signal simulator—not as an after-the-fact reconstruction. Cap concurrent positions, total premium, per-family exposure, issuer exposure, and correlated delta/vega.

**Stop condition:** reject if the strategy needs more than 20 concurrent positions or more than 10% premium at risk to remain profitable.

### Gate 5 — Live shadow execution

Map each signal to an actual broker contract and record signal time, quote, order, acknowledgment, fill, cancel, and discrepancy.

**Stop condition:** require at least six months/100 orders, ≥95% reconciliation, positive net results after actual costs, and no unresolved risk-control failure before considering small capital.

## Bottom line

The falsification work found **real evidence of a broad synthetic effect**: old periods, a new ETF universe, all weekdays, all nearby parameters, close-only target checks, and large generic spread assumptions remained positive.

It also found a decisive market-readiness failure: a 25% increase in entry option volatility makes the system negative, and there are no historical option quotes proving the modeled premiums or +500% fills existed. The strategy therefore cannot honestly be called unbiased, proven, or ready for real money today.
