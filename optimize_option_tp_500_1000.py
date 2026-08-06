#!/usr/bin/env python
"""Optimize only the JayBot option take-profit from +500% to +1000%.

Strike, DTE, sizing, pause logic, universes, and date windows remain frozen.
Reports raw and robustness-aware rankings; does not rewrite winning parameters.
"""
import json,os
from pathlib import Path
import pandas as pd
from falsification_audit import CURRENT,UNSEEN,Scenario,fetch,run_universe
OUT=Path('backtest_results/tp_500_1000_audit');OUT.mkdir(parents=True,exist_ok=True)
TPS=[int(os.environ['TP_ONLY'])] if os.environ.get('TP_ONLY') else list(range(500,1001,50))
def main():
 data={s:fetch(s) for s in sorted(set(CURRENT+UNSEEN))};rows=[]
 samples=[('current_mature',CURRENT,'2023-08-06','2026-08-05'),('unseen_recent',UNSEEN,'2023-08-06','2026-08-05'),('unseen_predevelopment',UNSEEN,'2010-01-01','2023-07-31')]
 for tp in TPS:
  for name,u,st,en in samples:
   sc=Scenario(f'tp_{tp}_{name}',tp_pct=tp);r,_,_=run_universe(data,u,st,en,sc);rows.append({'tp_pct':tp,'sample':name,**r})
  # The already-failing +25% entry-IV sensitivity is retained as a hard robustness check.
  sc=Scenario(f'tp_{tp}_iv25',tp_pct=tp,entry_iv_mult=1.25);r,_,_=run_universe(data,UNSEEN,'2023-08-06','2026-08-05',sc);rows.append({'tp_pct':tp,'sample':'unseen_recent_iv25',**r})
  sc=Scenario(f'tp_{tp}_combined_adverse',tp_pct=tp,target_mark='close',entry_iv_mult=1.25,hold_iv_mult=.8,entry_spread_pct=.05,exit_spread_pct=.05,commission_per_contract=1);r,_,_=run_universe(data,UNSEEN,'2023-08-06','2026-08-05',sc);rows.append({'tp_pct':tp,'sample':'combined_adverse',**r})
 d=pd.DataFrame(rows);suffix=f"_{os.environ['TP_ONLY']}" if os.environ.get('TP_ONLY') else '';d.to_csv(OUT/f'all_tp_results{suffix}.csv',index=False)
 base=d[d['sample'].isin([x[0] for x in samples])].copy();pivot=base.pivot(index='tp_pct',columns='sample',values='profit_on_premium_pct');profit=base.pivot(index='tp_pct',columns='sample',values='profit');rank=pd.DataFrame(index=pivot.index);rank['current_profit']=profit.current_mature;rank['unseen_recent_profit']=profit.unseen_recent;rank['unseen_predevelopment_profit']=profit.unseen_predevelopment;rank['current_pop_pct']=pivot.current_mature;rank['unseen_recent_pop_pct']=pivot.unseen_recent;rank['unseen_predevelopment_pop_pct']=pivot.unseen_predevelopment;rank['median_pop_pct']=pivot.median(axis=1);rank['worst_pop_pct']=pivot.min(axis=1);rank['dispersion_pop_pct']=pivot.max(axis=1)-pivot.min(axis=1);iv=d[d['sample']=='unseen_recent_iv25'].set_index('tp_pct');ad=d[d['sample']=='combined_adverse'].set_index('tp_pct');rank['iv25_profit']=iv.profit;rank['iv25_pop_pct']=iv.profit_on_premium_pct;rank['combined_adverse_profit']=ad.profit;rank['combined_adverse_pop_pct']=ad.profit_on_premium_pct;rank['positive_base_samples']=(pivot>0).sum(axis=1);rank['robust_score']=rank['median_pop_pct']+0.5*rank['worst_pop_pct']-0.15*rank['dispersion_pop_pct'];rank['iv25_pass']=rank.iv25_profit>0;rank['recommended_eligible']=rank.iv25_pass&(rank.positive_base_samples==3);rank=rank.reset_index().sort_values('robust_score',ascending=False);rank.to_csv(OUT/'tp_ranking.csv',index=False)
 eligible=rank[rank.recommended_eligible].sort_values('robust_score',ascending=False);recommended=eligible.iloc[0];best_raw=int(rank.loc[rank.current_profit.idxmax(),'tp_pct']);best_robust=int(rank.iloc[0].tp_pct);best_iv=int(rank.loc[rank.iv25_profit.idxmax(),'tp_pct']);summary={'tested_tp_pct':TPS,'best_current_raw_profit_tp_pct':best_raw,'unconstrained_robust_tp_pct':best_robust,'best_iv25_tp_pct':best_iv,'recommended_system_tp_pct':int(recommended.tp_pct),'selection_rule':'best robustness score among TPs positive in all three base samples and under +25% entry-IV markup','combined_adverse_passes':int((rank.combined_adverse_profit>0).sum()),'warning':'This is a new TP optimization, not a pristine holdout or historical option-chain validation.','recommended_row':recommended.to_dict()};(OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(rank.to_string(index=False));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
