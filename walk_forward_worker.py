#!/usr/bin/env python
import os,json
from pathlib import Path
import pandas as pd
from falsification_audit import UNSEEN,Scenario,fetch,run_universe
EMBARGO_DAYS=84
def scenarios():
 return [Scenario(f'wf_{sp}_84_{tp}',strike_pct=sp,dte=84,tp_pct=tp) for sp in [7.5,10.0,12.5] for tp in [300.0,500.0,700.0]]
FOLDS={'2014_2015':('2014-01-01','2015-12-31'),'2016_2017':('2016-01-01','2017-12-31'),'2018_2019':('2018-01-01','2019-12-31'),'2020_2021':('2020-01-01','2021-12-31'),'2022_2023':('2022-01-01','2023-12-31'),'2024_2026':('2024-01-01','2026-08-05')}
name=os.environ['WF_FOLD'];ts,te=FOLDS[name];tr_start='2010-01-01';tr_end=str((pd.Timestamp(ts)-pd.Timedelta(days=EMBARGO_DAYS)).date());data={s:fetch(s) for s in UNSEEN};rows=[]
for sc in scenarios():
 tr,_,_=run_universe(data,UNSEEN,tr_start,tr_end,sc);test,_,_=run_universe(data,UNSEEN,ts,te,sc);rows.append({'fold':name,'train_start':tr_start,'train_end_purged':tr_end,'test_start':ts,'test_end':te,'embargo_days':EMBARGO_DAYS,'strike_otm_pct':sc.strike_pct,'dte_days':sc.dte,'tp_pct':sc.tp_pct,'train_profit':tr['profit'],'train_profit_on_premium_pct':tr['profit_on_premium_pct'],'test_profit':test['profit'],'test_premium':test['premium'],'test_profit_on_premium_pct':test['profit_on_premium_pct'],'test_trades':test['trades'],'test_win_rate_pct':test['win_rate_pct']})
out=Path('backtest_results/rigorous_stat_audit');out.mkdir(parents=True,exist_ok=True);pd.DataFrame(rows).to_csv(out/f'walk_forward_{name}.csv',index=False);print(name,'done')
