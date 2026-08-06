#!/usr/bin/env python
"""Grid-search crash-resilient weekly calls across strike, DTE, and TP."""
import math,time,os
from pathlib import Path
import pandas as pd
from stress_test_weekly_options_crashes import TICKERS,WINDOWS,call,fetch
STRIKES=[10,12.5,15,17.5,20];DTES=[28,56,84,112,140,168];TPS=list(range(50,501,50))
def prep(d,start,end):
 x=d[(d.index>=start)&(d.index<=pd.Timestamp(end)+pd.Timedelta(days=180))].copy();td=x[x.index<=end].copy();td['week']=td.index.to_period('W-MON');entries=td.groupby('week').head(1);rv=d.Close.pct_change().rolling(20).std()*math.sqrt(252);return x,entries,rv
def sim(x,entries,rv,strike_pct,dte,tp,ledger=False):
 pause_until=pd.Timestamp.min;checks=[];profit=0.;wins=losses=executed=paused=triggers=0;premium=0.;log=[]
 for ed,r in entries.iterrows():
  for q in checks:
   if not q['done'] and ed>=q['date']:
    q['done']=True
    if q['trigger']:
     pause_until=max(pause_until,q['date']+pd.Timedelta(weeks=6));triggers+=1
  if ed<pause_until:
   paused+=1
   if ledger:log.append([ed,float(r.Close),None,None,0,None,0,'PAUSED'])
   continue
  s=float(r.Close);v=float(rv.loc[ed]) if pd.notna(rv.loc[ed]) else .60;v=min(max(v,.25),1.75);k=round(s*(1+strike_pct/100),2);ep=call(s,k,dte/365,v,.03);n=math.floor(500/(ep*100))
  if n<1:
   if ledger:log.append([ed,s,k,ep,0,None,0,'SKIP_PREMIUM'])
   continue
  expiry=ed+pd.Timedelta(days=dte);fut=x[(x.index>ed)&(x.index<=expiry)];ev=None;xd=None;reason='EXPIRY'
  for dt,z in fut.iterrows():
   rem=max((expiry-dt).days,0)/365;hv=call(float(z.High),k,rem,v,.03)
   if hv>=ep*(1+tp/100):ev=ep*(1+tp/100);xd=dt;reason=f'TARGET_{tp}';break
  if ev is None:
   xd=fut.index[-1] if len(fut) else ed;ev=max(float(fut.iloc[-1].Close)-k,0) if len(fut) else 0
  pnl=(ev-ep)*100*n;profit+=pnl;premium+=ep*100*n;executed+=1;wins+=pnl>0;losses+=pnl<=0
  check_date=ed+pd.Timedelta(days=21)
  if xd>=check_date:
   dates=x.index[x.index>=check_date]
   if len(dates):
    cd=dates[0];cv=call(float(x.loc[cd].Close),k,max((expiry-cd).days,0)/365,v,.03);checks.append({'date':cd,'trigger':cv<=ep*.5,'done':False})
  if ledger:log.append([ed,s,k,ep,n,xd,pnl,reason])
 return {'profit':profit,'executed':executed,'wins':wins,'losses':losses,'win_rate_pct':wins/executed*100 if executed else 0,'premium':premium,'paused':paused,'triggers':triggers,'ledger':log}
def main():
 data={s:fetch(s) for s in TICKERS};prepared={(c,s):prep(data[s],st,en) for c,(st,en) in WINDOWS.items() for s in TICKERS};rows=[];best=None
 for sp in ([float(os.environ['STRIKE_ONLY'])] if os.environ.get('STRIKE_ONLY') else STRIKES):
  for dte in ([int(os.environ['DTE_ONLY'])] if os.environ.get('DTE_ONLY') else DTES):
   for tp in TPS:
    total={'profit':0,'executed':0,'wins':0,'losses':0,'premium':0,'paused':0,'triggers':0};by={}
    for c in WINDOWS:
     cp=0
     for s in TICKERS:
      r=sim(*prepared[(c,s)],sp,dte,tp)
      for k in total:total[k]+=r[k]
      cp+=r['profit']
     by[c]=cp
    row=[sp,dte,tp,total['profit'],total['executed'],total['wins'],total['losses'],total['wins']/total['executed']*100,total['premium'],total['profit']/total['premium']*100,total['paused'],total['triggers'],by['Dot-com crash'],by['Housing/GFC crash'],by['COVID crash']];rows.append(row)
    if best is None or total['profit']>best[0]:best=(total['profit'],sp,dte,tp)
 out=Path('backtest_results/crash_option_variable_grid');out.mkdir(parents=True,exist_ok=True);cols=['strike_otm_pct','dte_days','tp_pct','total_profit','executed','wins','losses','win_rate_pct','premium_deployed','profit_on_premium_pct','paused_entries','pause_triggers','dotcom_profit','gfc_profit','covid_profit'];res=pd.DataFrame(rows,columns=cols).sort_values('total_profit',ascending=False);suffix=(f"_dte{os.environ['DTE_ONLY']}" if os.environ.get('DTE_ONLY') else '')+(f"_strike{os.environ['STRIKE_ONLY'].replace('.','p')}" if os.environ.get('STRIKE_ONLY') else '');res.to_csv(out/f'all_combinations{suffix}.csv',index=False);res.head(20).to_csv(out/f'top_20{suffix}.csv',index=False)
 if os.environ.get('DTE_ONLY'):
  print(res.head(5).to_string(index=False));return
 # detailed best ledger
 logs=[]
 for c in WINDOWS:
  for s in TICKERS:
   r=sim(*prepared[(c,s)],best[1],best[2],best[3],True)
   z=pd.DataFrame(r['ledger'],columns=['entry_date','spot','strike','entry_option_price','contracts','exit_date','pnl','reason']);z['crash']=c;z['symbol']=s;logs.append(z)
 pd.concat(logs).to_csv(out/'best_ledger.csv',index=False);print(res.head(20).to_string(index=False));print('BEST',best)
if __name__=='__main__':main()
