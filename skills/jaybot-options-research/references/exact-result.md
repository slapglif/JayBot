# Exact result reference

## Parameters

- Universe: METU, AAPU, MSFU, NFXL, PLTU, IBX, NVDU, GGLL, AMZU, TSLT
- Fixed premium cap: $500 per trade
- Strike: 10% OTM
- DTE: 84 calendar days
- Take profit: +500%
- Risk gate: if still open on day 21 and option value is down at least 50%, pause that symbol six weeks
- Model: Black–Scholes over real adjusted ETF OHLC; rolling 20-session realized volatility clipped 25%–175%; 3% risk-free rate
- Window: 2023-08-06 through 2026-08-05; actual ETF inception respected

## Shared-$100k mark-to-model reconstruction

- Ending equity: $271,548.3515
- Max drawdown: −17.6373217% / −$19,286.5164
- Peak: $109,350.5957 on 2023-12-19
- Trough: $90,064.0793 on 2024-01-04
- Minimum cash: $77,925.6640
- Maximum open positions: 69
- Round trips: 504
- Orders: 1,008

## Boundary

Underlying OHLC is historical; option prices and fills are synthetic. The result is not historical option-chain replay and does not verify spreads, liquidity, IV surfaces, or contract availability.
