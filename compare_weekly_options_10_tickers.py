#!/usr/bin/env python
"""Compare weekly $5-OTM 28-DTE synthetic call strategy across ten requested tickers."""
import math,json
from pathlib import Path
import pandas as pd
from validate_best_2y_hourly import fetch
TICKERS=['METU','AAPU','MSFU','NFLX','PLTR','IBX','NVDU','GGLL','AMZU','TSLT']
def N(x):return .5*(1+math.erf(x/math.sqrt(2)))
def call(s,k,t,v,r=.043):
 if t<=0:return max(s-k,0)
 v=max(v,.05);d1=(math.log(s/k)+(r+.5*v*v)*t)/(v*math.sqrt(t));d2=d1-v*math.sqrt(t);return s*N(d1)-k*math.exp(-r*t)*N(d2)
def simulate(sym,eq):
 d=fetch(sym);daily=d.groupby(d.index.date).agg(Open=('Open','first'),High=('High','max'),Low=('Low','min'),Close=('Close','last'));daily.index=pd.to_datetime(daily.index);daily['rv']=daily.Close.pct_change().rolling(20).std()*math.sqrt(252);daily.rv=daily.rv.clip(.25,1.75).fillna(.80);daily['week']=daily.index.to_period('W-MON');entries=daily.groupby('week').head(1);ledger=[]
 for ed,r in entries.iterrows():
  spot=float(r.Close);vol=float(r.rv);strike=math.ceil(spot)+5;entry=call(spot,strike,28/365,vol);acct=float(eq.iloc[(eq.timestamp-pd.Timestamp(ed,tz='US/Eastern')).abs().argsort()[:1]].equity.iloc[0]);budget=acct*.005;contracts=math.floor(budget/(entry*100))
  if contracts<1:ledger.append([sym,ed,spot,strike,entry,budget,0,None,None,0,'SKIP_PREMIUM']);continue
  fut=daily[(daily.index>ed)&(daily.index<=ed+pd.Timedelta(days=28))];exitv=None;exitd=None;reason='EXPIRY'
  for dt,rr in fut.iterrows():
   rem=max((ed+pd.Timedelta(days=28)-dt).days,0)/365;hv=call(float(rr.High),strike,rem,vol)
   if hv>=entry*1.95:exitv=entry*1.95;exitd=dt;reason='TARGET_95';break
  if exitv is None:
   if len(fut):exitd=fut.index[-1];exitv=max(float(fut.iloc[-1].Close)-strike,0)
   else:exitd=ed;exitv=0
  ledger.append([sym,ed,spot,strike,entry,budget,contracts,exitd,exitv,(exitv-entry)*100*contracts,reason])
 x=pd.DataFrame(ledger,columns=['symbol','entry_date','spot','strike','entry_option_price','budget','contracts','exit_date','exit_option_price','pnl','reason']);exe=x[x.contracts>0];prem=float((exe.entry_option_price*exe.contracts*100).sum());return x,{'symbol':sym,'start':str(daily.index.min().date()),'end':str(daily.index.max().date()),'weeks':len(entries),'executed':len(exe),'skipped':int((x.contracts==0).sum()),'wins':int((exe.pnl>0).sum()),'losses':int((exe.pnl<=0).sum()),'win_rate_pct':float((exe.pnl>0).mean()*100) if len(exe) else 0,'premium_deployed':prem,'option_profit':float(exe.pnl.sum()),'profit_on_deployed_pct':float(exe.pnl.sum()/prem*100) if prem else 0}
def main():
 eq=pd.read_csv('backtest_results/kitty_2_5pct_tp50_2y_hourly/equity_curve.csv');eq.timestamp=pd.to_datetime(eq.timestamp,utc=True).dt.tz_convert('US/Eastern');out=Path('backtest_results/weekly_options_10_tickers');out.mkdir(parents=True,exist_ok=True);summ=[];led=[]
 for s in TICKERS:
  x,r=simulate(s,eq);summ.append(r);led.append(x);print(s,r['option_profit'])
 res=pd.DataFrame(summ).sort_values('option_profit',ascending=False);res['rank']=range(1,len(res)+1);res.to_csv(out/'ranking.csv',index=False);pd.concat(led).to_csv(out/'all_ledgers.csv',index=False);res.head(5).to_csv(out/'top_5.csv',index=False);(out/'summary.json').write_text(json.dumps({'criteria':'weekly first session; 0.5% equity; $5 OTM; 28 DTE; +95% TP; synthetic prices','top_5':res.head(5).symbol.tolist()},indent=2));print(res.to_string(index=False))
if __name__=='__main__':main()
