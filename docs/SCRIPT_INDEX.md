# Script and artifact index

## Core share research

- `backtest.py` — original one-year hourly portfolio reference engine.
- `optimize_kitty_strategy.py` — share-rule optimizer and stitched ETF/underlying daily data.
- `test_two_buys_daily.py` — two different purchases/day and 1–5-day tranche interval sweep.
- `validate_best_2y_hourly.py` — two-year hourly validation of the 1.25%/29%-TP share winner.
- `test_kitty_2_5pct_tp35.py` — 2.5% tranches, 10% per asset, +35% TP.
- `test_kitty_2_5pct_tp50.py` — 2.5% tranches, 10% per asset, +50% TP.
- `test_portfolio_rules.py` — portfolio pause/rule overlay.
- `test_share_profit_lock.py` — +4% arm/+2% lock.
- `test_ten_stock_profit_lock_reentry.py` — +5%/+2.5% and two-hour replacement scan.
- `test_ten_stock_10_5_reentry.py` — +10%/+5% and two-hour replacement scan.

## Early option overlays

- `test_pltr_option_overlay.py` — PLTR monthly calls, strike-offset comparison.
- `test_pltr_option_overlay_twice_monthly.py` — two monthly PLTR entries, +50% TP.
- `test_pltr_option_overlay_twice_monthly_tp75.py` — two monthly entries, +75% TP.
- `test_pltr_option_overlay_three_monthly_tp75.py` — three monthly entries, +75% TP.
- `test_tsmx_option_overlay_tp80.py` — TSMX $5-OTM/28-DTE/+80% overlay.
- `optimize_tsmx_weekly_options.py` — weekly TSMX 0.1%–0.5% risk and 50%–100% TP grid.
- `compare_weekly_options_10_tickers.py` — requested ten-ticker option ranking.

## Crash research

- `stress_test_weekly_options_crashes.py` — dot-com, GFC, COVID baseline on long-history technology stocks.
- `stress_test_crashes_with_pause.py` — three-week/−50% trigger and six-week per-symbol pause.
- `optimize_crash_option_variables.py` — 300-combination strike/DTE/TP grid and best-ledger generation.

## Final leveraged-ETF result

- `test_leveraged_etf_options_3y.py` — last-three-year comparison of raw and balanced crash-grid winners on ten 2× ETFs.
- `calculate_option_drawdown_and_orders.py` — shared-$100k mark-to-model equity curve, maximum drawdown, and 1,008-row buy/sell ledger.

## Falsification audit

- `falsification_audit.py` — frozen-parameter unseen-era/universe tests, weekday perturbations, execution/IV stresses, annual diagnostics, and nearby-parameter surface.
- `docs/FALSIFICATION_AUDIT.md` — executed evidence, 33/100 market-readiness score, every deduction, and remediation gates.
- `docs/GENERALIZATION_AUDIT.md` — independent statistical audit, leave-one-regime-out failures, and prospective protocol.
- `backtest_results/falsification_audit/` — complete machine-readable tests, manifests, ledgers, score, bootstrap diagnostics, benchmarks, and shared-cash diagnostics.
- `screenshots/30_falsification_audit.png` — white-font audit dashboard.

## Key artifacts

- `backtest_results/leveraged_etf_options_3y/summary.csv`
- `backtest_results/leveraged_etf_options_3y/by_symbol.csv`
- `backtest_results/leveraged_etf_options_3y/all_trades.csv`
- `backtest_results/leveraged_etf_options_3y/raw_winner_option_orders.csv`
- `backtest_results/leveraged_etf_options_3y/raw_winner_option_equity_curve.csv`
- `backtest_results/leveraged_etf_options_3y/raw_winner_drawdown_summary.json`
- `backtest_results/crash_option_variable_grid/all_300_combinations.csv`
- `backtest_results/crash_option_variable_grid/top_20.csv`
- `screenshots/27_option_variable_grid_crashes.png`
- `screenshots/28_leveraged_etf_options_3y.png`
- `screenshots/29_leveraged_options_drawdown.png`

## Generated data

`data_cache/` is intentionally excluded from Git. Every downloader records its symbols and dates in source and can regenerate the cache. `__pycache__/` is also excluded.
