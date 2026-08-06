# Path to 100/100 Falsification Readiness

## Integrity rule

The score is evidence, not a target to optimize. A gate receives credit only after its predeclared test passes. Engineering more tests can expose failure; it cannot convert a failed strategy into a validated one. Changing sizing, DTE, universe, strike, or TP creates a new strategy generation and restarts out-of-sample validation.

## Current hard blocker discovered prospectively

The first public Cboe delayed-chain snapshot was captured with a cryptographically linked manifest. Under the frozen $500 cap, 10% OTM strike, and roughly 84-DTE requirement:

- 10 symbols requested;
- nine chains retrieved;
- only three symbols mapped to a contract affordable at the ask;
- three had no contract in the 70–105 DTE band;
- three had a qualifying contract but one contract cost more than $500;
- one endpoint was unavailable;
- mapped spreads were approximately 34%–57%;
- mapped contracts had daily volume of 0, 1, and 0.

This is a 30% mapping rate, versus the predeclared 95% executability gate. The frozen system therefore fails executability today. This cannot be repaired by scoring; changing the system would create a new hypothesis.

## Gates required for 100

| Gate | Required evidence | Current state |
|---|---|---|
| Historical option chain | Point-in-time listed contracts and actual NBBO/trades across at least 500 entries and three regimes | Blocked: licensed historical OPRA-class data required |
| Executability | ≥95% signals map to listed/liquid contracts under frozen $500/DTE/strike rules | Failed first prospective snapshot: 3/10 |
| Prospective validation | ≥2 years and ≥100 matured, broker-mapped entries with no rule changes | Started 2026-08-06; time cannot be backfilled |
| Execution | Actual or broker-shadow bid/ask, acknowledgments, fills/misses, and costs | Delayed public chain collection started; broker shadow not connected |
| Multiple testing | PBO <25% and corrected significance <0.05 | Pending dedicated audit |
| Purged walk-forward | ≥75% positive folds, median PF ≥1.15, no fold >50% of profit | Pending dedicated audit; prior leave-one-crash failed 0/3 |
| Point-in-time universe | Objective census including closures/delistings and leave-family-out success | Pending dedicated audit |
| Portfolio risk | ≤20 positions, ≤10% premium at risk, family caps, DD kill switch, positive after caps | Pending integrated simulation |
| Live operations | ≥6 months/100 mapped orders, ≥95% reconciliation, no unresolved risk failure | Not started |

## Data access required

Historical US option NBBO is licensed market data. Practical sources identified:

- Databento OPRA, historical since 2013, including definitions and NBBO; account/API key required. Their published offer currently includes trial credits, but credentials are still required.
- Cboe DataShop Option Quote Intervals, available from 2012; purchase required.
- ThetaData historical options/NBBO, available from 2012; account and appropriate tier required.
- Alpaca indicative option history is not actual OPRA NBBO and cannot close the real-chain gate.

No credentials are embedded in the repository. The provider-neutral adapter must fail closed when licensed data is unavailable.

## Prospective evidence protocol

`collect_prospective_option_chain.py` records delayed Cboe chains, selected contracts, source timestamps, raw and compressed SHA-256 hashes, and a previous-record hash. `verify_prospective_evidence.py` validates the entire chain. One initial research snapshot was captured. Recurring automated Cboe collection is **not enabled** because provider terms/licensing must authorize the intended bulk use first; the prepared wrapper remains available after permission or migration to a licensed provider.

This prospective record can earn future evidence, but it cannot grant credit for dates before the protocol was frozen.
