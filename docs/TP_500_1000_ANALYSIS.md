# Option Take-Profit Sweep: +500% to +1000%

## Recommendation

Use **+800% TP** as the next synthetic-model system candidate, meaning sell when the option value reaches **9× entry value**.

This is not the highest result in every sample. It is the best robustness-aware compromise that:

- is positive in the requested-ETF mature sample;
- is positive in the recent unseen broad/sector 2× ETF sample;
- is positive in the 2010–2023 pre-development sample;
- remains positive when entry option volatility is increased 25%;
- has the least-negative combined-adverse result of the tested targets.

No TP from +500% through +1000% passed the combined-adverse scenario, so +800% does not make the strategy market-ready.

## Frozen parameters

Only TP changed. Strike remains 10% OTM, DTE 84 days, fixed $500 premium, whole contracts, day-21/−50% check, and six-week per-ETF pause.

## Winners by objective

- Highest current requested-ETF raw profit: **+950% TP** — $206,480.
- Highest recent unseen-universe raw profit: **+1000% TP** — $169,065.
- Highest pre-development raw profit: **+600% TP** — $444,673.
- Highest unconstrained robustness score: **+550% TP**, but it loses under +25% entry IV.
- Best +25%-IV result: **+800% TP** — +$8,482.
- Recommended system compromise: **+800% TP**.

## +800% results

| Sample | Profit | Trades | Win rate | Profit/premium |
|---|---:|---:|---:|---:|
| Requested ETFs, mature 2023–2026 | $187,515 | 458 | 37.12% | 99.73% |
| Unseen ETFs, 2023–2026 | $163,573 | 740 | 33.51% | 51.35% |
| Unseen ETFs, 2010–2023 | $429,001 | 3,691 | 29.53% | 24.78% |
| Unseen recent, entry IV +25% | $8,482 | 751 | 30.23% | 2.81% |
| Combined adverse | −$6,283 | — | — | −2.68% |

## Interpretation

Raising TP generally increases payoff per rare winner while reducing target frequency. Current and recent samples favor very high targets, but the long pre-development sample peaks near +600% and deteriorates above that. +800% sacrifices some long-history profit to obtain a positive +25%-IV stress result and strong recent transfer.

This adds eleven more searched parameter cells and therefore increases multiple-testing exposure. It must be treated as a new research generation. Historical option-chain replay and a new prospective holdout are still required before changing any live or paper system.
