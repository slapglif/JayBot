---
name: jaybot-options-research
description: Use when reproducing or extending JayBot option backtests.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [trading, options, backtesting, jaybot, crash-testing]
    related_skills: [trading-strategy-porting]
---

# JayBot Options Research

## Overview

Reproduce and extend the JayBot share and synthetic-option research without losing portfolio semantics, data limitations, or the exact parameter path that produced the current result.

## When to use

Use for JayBot option grids, leveraged single-stock ETF tests, crash stress tests, option-pause changes, order-ledger reconstruction, or drawdown questions.

Do not use this as evidence of live option fills. Historical option chains were unavailable; the current engines price options synthetically over real adjusted underlying OHLC.

## Source of truth

Read these before changing parameters:

1. `docs/RESEARCH_JOURNEY.md` — ordered experiment history and rejected rules.
2. `config/winning_parameters.json` — machine-readable exact parameters and result.
3. `docs/SCRIPT_INDEX.md` — script-to-artifact map.
4. `docs/FALSIFICATION_AUDIT.md` — current 33/100 readiness score, executed unseen tests, failed IV/adverse stresses, and remediation gates.
5. `backtest_results/leveraged_etf_options_3y/raw_winner_drawdown_summary.json` — verified drawdown reconstruction.

The current synthetic effect transfers across unseen underlying samples, but +25% entry-IV markup makes it negative and no historical option-chain fills have been validated.

Completion criterion: the proposed run can name its parent configuration and every changed field.

## Current raw option winner

- Universe: METU, AAPU, MSFU, NFXL, PLTU, IBX, NVDU, GGLL, AMZU, TSLT.
- Weekly entries per ETF when not paused.
- Fixed $500 premium cap per trade in the last-three-year reconstruction.
- 10% OTM strike.
- 84 calendar DTE.
- +500% TP, meaning 6× option value.
- If still open at day 21 and modeled value is down at least 50%, pause new entries on that ETF for six weeks.
- Integer contracts; skip when the cap cannot buy one.
- Black–Scholes, entry-date rolling 20-session realized volatility clipped to 25%–175%, 3% risk-free rate.

## Required workflow

1. **Classify the request.** Decide whether it changes share rules, option rules, universe, data window, or portfolio constraints. Completion: a parameter diff exists before code changes.
2. **Preserve the parent.** Create a new script/output directory rather than overwriting prior ledgers. Completion: prior artifacts remain readable.
3. **Use real underlying data.** Record inception and test each ETF only after inception unless an explicitly labeled return-chained proxy is required. Completion: output contains start/end per symbol.
4. **Model pause semantics correctly.** A contract that hit its target before day 21 cannot trigger the loss pause. Pause is per symbol unless the user explicitly requests portfolio-wide behavior. Completion: ledger includes trigger and resume evidence.
5. **Mark terminal positions.** Include open-option model value in equity and drawdown. Completion: ending equity reconciles cash plus open values.
6. **Separate trade grid from portfolio simulation.** Independent-symbol cumulative P&L is not automatically a cash-constrained account. Reconstruct shared cash/equity before reporting account return or drawdown. Completion: minimum cash and max concurrent positions are reported.
7. **Verify artifacts.** Save complete grid, top configurations, dated order ledger, equity curve, drawdown summary, and white-font chart. Completion: every reported number has a machine-readable source.
8. **State model limits.** Explicitly label synthetic pricing, static entry-volatility behavior, OHLC target-touch assumptions, missing spreads/IV surfaces/liquidity, and selection bias.

## Reproduction commands

On the Windows/Cygwin host, clear the Hermes-injected `PYTHONPATH` if it points Python at incompatible packages:

```bash
env -u PYTHONPATH /cygdrive/c/Python313/python.exe test_leveraged_etf_options_3y.py
env -u PYTHONPATH /cygdrive/c/Python313/python.exe calculate_option_drawdown_and_orders.py
```

Expected drawdown summary for the committed raw-winner schedule:

- ending modeled equity: $271,548.35;
- max drawdown: −17.6373%;
- peak/trough: 2023-12-19 to 2024-01-04;
- minimum cash: $77,925.66;
- maximum open positions: 69;
- 504 round trips / 1,008 orders.

## Common pitfalls

1. Calling cumulative independent-symbol P&L an account return without shared-cash reconstruction.
2. Treating the fixed $500 cap as dynamically compounded 0.5% equity.
3. Checking a winning, already-closed option at day 21 and falsely triggering a pause.
4. Using leveraged ETFs before their inception or assuming listed/liquid options existed.
5. Optimizing aggregate crash profit and calling it robust when COVID dominates. No tested grid combination was profitable in all three crashes.
6. Omitting open-position marks when calculating drawdown.
7. Forgetting that 84-DTE weekly entries can overlap heavily; the committed run reached 69 positions.

## Verification checklist

- [ ] Parent and parameter diff documented
- [ ] Actual symbol inception dates preserved
- [ ] Only still-open day-21 contracts trigger pauses
- [ ] Complete dated buy/sell ledger saved
- [ ] Shared cash, open values, and terminal equity reconcile
- [ ] Maximum drawdown, minimum cash, and maximum concurrent positions reported
- [ ] White-font chart saved
- [ ] Synthetic-option limitations stated
- [ ] Scripts and small result artifacts committed; data cache excluded
