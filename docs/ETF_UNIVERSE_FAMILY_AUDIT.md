# Point-in-time ETF universe and family audit

## Scope and honest coverage statement

The executable census applies one objective rule: a US-listed ETF targeting **+2x the daily return** of a US equity index, sector, or single stock. It records sponsor/SEC URLs, issuer, underlying, economic family, and the first date for which JayBot observed price history.

`data/etf_universe_census.csv` is deliberately labeled an **observed research census**. It contains the 20 products used in the frozen current and unseen tests. It is not represented as every long 2x ETF ever launched. Durable sponsor pages and SEC filings establish the listed products used here, but did not provide an exhaustive historical security master of closures/delistings. Missing products are therefore missing-series accounting, not silently treated as nonexistent. `first_observed_price_date` is an availability bound; it is not called inception unless a sponsor source establishes inception.

Run:

```bash
env -u PYTHONPATH /cygdrive/c/Python313/python.exe build_etf_universe_census.py
env -u PYTHONPATH /cygdrive/c/Python313/python.exe audit_etf_universe_families.py
```

The census builder validates all rows against the objective +2x/long rule, rejects duplicate tickers or missing durable URLs, hashes the source CSV, and writes dated eligibility snapshots. Default snapshots are 2023-08-06 and 2026-08-06. A product is point-in-time eligible only on/after its first observed date; no backfill before launch/observation is permitted.

## Family audit method

`audit_etf_universe_families.py` joins the frozen synthetic-option ledger to the census and groups P&L by economic underlying family, issuer, and symbol. It performs leave-one-family-out by removing all frozen trades in one family, with no parameter selection. This is exactly additive for the current engine because premium is fixed and pause state is independent per symbol.

The two preregistered gates from `FALSIFICATION_AUDIT.md` are reported mechanically:

- at least 70% of economic families profitable;
- largest positive family no more than 25% of total net profit.

Results:

| Frozen scenario | Positive families | Largest family / total profit | Gates |
|---|---:|---:|---|
| current mature | 9/10 (90%) | Alphabet, 29.76% | family breadth pass; concentration fail |
| unseen recent | 8/10 (80%) | Semiconductors, 39.71% | family breadth pass; concentration fail |
| unseen pre-development | 6/10 (60%) | Semiconductors, 31.43% | both fail |

Every leave-one-family-out remainder stayed positive in these three ledgers, but this does not rescue the failed breadth/concentration gates. Issuer concentration is also severe: the unseen sample is 100% ProShares, while 91.0% of absolute grouped P&L in the current sample is Direxion. Issuer leave-out would empty the unseen sample and is therefore not evidence of issuer portability.

## Artifacts

- `data/etf_universe_census.csv` — sourced observed-product/family registry.
- `backtest_results/universe_census/census_manifest.json` — hash, counts, and explicit completeness limitations.
- `backtest_results/universe_census/census_as_of_2023-08-06.csv`
- `backtest_results/universe_census/census_as_of_2026-08-06.csv`
- `backtest_results/universe_family_audit/scenario_summary.csv`
- `backtest_results/universe_family_audit/group_concentration.csv`
- `backtest_results/universe_family_audit/leave_one_family_out.csv`
- `backtest_results/universe_family_audit/audit_summary.json`

All P&L remains synthetic Black-Scholes research output, not historical option-chain fills. The audit reduces concentration opacity; it does not close the unavailable historical-constituent or option-execution gaps.
