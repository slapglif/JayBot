# JayBot

JayBot contains a TradingView Pine v6 strategy plus reproducible portfolio, crash, and synthetic-option research engines.

## Current research source of truth

- `docs/RESEARCH_JOURNEY.md` — ordered path from the baseline through the current result, including rejected rules and model boundaries.
- `config/winning_parameters.json` — exact machine-readable share/option parameters and reconstructed result.
- `docs/SCRIPT_INDEX.md` — every experiment script and its artifacts.
- `skills/jaybot-options-research/SKILL.md` — repeatable workflow and verification gate.

The current raw modeled option configuration is 10% OTM, 84 DTE, +500% TP, fixed $500 premium per weekly ETF entry, with a day-21/−50% trigger that pauses that ETF for six weeks. Its shared-$100k mark-to-model reconstruction ended at $271,548.35 with −17.64% maximum drawdown, 69 maximum open positions, and 504 round trips. Option prices are synthetic over real ETF OHLC, not historical option-chain fills.

## Pine strategy

1. Open a 15-minute chart in TradingView.
2. Open Pine Editor, paste `GistDipBuyer_v1.pine`, save, and add it to the chart.
3. Enable the approved-watchlist control only for an authorized symbol.
4. Use regular-session data and set realistic commission/slippage.

The Pine strategy implements single-symbol behavior. TradingView `strategy()` cannot hold a shared multi-symbol portfolio; the Python engines provide the portfolio reference implementation.

## Reproduce the final option result

```bash
env -u PYTHONPATH /cygdrive/c/Python313/python.exe test_leveraged_etf_options_3y.py
env -u PYTHONPATH /cygdrive/c/Python313/python.exe calculate_option_drawdown_and_orders.py
```

Key outputs:

- `backtest_results/leveraged_etf_options_3y/raw_winner_option_orders.csv`
- `backtest_results/leveraged_etf_options_3y/raw_winner_option_equity_curve.csv`
- `backtest_results/leveraged_etf_options_3y/raw_winner_drawdown_summary.json`
- `screenshots/29_leveraged_options_drawdown.png`

## Verification boundary

These artifacts are research, not investment advice or evidence of future profitability. The option engines omit historical option-chain quotes, IV surfaces/skew, spreads, liquidity, and verified contract availability. Do not call a configuration live-ready until it is rerun with licensed chain/NBBO data and portfolio-wide exposure controls.
