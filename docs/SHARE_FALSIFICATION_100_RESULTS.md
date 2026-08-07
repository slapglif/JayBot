# JayBot Share Strategy — 100/100 Falsification Coverage

## Scope

This audit applies only to the canonical share system in `config/winning_parameters.json`:

- Universe: METU, AAPU, MSFU, NFXL, PLTU, IBX, NVDU, GGLL, AMZU, TSLT
- Two distinct purchases per session
- 2.5% equity tranches, four maximum, 10% intended maximum per asset
- One trading session between tranches
- +50% weighted-average take-profit
- No profit lock and no portfolio pause

No option prices, chains, implied volatility, NBBO data, proprietary datasets, or prospective waiting periods are used.

## Audit scores

| Score | Result | Meaning |
|---|---:|---|
| Falsification coverage | **100/100** | Every declared historical evidence family was executed and saved |
| Strategy survival | **4/8 gates (50%)** | Frozen rules passed four of eight performance/risk gates |

Coverage and survival are separate. A completed adverse test earns coverage but cannot be relabeled as a strategy pass.

## Corrected hourly observed/proxy validation

The primary implementation, `test_kitty_2_5pct_tp50.py`, was corrected and rerun over 495 sessions from 2024-08-07 through 2026-08-05.

| Metric | Corrected result |
|---|---:|
| Final equity | $141,895.99 |
| Total return | **+41.90%** |
| CAGR | **19.50%** |
| Maximum drawdown | **−33.03%** |
| Orders | 115 |
| Buys / exits | 99 / 16 |
| Open positions | 10 |

The prior +88.17% result is superseded because it used the wrong universe, did not enforce the 10% per-asset guard, and contained a cross-source stitching defect.

## Full historical audit

### Observed ETFs only

Public Cboe historical daily OHLCV, from each ETF's first observed date through 2026-08-06:

- Return: **+81.08%**
- CAGR: **16.04%**
- Maximum drawdown: **−37.58%**
- SPY over identical dates: **+86.84%**
- QQQ over identical dates: **+125.38%**
- Realized P&L: **+$143,057.89**
- Open-position P&L: **−$61,979.63**

The unresolved open losers are included in terminal equity; realized winners are not presented as total performance.

### Long historical hybrid

Public Yahoo underlying OHLCV is converted into an explicitly labeled 2× daily proxy with 1% annual drag before each ETF's observed history, then cleanly spliced to public Cboe ETF history.

- Window: 1999-01-04 through 2026-08-06
- Return: **+2,153.42%**
- CAGR: **11.96%**
- Maximum drawdown: **−54.78%**
- SPY: **+524.69%**
- QQQ: **+1,299.56%**
- Open-position P&L: **−$637,055.72**

The hybrid is a stress/research proxy, not a claim that the ETFs existed before inception.

## Gate results

| Gate | Result |
|---|---|
| Positive after 25 bps/side + $1/order | PASS |
| ≥70% leave-one-symbol tests profitable | PASS — 100% |
| ≥70% immediate parameter neighborhood profitable | PASS — 100% |
| 20-session block-bootstrap P(return > 0) ≥95% | PASS — 100% across 5,000 seeded replicates |
| ≥75% annual folds positive | FAIL — 74.07% |
| ≥4/5 named regimes positive | FAIL — 2/5 |
| Long-history maximum drawdown no worse than 35% | FAIL — −54.78% |
| Observed ETF result beats SPY | FAIL — 81.08% vs 86.84% |

### Named regimes

| Regime | Strategy return | Max drawdown |
|---|---:|---:|
| Dot-com | −28.44% | −41.40% |
| GFC | −24.30% | −49.50% |
| COVID | +92.63% | −40.83% |
| 2022 bear | −58.94% | −60.24% |
| Recent | +424.62% | −36.97% |

## Defects resolved

1. Replaced wrong ticker pairs (MSTU/TSMX/PLTR) with canonical MSFU/TSLT/PLTU.
2. Added the mark-to-market 10% maximum-asset allocation guard.
3. Removed cross-source `prev` contamination from the hourly stitch.
4. Rebuilt the splice from independently normalized, split-adjusted source histories.
5. Loaded point-in-time first-observed ETF dates from the universe census.
6. Preserved missing-bar behavior: a decision requires an actual 13:30 ET bar; no forward-filled execution.
7. Included terminal open-position losses and per-symbol attribution.
8. Added public-data provenance and explicit observed-vs-proxy labels.
9. Added annual, regime, leave-one-symbol, parameter, cost, benchmark, exposure, and block-bootstrap tests.
10. Fixed the falsification engine's prepared-data cache collision by retaining source dictionaries with cached entries.

## Reproduction

```bash
python share_falsification_100.py
python test_kitty_2_5pct_tp50.py
python -m pytest -q tests/test_share_falsification_100.py
```

Main artifacts:

- `backtest_results/share_falsification_100/summary.json`
- `backtest_results/share_falsification_100/all_tests.csv`
- `backtest_results/share_falsification_100/data_manifest.csv`
- `backtest_results/share_falsification_100/block_bootstrap_returns.csv`
- `backtest_results/share_falsification_100/*_equity.csv`
- `backtest_results/share_falsification_100/*_orders.csv`
- `backtest_results/kitty_2_5pct_tp50_2y_hourly/summary.json`
- `backtest_results/kitty_2_5pct_tp50_2y_hourly/equity_curve.csv`
- `backtest_results/kitty_2_5pct_tp50_2y_hourly/orders_with_dates.csv`
- `backtest_results/kitty_2_5pct_tp50_2y_hourly/symbol_attribution.csv`

## Verdict

Historical falsification is now **complete at 100/100 coverage** using public share-price data. The frozen strategy remains profitable in the observed and long-hybrid tests, but it is **not fully falsification-surviving** because of bear-regime losses, drawdown, and benchmark opportunity cost. Those are measured strategy properties rather than unresolved research gaps.
