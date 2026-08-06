#!/usr/bin/env python
import os,pandas as pd
from pathlib import Path
from falsification_audit import UNSEEN,Scenario,fetch,run_universe
tp=int(os.environ['TP_ONLY']);data={s:fetch(s) for s in UNSEEN};sc=Scenario(f'tp_{tp}_combined_adverse',tp_pct=tp,target_mark='close',entry_iv_mult=1.25,hold_iv_mult=.8,entry_spread_pct=.05,exit_spread_pct=.05,commission_per_contract=1);r,_,_=run_universe(data,UNSEEN,'2023-08-06','2026-08-05',sc);Path('backtest_results/tp_500_1000_audit').mkdir(parents=True,exist_ok=True);pd.DataFrame([{'tp_pct':tp,'sample':'combined_adverse',**r}]).to_csv(f'backtest_results/tp_500_1000_audit/adverse_{tp}.csv',index=False);print(tp,r['profit'],r['profit_on_premium_pct'])
