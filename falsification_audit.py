#!/usr/bin/env python
"""Falsification-first audit for the frozen JayBot option rule.

Tests frozen parameters on unseen eras/universes, nearby parameters, entry-day
perturbations, and adverse execution/model assumptions. Underlying OHLC is real;
option prices remain synthetic and are never represented as historical fills.
"""
from __future__ import annotations
import json,math,requests
from dataclasses import dataclass,asdict
from pathlib import Path
import numpy as np,pandas as pd

OUT=Path('backtest_results/falsification_audit'); CACHE=Path('data_cache/falsification')
CURRENT=['METU','AAPU','MSFU','NFXL','PLTU','IBX','NVDU','GGLL','AMZU','TSLT']
UNSEEN=['SSO','QLD','USD','ROM','UCC','UYG','DDM','MVV','RXL','DIG']
FROZEN={'strike_pct':10.0,'dte':84,'tp_pct':500.0}

def N(x): return .5*(1+math.erf(x/math.sqrt(2)))
def call(s,k,t,v,r=.03):
 if t<=0:return max(s-k,0.)
 if s<=0 or k<=0:return 0.
 d1=(math.log(s/k)+(r+.5*v*v)*t)/(v*math.sqrt(t));d2=d1-v*math.sqrt(t)
 return s*N(d1)-k*math.exp(-r*t)*N(d2)

def fetch(sym,start='2009-01-01',end='2026-08-06'):
 CACHE.mkdir(parents=True,exist_ok=True);p=CACHE/f'{sym}.csv'
 if p.exists():return pd.read_csv(p,index_col=0,parse_dates=True)
 p1=int(pd.Timestamp(start,tz='UTC').timestamp());p2=int((pd.Timestamp(end,tz='UTC')+pd.Timedelta(days=200)).timestamp())
 u=f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1={p1}&period2={p2}&interval=1d&events=div%2Csplits&includeAdjustedClose=true'
 j=requests.get(u,headers={'User-Agent':'Mozilla/5.0'},timeout=45).json();res=j.get('chart',{}).get('result')
 if not res:return pd.DataFrame()
 z=res[0];q=z['indicators']['quote'][0];adj=z['indicators'].get('adjclose',[{}])[0].get('adjclose',q['close'])
 x=pd.DataFrame(q,index=pd.to_datetime(z['timestamp'],unit='s',utc=True).tz_convert('US/Eastern').tz_localize(None));x['AdjClose']=adj;fac=x.AdjClose/x.close
 for c in ['open','high','low','close']:x[c.title()]=x[c]*fac
 x=x[['Open','High','Low','Close']].dropna();x.to_csv(p);return x

@dataclass(frozen=True)
class Scenario:
 name:str; strike_pct:float=10.; dte:int=84; tp_pct:float=500.; entry_nth:int=0
 target_mark:str='high'; entry_iv_mult:float=1.; hold_iv_mult:float=1.; entry_spread_pct:float=0.; exit_spread_pct:float=0.; commission_per_contract:float=0.

def entry_indices(idx,start,end,dte,nth,mature_only=True):
 end=pd.Timestamp(end);cut=end-pd.Timedelta(days=dte) if mature_only else end
 ok=(idx>=pd.Timestamp(start))&(idx<=cut);pos=np.flatnonzero(ok)
 if not len(pos):return []
 # Calendar Monday-Sunday weeks. nth=0..4 tests weekday/holiday perturbation.
 periods=idx[pos].to_period('W-SUN');groups={}
 for i,w in zip(pos,periods):groups.setdefault(w,[]).append(i)
 return [v[min(nth,len(v)-1)] for v in groups.values() if v]

def simulate_symbol(sym,d,start,end,sc,mature_only=True):
 if d.empty:return [],{'symbol':sym,'profit':0,'premium':0,'trades':0,'wins':0,'paused':0,'triggers':0,'start':None,'end':None}
 d=d.copy();d['rv']=d.Close.pct_change().rolling(20).std()*math.sqrt(252);d.rv=d.rv.clip(.25,1.75).fillna(.80)
 idx=d.index;close=d.Close.to_numpy(float);high=d.High.to_numpy(float);rv=d.rv.to_numpy(float);entries=entry_indices(idx,start,end,sc.dte,sc.entry_nth,mature_only)
 pause_until=pd.Timestamp.min;checks=[];ledger=[];profit=premium=0.;wins=paused=triggers=0
 for ei in entries:
  ed=idx[ei]
  for q in checks:
   if not q['done'] and ed>=q['date']:
    q['done']=True
    if q['trigger']:pause_until=max(pause_until,q['date']+pd.Timedelta(weeks=6));triggers+=1
  if ed<pause_until:paused+=1;continue
  s=close[ei];k=round(s*(1+sc.strike_pct/100),2);entry_iv=min(rv[ei]*sc.entry_iv_mult,3.0);hold_iv=min(entry_iv*sc.hold_iv_mult,3.0)
  theo=call(s,k,sc.dte/365,entry_iv);entry_price=theo*(1+sc.entry_spread_pct);n=math.floor(500/(entry_price*100))
  if n<1:continue
  expiry=ed+pd.Timedelta(days=sc.dte);last=np.searchsorted(idx.values,expiry.to_datetime64(),side='right')-1;last=min(last,len(idx)-1)
  target=entry_price*(1+sc.tp_pct/100);ev=None;xi=None;reason='EXPIRY'
  for j in range(ei+1,last+1):
   mark=high[j] if sc.target_mark=='high' else close[j];rem=max((expiry-idx[j]).days,0)/365;v=call(mark,k,rem,hold_iv)*(1-sc.exit_spread_pct)
   if v>=target:ev=target;xi=j;reason='TARGET';break
  if ev is None:
   xi=last;ev=max(close[last]-k,0)*(1-sc.exit_spread_pct)
  gross=(ev-entry_price)*100*n;fees=sc.commission_per_contract*n*2;pnl=gross-fees;profit+=pnl;premium+=entry_price*100*n+sc.commission_per_contract*n;wins+=pnl>0
  check_date=ed+pd.Timedelta(days=21)
  if idx[xi]>=check_date:
   ci=np.searchsorted(idx.values,check_date.to_datetime64(),side='left')
   if ci<len(idx):
    cv=call(close[ci],k,max((expiry-idx[ci]).days,0)/365,hold_iv)*(1-sc.exit_spread_pct)
    checks.append({'date':idx[ci],'trigger':cv<=entry_price*.5,'done':False})
  ledger.append({'symbol':sym,'entry_date':ed,'exit_date':idx[xi],'entry_price':entry_price,'exit_price':ev,'contracts':n,'strike':k,'expiry_date':expiry,'entry_iv':entry_iv,'hold_iv':hold_iv,'pnl':pnl,'reason':reason,'scenario':sc.name})
 return ledger,{'symbol':sym,'profit':profit,'premium':premium,'trades':len(ledger),'wins':wins,'paused':paused,'triggers':triggers,'start':str(max(pd.Timestamp(start),idx.min()).date()),'end':str(min(pd.Timestamp(end),idx.max()).date())}

def run_universe(data,syms,start,end,sc,mature_only=True):
 logs=[];rows=[]
 for s in syms:
  l,r=simulate_symbol(s,data[s],start,end,sc,mature_only);logs.extend(l);rows.append(r)
 a=pd.DataFrame(rows);summary={'test':sc.name,'start':start,'end':end,'symbols':len(syms),'profit':float(a.profit.sum()),'premium':float(a.premium.sum()),'trades':int(a.trades.sum()),'wins':int(a.wins.sum()),'win_rate_pct':float(a.wins.sum()/a.trades.sum()*100) if a.trades.sum() else 0.,'profit_on_premium_pct':float(a.profit.sum()/a.premium.sum()*100) if a.premium.sum() else 0.,'positive_symbols':int((a.profit>0).sum()),'max_symbol_share_pct':float(a.profit.max()/a.profit.sum()*100) if a.profit.sum()>0 else None}
 return summary,a,pd.DataFrame(logs)

def equal_weight_benchmark(data,syms,start,end):
 vals=[]
 for s in syms:
  d=data[s];x=d[(d.index>=start)&(d.index<=end)]
  if len(x)>1:vals.append((s,float(x.Close.iloc[-1]/x.Close.iloc[0]-1)))
 return {'benchmark_symbols':len(vals),'equal_weight_buy_hold_pct':float(np.mean([v for _,v in vals])*100),'components':dict(vals)}

def main():
 OUT.mkdir(parents=True,exist_ok=True);syms=sorted(set(CURRENT+UNSEEN));data={s:fetch(s) for s in syms}
 manifest=pd.DataFrame([{'symbol':s,'rows':len(data[s]),'first':str(data[s].index.min().date()) if len(data[s]) else None,'last':str(data[s].index.max().date()) if len(data[s]) else None} for s in syms]);manifest.to_csv(OUT/'data_manifest.csv',index=False)
 results=[];symbol_rows=[];ledgers=[]
 # Frozen tests: post-selection current universe, unseen cross-section, and long pre-development era.
 tests=[('current_mature','2023-08-06','2026-08-05',CURRENT,Scenario('current_mature')),
        ('unseen_recent','2023-08-06','2026-08-05',UNSEEN,Scenario('unseen_recent')),
        ('unseen_predevelopment','2010-01-01','2023-07-31',UNSEEN,Scenario('unseen_predevelopment'))]
 for name,st,en,u,sc in tests:
  r,a,l=run_universe(data,u,st,en,sc);r.update(equal_weight_benchmark(data,u,st,en));results.append(r);a['test']=name;symbol_rows.append(a);ledgers.append(l)
 # Entry-day perturbation on unseen recent sample.
 for nth in range(5):
  sc=Scenario(f'entry_day_{nth+1}',entry_nth=nth);r,a,l=run_universe(data,UNSEEN,'2023-08-06','2026-08-05',sc);results.append(r)
 # Adverse pricing/execution/model assumptions on unseen recent sample.
 stress=[Scenario('close_only',target_mark='close'),Scenario('spread_5pct_commission',entry_spread_pct=.05,exit_spread_pct=.05,commission_per_contract=1),Scenario('iv_markup_25pct',entry_iv_mult=1.25),Scenario('iv_crush_20pct',hold_iv_mult=.8),Scenario('combined_adverse',target_mark='close',entry_iv_mult=1.25,hold_iv_mult=.8,entry_spread_pct=.05,exit_spread_pct=.05,commission_per_contract=1)]
 for sc in stress:
  r,a,l=run_universe(data,UNSEEN,'2023-08-06','2026-08-05',sc);results.append(r)
 # Nearby parameter surface, evaluated only on unseen recent universe.
 grid=[]
 for sp in [7.5,10,12.5]:
  for dte in [56,84,112]:
   for tp in [300,500,700]:
    sc=Scenario(f'grid_{sp}_{dte}_{tp}',strike_pct=sp,dte=dte,tp_pct=tp);r,_,_=run_universe(data,UNSEEN,'2023-08-06','2026-08-05',sc);grid.append({**r,'strike_pct':sp,'dte':dte,'tp_pct':tp})
 pd.DataFrame(grid).sort_values('profit',ascending=False).to_csv(OUT/'unseen_parameter_neighborhood.csv',index=False)
 # Frozen annual slices on unseen long universe.
 years=[]
 for y in range(2010,2026):
  en=f'{y}-12-31';st=f'{y}-01-01';r,_,_=run_universe(data,UNSEEN,st,en,Scenario(f'year_{y}'));years.append(r)
 pd.DataFrame(years).to_csv(OUT/'unseen_annual_results.csv',index=False)
 pd.DataFrame(results).to_csv(OUT/'falsification_tests.csv',index=False);pd.concat(symbol_rows).to_csv(OUT/'symbol_results.csv',index=False);pd.concat(ledgers,ignore_index=True).to_csv(OUT/'frozen_test_ledgers.csv',index=False)
 # Mechanical evidence summary; readiness score is assigned in the audit report after code-review findings.
 rmap={r['test']:r for r in results};g=pd.DataFrame(grid);base=float(g[(g.strike_pct==10)&(g.dte==84)&(g.tp_pct==500)].profit.iloc[0]);neighbor_positive=int((g.profit>0).sum());annual=pd.DataFrame(years)
 evidence={'frozen_parameters':FROZEN,'current_mature':rmap['current_mature'],'unseen_recent':rmap['unseen_recent'],'unseen_predevelopment':rmap['unseen_predevelopment'],'entry_day_positive_count':sum(r['profit']>0 for r in results if r['test'].startswith('entry_day_')),'entry_day_test_count':5,'stress_positive_count':sum(r['profit']>0 for r in results if r['test'] in {s.name for s in stress}),'stress_test_count':len(stress),'nearby_grid_positive_count':neighbor_positive,'nearby_grid_count':len(g),'frozen_rank_in_nearby_grid':int(g.profit.rank(ascending=False,method='min')[g.index[(g.strike_pct==10)&(g.dte==84)&(g.tp_pct==500)][0]]),'unseen_positive_years':int((annual.profit>0).sum()),'unseen_years_tested':len(annual),'notes':['All tests still use synthetic options.','Mature-only entries require full DTE before the period end.','Unseen universe was not used in the original crash-grid selection.']}
 (OUT/'evidence_summary.json').write_text(json.dumps(evidence,indent=2,default=str));print(json.dumps(evidence,indent=2,default=str))
if __name__=='__main__':main()
