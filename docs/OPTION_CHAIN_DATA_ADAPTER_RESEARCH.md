# Option Chain Data Adapter Research

## Outcome

JayBot now has a provider-neutral option-chain schema and adapter prototype in `option_chain_adapter.py`.  It embeds no secrets.  Authenticated providers must read credentials from environment variables supplied by the caller.

A live no-auth smoke test succeeded against public current-chain endpoints on 2026-08-06, but these endpoints are not a replacement for historical OPRA/NBBO replay.

## Implemented prototype

### Provider-neutral schema

- `OptionContract`: underlying, normalized option symbol, expiration, call/put right, strike.
- `OptionQuote`: nullable bid/ask/last, sizes, volume, open interest, IV/Greeks, source, delayed flag, provider payload.
- `OptionChainAdapter` protocol: `fetch_chain(underlying, as_of=None)`.

### No-auth current adapters

1. `NasdaqCurrentOptionChainAdapter`
   - Endpoint observed working: `https://api.nasdaq.com/api/quote/AAPL/option-chain?assetclass=stocks&limit=10`
   - Returned JSON rows with bid/ask/last/volume/open interest for calls and puts.
   - Current table only; no historical `as_of` support; not historical NBBO evidence.

2. `CboeDelayedOptionChainAdapter`
   - Endpoint observed working: `https://cdn.cboe.com/api/global/delayed_quotes/options/AAPL.json`
   - Returned delayed quote-table JSON with OSI symbols, bid/ask/sizes, last, volume, OI, IV, Greeks, timestamp.
   - Important legal/use blocker: Cboe's delayed quote table page states automated downloading of delayed quote table data from the website is strictly prohibited. Do not use this for automated/bulk collection without permission/licensing.

CLI example:

```bash
env -u PYTHONPATH /cygdrive/c/Python313/python.exe option_chain_adapter.py AAPL --provider nasdaq
env -u PYTHONPATH /cygdrive/c/Python313/python.exe option_chain_adapter.py AAPL --provider cboe
```

## Provider research

### Databento OPRA.PILLAR

Best technical fit for JayBot historical validation.

Findings from Databento docs/pages:

- Dataset `OPRA.PILLAR` covers consolidated last sale and national BBO across US equity options exchanges.
- Available since 2013-04-01 UTC.
- Schemas include definitions plus quote/trade/bar forms such as `CBBO-1s`, `CBBO-1m`, `TCBBO`, `Trades`, OHLCV, statistics, status, and definition.
- Databento says historical data is available for usage-based rates or with an OPRA subscription; new users advertise credits, but an API key/account and dataset access are still required.

Blocker for JayBot historical NBBO:

- Need a Databento account/API key (`DATABENTO_API_KEY`) and licensed/paid OPRA.PILLAR access/usage credit for the selected date range and schemas.
- For each JayBot signal, implementation must fetch point-in-time definitions to prove contract existence, then fetch NBBO/quotes/trades around entry/exit times.

### Alpaca options market data

Findings from Alpaca docs:

- Historical option data availability begins February 2024.
- Alpaca has two options sources:
  - `Indicative`: free derivative of OPRA; quotes/trades are not actual OPRA and are delayed by 15 minutes.
  - `OPRA`: consolidated BBO feed; available only to subscribed users.

Blocker for JayBot historical NBBO:

- Need Alpaca account credentials (`ALPACA_API_KEY_ID`, `ALPACA_API_SECRET_KEY`) and OPRA agreements/subscription for real OPRA.
- Free/indicative source is useful for API-shape testing but must not be presented as real historical NBBO or fill validation.
- Limited start date (Feb 2024) cannot validate the full 3-year/older research horizon.

### ThetaData

Findings from ThetaData public pages/search snippets:

- Offers historical and real-time options data with tick, 1-second, 1-minute, EOD, chain snapshots, trades, NBBO quotes, and OPRA coverage.
- Pricing pages describe paid Options tiers; a historical free EOD blog mentions a ThetaData account is still required.

Blocker for JayBot historical NBBO:

- Need a ThetaData account/subscription tier covering the needed historical NBBO/quote granularity and date range. No embedded credentials.

### Cboe DataShop / LiveVol

Findings from Cboe DataShop page:

- All Access API includes real-time/historical options/equity data through subscriptions.
- Access to licensed SIP/OPRA fields is optional and not included in base price; OPRA subscription is required for live/delayed option prices.
- Trial subscriptions are not eligible for SIP data access.

Blocker for JayBot historical NBBO:

- Need Cboe/LiveVol account/subscription plus OPRA/SIP approvals for required fields; likely professional-user fee handling depending use.

## Exact historical NBBO blocker

The JayBot falsification gate requires point-in-time option contract existence and executable historical bid/ask/trade data. Public no-auth current-chain endpoints can prove the adapter/schema but cannot answer: "what was the bid/ask for this 84-DTE 10% OTM contract at the historical signal and target/exit time?"

To remove this blocker, buy/enable one of:

1. Databento `OPRA.PILLAR` historical access, with `Definition` + NBBO/CBBO/trade schema access for all needed signal dates; set `DATABENTO_API_KEY`.
2. Alpaca OPRA subscription and account credentials, accepting Feb-2024+ history only; set `ALPACA_API_KEY_ID` and `ALPACA_API_SECRET_KEY`.
3. ThetaData paid options tier/account covering historical NBBO for the target horizon.
4. Cboe DataShop/LiveVol subscription plus OPRA/SIP entitlement approval.

Until then, JayBot option results remain synthetic and should not be relabeled as historical option-chain validated.
