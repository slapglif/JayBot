# JayBot strategy research journey

This document preserves the path that produced the current modeled result. All figures are research outputs, not investment advice.

## Data and execution conventions

- Equity tests use real Yahoo OHLC data. The strongest two-year share validation uses hourly regular-session bars and a 13:30 ET decision proxy.
- Option tests use real underlying/ETF OHLC but synthetic Black–Scholes option values because historical option chains were unavailable.
- Option assumptions omit historical IV surfaces, skew, spreads, liquidity, and exact contract availability. High-target results are especially model-sensitive.
- Five basis points per side is used in the principal share tests.
- New ETFs are tested only after inception unless a run explicitly says it chains an underlying proxy.

## Share-strategy progression

1. Baseline: 1.25% tranches, four tranches/5% per asset, one purchase per day, +29% weighted-average TP.
2. Two separate assets per day beat one; a one-trading-day tranche interval was best among 1–5 days.
3. Two-year hourly validation of the 1.25%/29% version returned 32.81%, CAGR 15.54%, max drawdown −17.87%; SPY returned 48.26% over the same bullish window.
4. Profit locks (+4/+2, +5/+2.5, +10/+5), portfolio pauses, and two-hour replacement scans reduced raw profit or increased churn. They were rejected from the raw winner.
5. Doubling sizing to 2.5% per tranche/four tranches/10% per asset and raising weighted-average TP to 35% returned 83.74% with −32.86% max drawdown.
6. Raising share TP to 50% returned 88.17%, CAGR 37.97%, max drawdown −35.11%. This is the current aggressive share rule set, but it carries large unresolved losers and up to roughly full-account intended allocation.

## Option-strategy progression

1. PLTR call overlays tested 0.2% premium risk, roughly 28 DTE, strikes $3–$8 above spot, and 50%/75% TPs. These were synthetic and small relative to share P&L.
2. TSMX was the strongest asset under the 50% share-TP run. A $5-OTM, 28-DTE, +80% TP overlay was slightly negative.
3. Weekly TSMX grid: risk 0.1%–0.5% and TP 50%–100%. The modeled raw winner was 0.5% risk with +95% TP.
4. Cross-asset weekly calls ranked PLTR, GGLL, NVDU, and AMZU positive; a fifth-ranked AAPU was negative.
5. Crash stress tests could not use recently launched leveraged ETFs before inception. A consistent AAPL/AMZN/MSFT/NVDA/CSCO universe was used. Weekly calls failed the prolonged dot-com and GFC bear markets but profited in COVID.
6. Added per-symbol pause: if an option is still open at three weeks and is down at least 50%, pause new options on that symbol for six weeks. This roughly halved modeled dot-com and GFC losses. Only still-open contracts can trigger the pause.
7. Exhaustive crash grid (300 combinations): strikes 10%–20% OTM, DTE 28–168 days, TP +50%–+500%. Highest aggregate profit: 10% OTM, 84 DTE, +500% TP. It was not universally robust: −$11,443 dot-com, +$1,724 GFC, +$62,863 COVID. No combination was positive in all three crashes.
8. More balanced crash candidate: 12.5% OTM, 28 DTE, +250% TP; +$5,575 dot-com, +$6,389 GFC, −$4,579 COVID, +$7,385 aggregate.
9. Last-three-year test on actual 2× ETFs used METU, AAPU, MSFU, NFXL, PLTU, IBX, NVDU, GGLL, AMZU, TSLT. The raw 10%/84-day/+500% configuration produced $171,548 cumulative modeled option profit on $209,338 cumulative premium, with 504 round trips and 37.30% wins.
10. A shared-$100,000 mark-to-model reconstruction was cash-feasible under fixed $500 entries: ending modeled equity $271,548, max drawdown −17.64%, peak $109,350.60 on 2023-12-19, trough $90,064.08 on 2024-01-04, minimum cash $77,925.66, and 69 maximum open positions.

## Current exact modeled option parameters

- Universe: METU, AAPU, MSFU, NFXL, PLTU, IBX, NVDU, GGLL, AMZU, TSLT.
- Entry frequency: first eligible session of each weekly bucket per ETF.
- Premium cap: fixed $500 per trade in the three-year reconstruction (described as 0.5% of the initial $100,000 reference account; it is not dynamically compounded risk).
- Strike: 10% above adjusted underlying close.
- Expiration: 84 calendar days.
- Profit target: +500% (option value reaches 6× entry value).
- Three-week risk gate: only if the option remains open at day 21; if modeled value is ≤50% of entry, pause that ETF’s new option entries for six weeks.
- Existing contracts remain open to target or expiration.
- Position sizing: integer contracts, floor($500 / (modeled premium × 100)); skip if zero.
- Model: Black–Scholes, rolling 20-session realized volatility clipped to 25%–175%, 3% risk-free rate.

## Principal risk and validity boundaries

- 69 simultaneous positions means the result is driven by highly correlated convex exposure, despite the small per-entry cap.
- The 504 round trips are 1,008 orders; many options expire worthless and a minority of large wins dominate.
- Synthetic target touches use daily underlying highs and static entry volatility. They are not verified option fills.
- Some ETFs may not have had liquid listed options, the required strike, or the required expiration throughout the period.
- Present-day ETF selection introduces survivorship and selection bias.
- Do not call this live-ready until rerun against licensed historical option-chain/NBBO data with portfolio-wide premium, position, liquidity, spread, and correlation caps.

## Reproduce

Run from the repository root with a Python environment containing pandas, numpy, requests, and matplotlib. On this Windows host, clear the injected Hermes `PYTHONPATH` when needed:

```bash
env -u PYTHONPATH /cygdrive/c/Python313/python.exe test_leveraged_etf_options_3y.py
env -u PYTHONPATH /cygdrive/c/Python313/python.exe calculate_option_drawdown_and_orders.py
```

The script index in `docs/SCRIPT_INDEX.md` maps every experiment to its artifact directory.
