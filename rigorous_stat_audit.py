#!/usr/bin/env python
"""Fast statistically conservative audit using existing JayBot artifacts."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd
OUT=Path('backtest_results/rigorous_stat_audit')
CRASH_GRID=Path('backtest_results/crash_option_variable_grid/all_300_combinations.csv')
FALS=Path('backtest_results/falsification_audit')
SEED=20260806; REPS=20000; EMBARGO_DAYS=84

def load():
    g=pd.read_csv(CRASH_GRID)
    annual=pd.read_csv(FALS/'unseen_annual_results.csv')
    neigh=pd.read_csv(FALS/'unseen_parameter_neighborhood.csv')
    return g,annual,neigh

def cscv_pbo(g):
    cols=['dotcom_profit','gfc_profit','covid_profit']; rows=[]
    for hold in cols:
        trcols=[c for c in cols if c!=hold]; train=g[trcols].sum(axis=1); i=int(train.idxmax())
        vals=g[hold].astype(float); rank=float(vals.rank(method='average',pct=True).iloc[i]); rank=float(np.clip(rank,1e-6,1-1e-6))
        rows.append({'holdout_block':hold.replace('_profit',''),'train_blocks':','.join(c.replace('_profit','') for c in trcols),'selected_row':i,'strike_otm_pct':float(g.loc[i,'strike_otm_pct']),'dte_days':int(g.loc[i,'dte_days']),'tp_pct':float(g.loc[i,'tp_pct']),'train_profit':float(train.iloc[i]),'heldout_profit':float(vals.iloc[i]),'heldout_rank_percentile':rank,'logit_rank':float(np.log(rank/(1-rank))),'below_median_oos':bool(rank<.5)})
    f=pd.DataFrame(rows)
    return f, {'method':'CSCV/PBO approximation: enumerate all leave-one-crash-out folds from the recorded 300-cell crash grid','candidate_count':int(len(g)),'fold_count':int(len(f)),'pbo':float(f.below_median_oos.mean()),'profitable_fold_rate':float((f.heldout_profit>0).mean()),'median_logit_rank':float(f.logit_rank.median()),'limitation':'Only 3 crash blocks exist; PBO has coarse 1/3 resolution and low power.'}

def max_stat(g):
    cols=['dotcom_profit','gfc_profit','covid_profit']; mat=g[cols].to_numpy(float); centered=mat-mat.mean(axis=0,keepdims=True); obs=mat.sum(axis=1); rng=np.random.default_rng(SEED); mx=[]
    for _ in range(REPS): mx.append(float(centered[:,rng.integers(0,3,3)].sum(axis=1).max()))
    mx=np.array(mx); obsi=int(obs.argmax()); p=float((1+(mx>=obs.max()).sum())/(REPS+1))
    return pd.DataFrame({'bootstrap_max_profit_null':mx}), {'method':'block bootstrap max-statistic with crash blocks resampled and block cross-sectional means centered','candidate_count':int(len(g)),'block_count':3,'bootstrap_reps':REPS,'seed':SEED,'observed_best_total_profit':float(obs.max()),'observed_best_row':obsi,'observed_best_params':{'strike_otm_pct':float(g.loc[obsi,'strike_otm_pct']),'dte_days':int(g.loc[obsi,'dte_days']),'tp_pct':float(g.loc[obsi,'tp_pct'])},'max_stat_corrected_p_value':p,'null_quantiles':{str(q):float(np.quantile(mx,q)) for q in [.5,.9,.95,.99]},'limitation':'Three crash blocks make this a conservative dependence-aware approximation, not a definitive SPA/White Reality Check.'}

def instability(cfold,neigh):
    top=neigh.sort_values('profit',ascending=False).head(10).copy()
    top['rank']=range(1,len(top)+1)
    selected=cfold[['strike_otm_pct','dte_days','tp_pct']].astype(str).agg('/'.join,axis=1)
    return top, {'method':'parameter-selection instability from leave-one-crash-out winners plus unseen-neighborhood ranking','crash_fold_unique_selected_parameter_sets':int(selected.nunique()),'crash_fold_parameter_change_count':int((selected!=selected.shift()).iloc[1:].sum()),'unseen_neighborhood_top10_parameter_sets':top[['rank','strike_pct','dte','tp_pct','profit','profit_on_premium_pct']].to_dict(orient='records') if 'strike_pct' in top.columns else top.head(10).to_dict(orient='records'),'limitation':'Uses existing crash and falsification artifacts; does not rerun the entire hidden human search path.'}

def walk_forward(annual):
    a=annual.copy(); a['year']=a['test'].str.extract(r'(\d{4})').astype(int); a=a.sort_values('year')
    folds=[('2010_2012',2010,2012),('2013_2015',2013,2015),('2016_2018',2016,2018),('2019_2021',2019,2021),('2022_2025',2022,2025)]
    rows=[]
    for name,s,e in folds:
        x=a[(a.year>=s)&(a.year<=e)]
        rows.append({'fold':name,'test_start':f'{s}-01-01','test_end':f'{e}-12-31','embargo_days':EMBARGO_DAYS,'selected_rule':'frozen 10% OTM / 84 DTE / +500% TP','test_profit':float(x.profit.sum()),'test_premium':float(x.premium.sum()),'test_trades':int(x.trades.sum()),'test_profit_on_premium_pct':float(x.profit.sum()/x.premium.sum()*100) if x.premium.sum() else 0,'positive_years':int((x.profit>0).sum()),'years':int(len(x))})
    f=pd.DataFrame(rows); total=float(f.test_profit.sum())
    return f, {'method':'purged walk-forward approximation using frozen-rule annual unseen results; 84-day embargo is declared between selection/fold boundaries, but annual artifact is the available machine-readable unit','fold_count':int(len(f)),'embargo_days':EMBARGO_DAYS,'selected_test_profit_sum':total,'selected_profitable_fold_rate':float((f.test_profit>0).mean()),'median_profit_on_premium_pct':float(f.test_profit_on_premium_pct.median()),'largest_fold_profit_share_pct':float(f.test_profit.max()/total*100) if total>0 else None,'passes_75pct_profitable_folds':bool((f.test_profit>0).mean()>=.75),'passes_no_fold_over_50pct_profit':bool(total>0 and f.test_profit.max()/total<=.5),'limitation':'This audits the frozen rule, not nested parameter re-optimization; annual blocks are coarser than exact trade-level purging.'}

def main():
    OUT.mkdir(parents=True,exist_ok=True); g,annual,neigh=load(); cf,cs=cscv_pbo(g); bd,bs=max_stat(g); top,ins=instability(cf,neigh); wf,ws=walk_forward(annual)
    cf.to_csv(OUT/'cscv_pbo_crash_folds.csv',index=False); bd.to_csv(OUT/'block_bootstrap_max_stat_distribution.csv',index=False); top.to_csv(OUT/'parameter_instability_top_neighborhood.csv',index=False); wf.to_csv(OUT/'purged_walk_forward_annual_folds.csv',index=False)
    summary={'inputs':{'crash_grid':str(CRASH_GRID),'falsification_dir':str(FALS),'embargo_days':EMBARGO_DAYS},'cscv_pbo':cs,'block_bootstrap_max_stat':bs,'parameter_selection_instability':ins,'purged_walk_forward':ws,'overall_interpretation':{'passes_strict_multiple_testing_gate':bool(bs['max_stat_corrected_p_value']<.05 and cs['pbo']<.25),'passes_walk_forward_gate':bool(ws['passes_75pct_profitable_folds'] and ws['passes_no_fold_over_50pct_profit']),'critical_limitations':['All source P&L remains synthetic option pricing over adjusted underlying OHLC; no option-chain/NBBO validation.','Recorded 300-cell crash grid understates the larger human research multiplicity.','CSCV/PBO and max-stat are low-power because only three crash regimes are recorded.','Walk-forward is annual frozen-rule audit from existing artifact, not exact trade-level nested CSCV.']}}
    (OUT/'audit_summary.json').write_text(json.dumps(summary,indent=2,default=str)); print(json.dumps(summary,indent=2,default=str))
if __name__=='__main__': main()
