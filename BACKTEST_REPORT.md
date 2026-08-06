# JayBot one-year portfolio backtest

## Result

Test window: **2025-08-05 through 2026-08-05** (250 US trading sessions), starting equity **$100,000**.

| Scenario | Friction | Final equity | Return | Max drawdown | Sharpe | Buys / exits | Open positions |
|---|---:|---:|---:|---:|---:|---:|---:|
| Frictionless sensitivity | 0 bps, $0/order | $97,779.03 | **-2.22%** | -8.07% | -0.31 | 137 / 54 | 9 |
| Base expected liquid-market case | 5 bps/side, $0/order | $94,238.89 | **-5.76%** | -8.51% | -1.21 | 159 / 78 | 8 |
| Stress case | 25 bps/side, $1/order | $99,063.62 | **-0.94%** | -5.28% | -0.16 | 144 / 72 | 8 |

The path-dependent portfolio changes holdings when fills change, so the stress scenarios are not expected to be monotonically ordered. In every case, open underwater positions are marked to market at the end. Reported 100% realized win rate is mechanical: the strategy has only a +5% profit exit and no stop, so losses remain unrealized rather than disproving risk.

## Strategy rules modeled

- $100,000 initial capital; 1.25% of current equity per entry.
- Up to four entries and 5% allocation per symbol.
- Up to ten concurrent symbols.
- Below intraday MA and below regular-session open at the evaluation point.
- New-position candidate ranked by largest decline from the session open; only the top eligible new symbol is opened per day.
- Existing positions may add after two observed sessions.
- Whole-position exit at weighted-average cost +5%.
- No stop or time exit; losing positions can remain indefinitely.
- Five-session portfolio pause after all ten slots are occupied.
- Fill sensitivity includes 0, 5, and 25 bps per side plus the stated commission case.

## Watchlist assumption

The source specification says the watchlist is user supplied but the repository contains no symbols. This run used a disclosed representative list of mega-caps and selected index/sector leveraged ETFs:

`AAPL MSFT NVDA AMZN GOOGL META TSLA AVGO BRK-B JPM V MA UNH XOM COST NFLX AMD QQQ SPY TQQQ SQQQ UPRO SPXU SOXL SOXS TECL TECS`

Changing this list materially changes the result.

## Critical data limitation

This is a **real-data hourly proxy**, not a claim of exact 15-minute parity. Yahoo exposes one year of hourly bars but only about 60 days of 15-minute history. Therefore:

- the 200×15-minute SMA is approximated by a 50×hourly SMA;
- the 1:00 PM ET decision uses the 1:30 PM ET hourly close, the first completed Yahoo hourly bar after 1 PM;
- OHLC fills are bar-based rather than quote/tick based;
- regular-session bars only are used;
- price data are historical Yahoo OHLC; dividends are not credited as cash, and borrow fees, taxes, spread dynamics, partial fills, halts, and market impact are not modeled;
- using today's constituent/watchlist selection creates possible selection/survivorship bias.

An exact production-grade rerun needs (1) the actual approved watchlist and (2) licensed one-year 15-minute or finer data, ideally including corporate actions and NBBO/quote information. The included engine is reproducible and can be adapted to that feed.

## Files

- `backtest.py` — reproducible portfolio engine and Yahoo downloader
- `data_cache/` — downloaded hourly OHLC cache
- `backtest_results/base/{summary.json,trades.csv,equity_curve.csv}`
- `backtest_results/frictionless/...`
- `backtest_results/stressed/...`

## Reproduce

```bash
python backtest.py --start 2025-08-05 --end 2026-08-06 --out backtest_results/base --slippage-bps 5 --commission 0
```

This backtest is research, not investment advice or evidence of future profitability.
