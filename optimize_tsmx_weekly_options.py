#!/usr/bin/env python
"""Grid-search weekly TSMX calls: 0.1%-0.5% equity risk, 50%-100% TP."""
import math,json
from pathlib import Path
import pandas as pd

def N(x):return .5*(1+math.erf(x/math.sqrt(2)))
def call(s,k,t,v,r=.043):
 if t<=0:return max(s-k,0)
 v=max(v,.05);d1=(math.log(s/k)+(r+.5*v*v)*t)/(v*math.sqrt(t));d2=d1-v*math.sqrt(t);return s*N(d1)-k*math.exp(-r*t)*N(d2)
def main():
 d=pd.read_csv('data_cache/TSMX_2024-08-07_2026-08-06_1h.csv',index_col=0,parse_dates=True);d.index=pd.to_datetime(d.index,utc=True).tz_convert('US/Eastern');daily=d.groupby(d.index.date).agg(Open=('Open','first'),High=('High','max'),Low=('Low','min'),Close=('Close','last'));daily.index=pd.to_datetime(daily.index);daily['rv']=daily.Close.pct_change().rolling(20).std()*math.sqrt(252);daily.rv=daily.rv.clip(.40,1.75).fillna(.80);daily['week']=daily.index.to_period('W-MON');entries=daily.groupby('week').head(1)
 eq=pd.read_csv('backtest_results/kitty_2_5pct_tp50_2y_hourly/equity_curve.csv');eq.timestamp=pd.to_datetime(eq.timestamp,utc=True).dt.tz_convert('US/Eastern')
 rows=[];best_ledger=None;best_key=None
 for risk_tenths in range(1,6):
  risk=risk_tenths/1000
  for tp in range(50,101,5):
   ledger=[]
   for ed,r in entries.iterrows():
    spot=float(r.Close);vol=float(r.rv);strike=math.ceil(spot)+5;entry=call(spot,strike,28/365,vol);acct=float(eq.iloc[(eq.timestamp-pd.Timestamp(ed,tz='US/Eastern')).abs().argsort()[:1]].equity.iloc[0]);budget=acct*risk;contracts=math.floor(budget/(entry*100))
    if contracts<1:ledger.append([ed,risk*100,tp,spot,strike,entry,budget,0,None,None,0,'SKIP_PREMIUM']);continue
    fut=daily[(daily.index>ed)&(daily.index<=ed+pd.Timedelta(days=28))];exitv=None;exitd=None;reason='EXPIRY'
    for dt,rr in fut.iterrows():
     rem=max((ed+pd.Timedelta(days=28)-dt).days,0)/365;hv=call(float(rr.High),strike,rem,vol)
     if hv>=entry*(1+tp/100):exitv=entry*(1+tp/100);exitd=dt;reason=f'TARGET_{tp}';break
    if exitv is None:
     if len(fut):exitd=fut.index[-1];exitv=max(float(fut.iloc[-1].Close)-strike,0)
     else:exitd=ed;exitv=0
    pnl=(exitv-entry)*100*contracts;ledger.append([ed,risk*100,tp,spot,strike,entry,budget,contracts,exitd,exitv,pnl,reason])
   x=pd.DataFrame(ledger,columns=['entry_date','risk_pct','tp_pct','spot','strike','entry_option_price','budget','contracts','exit_date','exit_option_price','pnl','reason']);exe=x[x.contracts>0];profit=float(exe.pnl.sum());wins=int((exe.pnl>0).sum());losses=int((exe.pnl<=0).sum());premium=float((exe.entry_option_price*exe.contracts*100).sum());max_concurrent=0
   if len(exe):
    for dt in daily.index:max_concurrent=max(max_concurrent,int(((pd.to_datetime(exe.entry_date)<=dt)&(pd.to_datetime(exe.exit_date)>=dt)).sum()))
   rows.append([risk*100,tp,profit,len(exe),wins,losses,int((x.contracts==0).sum()),wins/len(exe)*100 if len(exe) else 0,premium,max_concurrent])
   if best_ledger is None or profit>max(r[2] for r in rows[:-1]):best_ledger=x;best_key=(risk*100,tp)
 out=Path('backtest_results/tsmx_weekly_option_grid');out.mkdir(parents=True,exist_ok=True);res=pd.DataFrame(rows,columns=['risk_pct','tp_pct','option_profit','executed','wins','losses','skipped','win_rate_pct','premium_deployed','max_concurrent']);res=res.sort_values('option_profit',ascending=False);res.to_csv(out/'all_55_combinations.csv',index=False);res.head(10).to_csv(out/'top_10.csv',index=False);best_ledger.to_csv(out/'best_ledger.csv',index=False);(out/'summary.json').write_text(json.dumps({'best_risk_pct':best_key[0],'best_tp_pct':best_key[1],'method':'Weekly first TSMX trading day; $5 OTM; 28 DTE; integer contracts; synthetic Black-Scholes; overlapping positions allowed.'},indent=2));print(res.head(15).to_string(index=False));print('BEST',best_key)
if __name__=='__main__':main()
