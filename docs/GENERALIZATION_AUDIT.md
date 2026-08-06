# Statistical Generalization Audit and Unseen-Sample Falsification Plan

## Bottom line

The reported result is an **in-sample synthetic-option research result**, not an estimate of live expected return. The 10% OTM / 84-DTE / +500% target rule was selected as the maximum of a 300-cell crash grid and was then applied to a favorable, present-day set of leveraged single-stock ETFs. The recent ETF run is not a clean holdout because both the strategy and the tested universe arrived after prior option overlays, cross-asset rankings, crash-grid selection, and recent-ETF tests.

The result can be falsified with free underlying data, but it cannot be validated as an executable option strategy without point-in-time historical option-chain and quote data.

## Audit findings

### Multiple testing and selection path

- The raw winner is rank 1 of 300 by aggregate crash profit, so its quoted aggregate is the maximized statistic, not an unbiased performance estimate.
- The search path was broader than 300 formal cells: earlier PLTR/TSMX overlays, risk and target sweeps, cross-asset ranking, pause-rule invention, a balanced candidate, and recent ETF comparisons add researcher degrees of freedom.
- No correction for family-wise selection, false discovery, Probability of Backtest Overfitting, or a deflated performance statistic is reported.
- Neighboring parameters should be treated as a family, not as independent confirmations: all cells reuse the same symbols, weeks, and three crash episodes.

### Regime dependence

From `all_300_combinations.csv`:

- Raw winner: dot-com **-$11,443**, GFC **+$1,724**, COVID **+$62,863**, aggregate **+$53,144**.
- COVID contributes **118.3%** of aggregate profit; dot-com offsets **21.5%**. The winner is therefore a COVID-dominated regime bet.
- Its per-regime ranks are only 39th (dot-com), 33rd (GFC), and 33rd (COVID), despite ranking first on the aggregate.
- **0 of 300** tested combinations was profitable in all three crashes.
- Leave-one-regime-out selection fails every held-out regime:
  - optimize on GFC+COVID -> 12.5%/84/+500%; held-out dot-com **-$25,787**;
  - optimize on dot-com+COVID -> 17.5%/112/+500%; held-out GFC **-$9,221**;
  - optimize on dot-com+GFC -> 12.5%/28/+250%; held-out COVID **-$4,579**.

This is direct evidence that parameter ranking does not generalize across the three available stress regimes.

### Universe selection, survivorship, and concentration

- The recent universe is a present-day list, not a point-in-time census of all eligible 2x single-stock ETFs. Delisted/closed products and products never selected are absent.
- Different inception dates create unequal exposure. PLTU and IBX have only 9 and 8 executed trades respectively, while GGLL has 83. Cross-symbol win counts are therefore not comparable without exposure adjustment.
- Nine of ten symbols are profitable, but the top symbol contributes **28.0%** of total profit and the top three contribute **66.9%**. METU loses **$9,306**.
- Symbols are highly correlated technology/growth exposures. Ten ticker labels do not represent ten independent samples.
- Issuer/product survival, option-listing availability, and today’s visibility can all select for successful underlyings ex post.

### Outcome concentration and dependence

- The 504 executed round trips overlap heavily, reaching 69 simultaneous positions. Trades are neither independent nor 504 effective observations.
- The top 10 profitable trades account for **14.4%** of total profit; the top 25 account for **35.6%**; the top 50 account for **69.2%**. Standard IID trade-level t-tests or confidence intervals would be invalid.
- Weekly entries in the same names and sectors share regime, volatility, and factor shocks. Inference must resample time blocks and preferably clusters of correlated symbols, not individual trades.

## What qualifies as genuinely unseen

A validation sample is genuinely unseen only if all of the following are frozen **before its outcomes are inspected**:

1. complete rule set, including volatility model, clipping, strike rounding, entry weekday/bucket, pause logic, target-touch logic, and sizing;
2. eligibility rule for the universe, not merely a handpicked ticker list;
3. start/end dates and exclusion/embargo rules;
4. primary metric and falsification thresholds;
5. transaction/model sensitivity scenarios;
6. treatment of missing prices, ETF inception, delistings, splits, and option unavailability.

Because the 2023-2026 ETF results have already been viewed and influenced claims, repartitioning that same period now creates only **post-selection diagnostics**, not a pristine holdout. The strongest temporal holdout is future data beginning after 2026-08-05, with no further tuning.

## Executable falsification experiments using free underlying data

These tests can reject robustness claims, but passing them validates only the synthetic model over underlying OHLC.

### 1. Locked prospective test (highest evidentiary value)

- Freeze the repository commit and a machine-readable protocol now.
- Start the holdout on 2026-08-06; do not modify parameters or universe eligibility.
- Use every ETF meeting the predeclared eligibility rule, including future launches and later closures where data remain available.
- Minimum horizon: two full years and at least 100 matured entries; score only entries whose 84-day expiry is observable.
- Primary falsification: terminal modeled P&L <= 0, max drawdown worse than the predeclared bound, or profit <= 0 after any one of the specified model haircuts.

### 2. Nested leave-one-regime-out test

- Define regimes without looking at strategy P&L, using public index drawdown/recovery dates.
- For each fold, choose one parameter cell using only the other regimes, then evaluate exactly once on the held-out regime.
- Include ordinary bull, sideways/high-rate, inflation shock, and slow bear regimes—not only crash windows.
- Aggregate fold signs and dollars with equal regime weights, not by pooling observations. The existing three-regime diagnostic already fails all three held-out folds.

### 3. Point-in-time universe holdout

- Build a dated census of all US 2x single-stock long ETFs from issuer pages/SEC filings and free daily price sources; define eligibility mechanically (for example, at least 120 prior sessions of prices).
- Freeze groups by underlying sector and issuer. Hold out entire sectors or underlying companies, not random trades from the same ticker.
- Score all eligible products from actual inception, including closures. Report unavailable historical price series as missing rather than silently dropping them.
- A defensible falsification is leave-one-underlying-family-out: tune nowhere, run the frozen rule on each omitted family, and require positive results in a predeclared fraction of families plus no single family contributing more than a fixed share.
- This reduces hand-selection bias but cannot remove option-listing survivorship with free underlying data.

### 4. Purged walk-forward temporal folds

- Use contiguous calendar folds with at least an 84-day embargo between training and test entries so open contracts cannot leak across boundaries.
- Freeze parameters from pre-fold data only; never select a global winner and call each fold out-of-sample.
- Report fold P&L, drawdown, hit rate, premium deployed, and concentration. Require a majority of test folds positive and no single fold responsible for most aggregate profit.
- Because all current dates have already been inspected, label this a stability diagnostic, not unseen validation.

### 5. Parameter-neighborhood and model-haircut falsification

Run the complete predeclared matrix, without selecting a new winner:

- strike: 7.5%, 10%, 12.5%; DTE: 70, 84, 98; TP: +400%, +500%, +600%;
- volatility: entry RV, daily-updated RV, and RV multiplied by 0.75/1.25;
- target execution: daily-high touch at target, next-close execution, and a one-session delay;
- premium/spread haircut: +10%, +25%, +50% entry cost and -10%, -25% exit proceeds;
- skip a predeclared 10%, 25%, and 50% of trades as unavailable.

Falsify robustness if profitability exists only at the exact selected cell, only with static entry volatility, or only under same-day high-touch target fills.

### 6. Time-cluster bootstrap and concentration stress

- Resample monthly or quarterly blocks, preserving all symbols and overlapping positions within each block.
- Reconstruct shared cash and marked open positions for every bootstrap path.
- Also remove the best month, best quarter, best symbol, and top 10/25/50 trades without replacement.
- Report the fraction of paths with positive terminal P&L and drawdown beyond the declared limit. Do not bootstrap individual trades.
- This is a conditional uncertainty analysis, not an independent validation, because it reuses selected data.

### 7. Negative controls

- Shift the weekly entry bucket by each possible weekday while preserving all other rules.
- Compare against predeclared simple controls: unpaused weekly calls, fixed-expiry/no-target calls, and randomized entry weeks generated with a fixed seed while preserving per-symbol trade counts.
- Apply the same 300-cell search to randomized/block-permuted regime data and compare the observed maximum with the distribution of maxima. This estimates how often a similarly impressive “winner” appears from the search procedure itself.

## Minimum reporting protocol

- Publish the frozen commit hash, protocol, full universe census, exclusions, and every tested cell.
- Use shared-cash equity, daily marks, and an 84-day terminal maturity lag.
- Report dollars and drawdown, not only profit-on-premium, because premium is repeatedly recycled.
- Report symbol, sector, month/quarter, and regime concentration.
- Make the primary test pass/fail before looking at secondary slices.
- Any rule or universe change after holdout inspection starts a new research generation and a new future holdout.

## What free underlying data cannot prove

No experiment using only underlying OHLC can establish:

- that the required option series, strike, and expiration existed on each entry date;
- executable bid/ask quotes, spreads, depth, or fills for integer contract sizes;
- historical implied volatility level, term structure, skew/smile, dividends, borrow effects, or early exercise;
- whether a daily underlying high caused the option ask/bid to touch the modeled +500% target;
- survivorship-free option-listing coverage or delisted-contract history;
- realistic assignment, corporate-action, market-halt, and expiration settlement behavior.

Those claims require licensed or otherwise archived point-in-time option chains with NBBO/trades and contract reference data. Even such data would still require a prospective or untouched holdout to address strategy-selection bias.
