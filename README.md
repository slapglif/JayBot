# Gist Dip Buyer v1 â€” TradingView Pine v6

This package translates the supplied Python-backtester specification into the closest correct TradingView strategy.

## Use

1. Open a **15-minute** chart in TradingView.
2. Open Pine Editor, paste `GistDipBuyer_v1.pine`, save, and add it to the chart.
3. Enable **Chart symbol is on approved watchlist** only for a symbol you authorize.
4. Use regular-session data for comparable results. Defaults assume US equities, 09:30â€“16:00 ET.
5. Set realistic commission/slippage in TradingView's Strategy Properties before interpreting results.

## Exact behavior implemented

- Evaluates the confirmed 13:00 ET 15-minute bar.
- Requires close below the captured regular-session open and below SMA(200).
- Buys 1.25% of current strategy equity per entry (quantity computed at the signal close).
- Waits two observed trading sessions between entries.
- Caps entries at four and planned allocation at 5%.
- Recalculates and places a limit exit at 5% above the whole position's weighted average price.
- Has no stop loss; positions can remain open indefinitely.
- Uses no lookahead.

## Platform constraints (not silently faked)

A TradingView `strategy()` runs and places orders on **one chart symbol**. It cannot hold a shared portfolio across arbitrary symbols. Therefore these prose requirements cannot be implemented faithfully inside one Pine strategy:

- scan a user watchlist and select the largest percentage decliner;
- hold/manage ten different stocks in one strategy account;
- enforce shared portfolio slots or a portfolio-wide five-day pause.

`request.security()` can inspect other symbols, but strategy orders still execute only on the chart symbol; pretending otherwise would produce invalid backtest results. This implementation deliberately gates the current chart with an approval checkbox and models all per-stock rules faithfully. A true portfolio replica needs the original Python backtester or an external alert/execution orchestrator.

## Semantics worth knowing

- "Trading days" means regular sessions actually observed in loaded chart data, not calendar days.
- The evaluation uses the 13:00 bar's **close** and `process_orders_on_close=true`.
- Limit exits allow the target to fill when touched using TradingView's broker emulator assumptions.
- `pyramiding` is fixed at Pine's declaration-time value of four; the configurable input may lower the cap from 4 but not raise it.
- The 15-minute restriction is runtime-checked because Pine cannot make the chart timeframe itself configurable.

## Local verification

```bash
python -m unittest discover -s tests -v
python validate.py
```

Local validation checks behavioral state transitions and Pine source invariants. TradingView does not publish a supported offline Pine compiler; final compiler validation must be done by pasting the source into TradingView's Pine Editor.