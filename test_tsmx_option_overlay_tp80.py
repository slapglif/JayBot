#!/usr/bin/env python
"""Synthetic TSMX calls on TP50 share-strategy signals."""
import math,json
from pathlib import Path
import pandas as pd

def N(x):return .5*(1+math.erf(x/math.sqrt(2)))
def call(s,k,t,v,r=.043):
 if t<=0:return max(s-k,0)
 v=max(v,.05);d1=(math.log(s/k)+(r+.5*v*v)*t)/(v*math.sqrt(t));d2=d1-v*math.sqrt(t);return s*N(d1)-k*math.exp(-r*t)*N(d2)
def main():
 root=Path('backtest_results/kitty_2_5pct_tp50_2y_hourly');o=pd.read_csv(root/'orders_with_dates.csv');o.timestamp=pd.to_datetime(o.timestamp,utc=True).dt.tz_convert('US/Eastern');sig=o[(o.symbol=='TSMX')&(o.side=='BUY')].copy();sig['month']=sig.timestamp.dt.to_period('M');sig=sig.sort_values('timestamp').groupby('month',group_keys=False).head(3)
 d=pd.read_csv('data_cache/TSMX_2024-08-07_2026-08-06_1h.csv',index_col=0,parse_dates=True);d.index=pd.to_datetime(d.index,utc=True).tz_convert('US/Eastern');daily=d.groupby(d.index.date).agg(Open=('Open','first'),High=('High','max'),Low=('Low','min'),Close=('Close','last'));daily.index=pd.to_datetime(daily.index);daily['rv']=daily.Close.pct_change().rolling(20).std()*math.sqrt(252);daily.rv=daily.rv.clip(.40,1.75).fillna(.80)
 eq=pd.read_csv(root/'equity_curve.csv');eq.timestamp=pd.to_datetime(eq.timestamp,utc=True).dt.tz_convert('US/Eastern');ledger=[]
 for _,sg in sig.iterrows():
  day=pd.Timestamp(sg.timestamp.date());avail=daily.index[daily.index<=day]
  if not len(avail):continue
  ed=avail[-1];spot=float(daily.loc[ed].Close);vol=float(daily.loc[ed].rv);strike=math.ceil(spot)+5;entry=call(spot,strike,28/365,vol);acct=float(eq.iloc[(eq.timestamp-sg.timestamp).abs().argsort()[:1]].equity.iloc[0]);budget=acct*.002;contracts=math.floor(budget/(entry*100))
  if contracts<1:ledger.append([ed,spot,strike,vol,entry,budget,0,None,None,0,'SKIP_PREMIUM']);continue
  future=daily[(daily.index>ed)&(daily.index<=ed+pd.Timedelta(days=28))];exitv=None;exitd=None;reason='EXPIRY'
  for dt,r in future.iterrows():
   rem=max((ed+pd.Timedelta(days=28)-dt).days,0)/365;hv=call(float(r.High),strike,rem,vol)
   if hv>=entry*1.8:exitv=entry*1.8;exitd=dt;reason='TARGET_80';break
  if exitv is None:
   if len(future):exitd=future.index[-1];exitv=max(float(future.iloc[-1].Close)-strike,0)
   else:exitd=ed;exitv=0
  pnl=(exitv-entry)*100*contracts;ledger.append([ed,spot,strike,vol,entry,budget,contracts,exitd,exitv,pnl,reason])
 out=Path('backtest_results/tsmx_option_overlay_tp80');out.mkdir(parents=True,exist_ok=True);x=pd.DataFrame(ledger,columns=['entry_date','spot','strike','vol','entry_option_price','budget','contracts','exit_date','exit_option_price','pnl','reason']);x.to_csv(out/'ledger.csv',index=False);exe=x[x.contracts>0];summary={'signals':len(x),'executed':len(exe),'skipped':int((x.contracts==0).sum()),'wins':int((exe.pnl>0).sum()),'losses':int((exe.pnl<=0).sum()),'win_rate_pct':float((exe.pnl>0).mean()*100) if len(exe) else 0,'premium_deployed':float((exe.entry_option_price*exe.contracts*100).sum()),'option_profit':float(exe.pnl.sum())};(out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));print(exe.to_string(index=False))
if __name__=='__main__':main()
