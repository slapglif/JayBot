#!/usr/bin/env python
"""Synthetic PLTR call-option overlay; not historical option-chain replay."""
import math,json
from pathlib import Path
import pandas as pd,numpy as np

def N(x):return .5*(1+math.erf(x/math.sqrt(2)))
def call(s,k,t,vol,r=.043):
 if t<=0:return max(s-k,0)
 vol=max(vol,.05);d1=(math.log(s/k)+(r+.5*vol*vol)*t)/(vol*math.sqrt(t));d2=d1-vol*math.sqrt(t);return s*N(d1)-k*math.exp(-r*t)*N(d2)
def main():
 root=Path('backtest_results/best_strategy_2y_hourly');orders=pd.read_csv(root/'orders_with_dates.csv');orders.timestamp=pd.to_datetime(orders.timestamp,utc=True).dt.tz_convert('US/Eastern');sig=orders[(orders.symbol=='PLTR')&(orders.side=='BUY')].copy();sig['month']=sig.timestamp.dt.to_period('M');sig=sig.sort_values('timestamp').groupby('month').first().reset_index()
 d=pd.read_csv('data_cache/PLTR_2024-08-07_2026-08-06_1h.csv',index_col=0,parse_dates=True);d.index=pd.to_datetime(d.index,utc=True).tz_convert('US/Eastern');daily=d.groupby(d.index.date).agg(Open=('Open','first'),High=('High','max'),Low=('Low','min'),Close=('Close','last'));daily.index=pd.to_datetime(daily.index);daily['rv']=daily.Close.pct_change().rolling(20).std()*math.sqrt(252);daily.rv=daily.rv.clip(.35,1.50).fillna(.65)
 eq=pd.read_csv(root/'equity_curve.csv');eq.timestamp=pd.to_datetime(eq.timestamp,utc=True).dt.tz_convert('US/Eastern')
 rows=[];ledgers={}
 for offset in range(3,9):
  pnl=0.;wins=losses=skips=0;ledger=[]
  for _,sg in sig.iterrows():
   day=pd.Timestamp(sg.timestamp.date());avail=daily.index[daily.index<=day]
   if not len(avail):continue
   entry_day=avail[-1];spot=float(daily.loc[entry_day].Close);vol=float(daily.loc[entry_day].rv);strike=math.ceil(spot)+offset;entry=call(spot,strike,28/365,vol);acct=float(eq.iloc[(eq.timestamp-sg.timestamp).abs().argsort()[:1]].equity.iloc[0]);budget=acct*.002;contracts=math.floor(budget/(entry*100))
   if contracts<1:skips+=1;ledger.append([entry_day,offset,spot,strike,vol,entry,budget,0,None,None,0,'SKIP_PREMIUM_TOO_HIGH']);continue
   future=daily[(daily.index>entry_day)&(daily.index<=entry_day+pd.Timedelta(days=28))];exit_val=None;exit_day=None;reason='EXPIRY'
   for dt,r in future.iterrows():
    rem=max((entry_day+pd.Timedelta(days=28)-dt).days,0)/365;high_val=call(float(r.High),strike,rem,vol)
    if high_val>=entry*1.5:exit_val=entry*1.5;exit_day=dt;reason='TARGET_50';break
   if exit_val is None:
    if len(future):exit_day=future.index[-1];exit_val=max(float(future.iloc[-1].Close)-strike,0)
    else:exit_day=entry_day;exit_val=0
   trade=(exit_val-entry)*100*contracts;pnl+=trade
   if trade>0:wins+=1
   else:losses+=1
   ledger.append([entry_day,offset,spot,strike,vol,entry,budget,contracts,exit_day,exit_val,trade,reason])
  rows.append([offset,pnl,wins,losses,skips,wins+losses,(wins/(wins+losses)*100 if wins+losses else 0)])
  ledgers[offset]=pd.DataFrame(ledger,columns=['entry_date','strike_offset_dollars','spot','strike','annualized_vol','entry_option_price','budget','contracts','exit_date','exit_option_price','pnl','reason'])
 out=Path('backtest_results/pltr_option_overlay');out.mkdir(parents=True,exist_ok=True);res=pd.DataFrame(rows,columns=['strike_offset_dollars','option_profit','wins','losses','skipped_budget','executed_trades','win_rate_pct']).sort_values('option_profit',ascending=False);res.to_csv(out/'strike_3_to_8_results.csv',index=False)
 for k,v in ledgers.items():v.to_csv(out/f'offset_{k}_ledger.csv',index=False)
 (out/'summary.json').write_text(json.dumps({'method':'Synthetic Black-Scholes call overlay; first PLTR strategy buy per month; 28 calendar DTE; 20-day realized vol clipped 35%-150%; integer contracts; premium <=0.2% equity; exit +50% or expiry.','results':res.to_dict('records')},indent=2));print(res.to_string(index=False))
if __name__=='__main__':main()
