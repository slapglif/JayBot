#!/usr/bin/env python
"""Crash option stress test with 3-week/-50% trigger and 6-week per-symbol pause."""
from pathlib import Path
import math,pandas as pd
from stress_test_weekly_options_crashes import TICKERS,WINDOWS,N,call,fetch

def sim(sym,d,start,end):
 x=d[(d.index>=start)&(d.index<=pd.Timestamp(end)+pd.Timedelta(days=42))].copy();trade_days=x[x.index<=end].copy();trade_days['week']=trade_days.index.to_period('W-MON');entries=trade_days.groupby('week').head(1);rv=d.Close.pct_change().rolling(20).std()*math.sqrt(252);active_checks=[];pause_until=pd.Timestamp.min;led=[];pauses=[]
 for ed,r in entries.iterrows():
  # Evaluate every prior contract once on the first session at/after age 21 days.
  for q in active_checks:
   if not q['checked'] and ed>=q['check_date']:
    dates=x.index[x.index>=q['check_date']]
    if len(dates):
     cd=dates[0];spot=float(x.loc[cd].Close);rem=max((q['expiry']-cd).days,0)/365;val=call(spot,q['strike'],rem,q['vol'])
     q['checked']=True;q['check_value']=val
     if val<=q['entry']*.5:
      new_pause=cd+pd.Timedelta(weeks=6);pause_until=max(pause_until,new_pause);pauses.append([sym,cd,q['entry_date'],q['entry'],val,(val/q['entry']-1)*100,pause_until])
  if ed<pause_until:
   led.append([sym,ed,float(r.Close),None,None,0,None,0,'PAUSED_6W']);continue
  s=float(r.Close);v=float(rv.loc[ed]) if pd.notna(rv.loc[ed]) else .60;v=min(max(v,.25),1.75);k=round(s*1.05,2);ep=call(s,k,28/365,v);contracts=math.floor(500/(ep*100))
  if contracts<1:led.append([sym,ed,s,k,ep,0,None,0,'SKIP_PREMIUM']);continue
  expiry=ed+pd.Timedelta(days=28);active_checks.append({'entry_date':ed,'entry':ep,'strike':k,'vol':v,'check_date':ed+pd.Timedelta(days=21),'expiry':expiry,'checked':False});fut=x[(x.index>ed)&(x.index<=expiry)];ev=None;xd=None;reason='EXPIRY'
  for dt,z in fut.iterrows():
   rem=max((expiry-dt).days,0)/365;hv=call(float(z.High),k,rem,v)
   if hv>=ep*1.95:ev=ep*1.95;xd=dt;reason='TARGET_95';break
  if ev is None:
   xd=fut.index[-1] if len(fut) else ed;ev=max(float(fut.iloc[-1].Close)-k,0) if len(fut) else 0
  led.append([sym,ed,s,k,ep,contracts,xd,(ev-ep)*100*contracts,reason])
 cols=['symbol','entry_date','spot','strike','entry_option_price','contracts','exit_date','pnl','reason'];return pd.DataFrame(led,columns=cols),pd.DataFrame(pauses,columns=['symbol','trigger_date','losing_entry_date','entry_option_price','week3_value','decline_pct','pause_until'])
def main():
 data={s:fetch(s) for s in TICKERS};rows=[];allx=[];allp=[]
 for crash,(st,en) in WINDOWS.items():
  for s in TICKERS:
   x,p=sim(s,data[s],st,en);x['crash']=crash;p['crash']=crash;allx.append(x);allp.append(p);e=x[x.contracts>0];prem=float((e.entry_option_price*e.contracts*100).sum());rows.append([crash,s,len(e),int((e.pnl>0).sum()),int((e.pnl<=0).sum()),float((e.pnl>0).mean()*100) if len(e) else 0,float(e.pnl.sum()),prem,int((x.reason=='PAUSED_6W').sum()),len(p)])
 out=Path('backtest_results/crash_options_3w50_6w_pause');out.mkdir(parents=True,exist_ok=True);r=pd.DataFrame(rows,columns=['crash','symbol','executed','wins','losses','win_rate_pct','profit','premium_deployed','paused_weekly_entries','pause_triggers']);r.to_csv(out/'results.csv',index=False);pd.concat(allx).to_csv(out/'all_trades.csv',index=False);pd.concat(allp).to_csv(out/'pause_events.csv',index=False);agg=r.groupby('crash').agg(profit=('profit','sum'),executed=('executed','sum'),wins=('wins','sum'),losses=('losses','sum'),premium_deployed=('premium_deployed','sum'),paused_weekly_entries=('paused_weekly_entries','sum'),pause_triggers=('pause_triggers','sum')).reset_index();agg['win_rate_pct']=agg.wins/agg.executed*100;agg.to_csv(out/'crash_summary.csv',index=False);print(agg.to_string(index=False));print(r.to_string(index=False))
if __name__=='__main__':main()
