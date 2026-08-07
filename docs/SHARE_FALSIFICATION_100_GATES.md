# JayBot Share-System Falsification — 100-Point Evidence Rubric

This rubric applies only to the share strategy in `config/winning_parameters.json`. It does not use or require options, option chains, proprietary feeds, or prospective wall-clock waiting.

## Frozen strategy under test

- Universe: METU, AAPU, MSFU, NFXL, PLTU, IBX, NVDU, GGLL, AMZU, TSLT.
- Up to two distinct share purchases per session.
- 2.5% of current equity per tranche; four tranches and 10% intended maximum per symbol.
- At least one trading session between tranches.
- Whole-position exit at weighted-average cost +50%.
- Five basis points per side in the base case.

## Meaning of the two scores

1. **Falsification coverage** measures whether all predeclared tests were actually executed with reproducible artifacts. It can reach 100 immediately from historical public data.
2. **Strategy survival** measures how many predeclared performance/risk gates the frozen strategy passes. It is never increased merely because a test was implemented.

Keeping these separate prevents missing research from being confused with an adverse result.

## Coverage rubric

| Evidence family | Points | Completion requirement |
|---|---:|---|
| Canonical implementation and reconciliation | 10 | Exact config, deterministic engine, cash/equity/order reconciliation, unit tests |
| Public-data provenance and corporate actions | 10 | Source URLs, hashes, date ranges, duplicate/split checks, point-in-time availability |
| Temporal out-of-sample slices | 15 | Non-overlapping annual/rolling folds with no parameter tuning on test folds |
| Long-history and crash regimes | 15 | Dot-com, GFC, COVID, 2022 bear, and recent samples using declared actual/proxy modes |
| Universe robustness | 10 | Leave-one-symbol, family, and issuer tests; concentration attribution |
| Parameter stability | 10 | Neighborhood around TP, tranche size, spacing, and purchase count; no winner-only report |
| Execution and costs | 10 | Base plus spread/slippage/commission/delayed-entry sensitivities |
| Benchmark opportunity cost | 10 | SPY and QQQ total-return or clearly labeled price-return comparisons |
| Portfolio risk and unresolved positions | 5 | Mark-to-market open positions, drawdown, cash, exposure, duration, tail concentration |
| Statistical uncertainty | 5 | Block bootstrap/confidence intervals and multiple-comparison accounting |
| **Total** | **100** | Every required artifact generated and verified |

## Strategy-survival gates

- Positive net return in at least 75% of non-overlapping temporal folds.
- Positive net return in at least four of five named stress regimes.
- Positive return after 25 bps/side plus $1/order.
- Maximum drawdown no worse than 35% and not materially worse than the leveraged benchmark.
- Return greater than SPY over the same dates and competitive with QQQ after accounting for materially greater drawdown.
- No symbol contributes more than 25% of total profit.
- At least 70% of leave-one-symbol remainders stay profitable.
- At least 70% of the immediate parameter neighborhood stays profitable.
- Terminal open-position losses are included; a 100% realized win rate earns no credit when only winners are closed.
- Bootstrap probability of positive return exceeds 95% after accounting for the tested parameter family.

## Historical public data hierarchy

1. Existing Signal Console adapters: Cboe delayed-quote historical daily OHLCV, Yahoo chart/spark, then Stooq fallback.
2. SEC/sponsor sources for inception, issuer, and corporate-action metadata.
3. Existing cached Yahoo hourly bars for the two-year 13:30 ET execution proxy.
4. Underlying-based pre-inception simulations only when explicitly labeled; 2× daily leverage, financing/expense drag, and the switch to the live ETF must be declared. A 1× underlying series must not be presented as a 2× ETF history.

All observed history can be processed immediately. No prospective waiting period is part of this historical falsification score.
