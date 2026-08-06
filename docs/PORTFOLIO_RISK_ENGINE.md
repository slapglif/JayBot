# Integrated shared-cash portfolio risk audit

The `run_portfolio_risk_audit.py` executable routes the frozen synthetic JayBot signals through one chronological account rather than reconstructing independently accepted symbol trades after the fact.

## Frozen signal generations evaluated

- +500% take-profit (the frozen raw option winner)
- +800% take-profit (the separately documented TP-sweep candidate)
- 10% OTM, 84 calendar DTE, fixed maximum $500 premium per signal, integer contracts, existing day-21 pause semantics
- Current mature and unseen-recent universes, both 2023-08-06 through 2026-08-05 with full-DTE entry eligibility

## Risk controls

- maximum 20 concurrent positions;
- maximum 10% account equity in original premium at risk;
- maximum 2.5% account equity per underlying family;
- maximum 1% account equity per symbol;
- cash affordability checked before every accepted entry;
- permanent new-entry kill switch at 25% peak-to-trough marked-equity drawdown.

Family and symbol caps are percentages of contemporaneous marked equity, not percentages of the 10% budget. Exits are processed before same-date entries. Candidate ordering is deterministic by entry date then symbol.

## Executed results

| Sample | TP | Ending modeled equity | Return | Max DD | Min cash | Max positions | Max premium risk | Accepted / candidates |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| current mature | +500% | $153,892.66 | 53.89% | -9.50% | $90,764.74 | 20 | 6.03% | 196 / 458 |
| unseen recent | +500% | $132,943.45 | 32.94% | -18.00% | $85,032.34 | 20 | 9.94% | 236 / 740 |
| current mature | +800% | $171,588.26 | 71.59% | -9.97% | $90,764.74 | 20 | 6.36% | 195 / 458 |
| unseen recent | +800% | $137,156.53 | 37.16% | -17.60% | $83,632.54 | 20 | 9.94% | 229 / 740 |

No evaluated run triggered the 25% drawdown kill switch. All limits were obeyed; position count was the binding control in each run. Rejected ledgers preserve the exact rejection reason.

## Validity boundary

These are **synthetic option simulations**, not historical option results. The underlying adjusted OHLC is real, but option entry prices, daily marks, and exits use Black-Scholes and do not observe historical chains, NBBO, IV surfaces/skew, spreads, liquidity, exact contract availability, or verified fills. The results do not remediate the historical-chain or +25% entry-IV falsification failures and are not evidence of live tradability.

## Reproduce

```bash
env -u PYTHONPATH /cygdrive/c/Python313/python.exe run_portfolio_risk_audit.py
```

Set `TP_ONLY=500|800` and/or `SAMPLE_ONLY=current_mature|unseen_recent` for resumable individual runs.
