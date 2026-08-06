#!/usr/bin/env python
"""Synthetic weekly-call stress test through dot-com, GFC, and COVID crashes."""
import math,time
from pathlib import Path
import pandas as pd,requests
TICKERS=['AAPL','AMZN','MSFT','NVDA','CSCO']
WINDOWS={'Dot-com crash':('1999-12-10','2002-10-09'),'Housing/GFC crash':('2007-07-09','2009-03-09'),'COVID crash':('2019-11-19','2020-03-23')}
def N(x):return .5*(1+math.erf(x/math.sqrt(2)))
def call(s,k,t,v,r=.03):
 if t<=0:return max(s-k,0)
 d1=(math.log(s/k)+(r+.5*v*v)*t)/(v*math.sqrt(t));d2=d1-v*math.sqrt(t);return s*N(d1)-k*math.exp(-r*t)*N(d2)
def fetch(sym):
 p=Path(f'data_cache/crash_{sym}_1d.csv')
 if p.exists():return pd.read_csv(p,index_col=0,parse_dates=True)
 u=f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1=915148800&period2=1770000000&interval=1d&events=div%2Csplits&includeAdjustedClose=true';j=requests.get(u,headers={'User-Agent':'Mozilla/5.0'},timeout=30).json()['chart']['result'][0];q=j['indicators']['quote'][0];adj=j['indicators']['adjclose'][0]['adjclose'];x=pd.DataFrame(q,index=pd.to_datetime(j['timestamp'],unit='s',utc=True).tz_convert('US/Eastern').tz_localize(None));x['AdjClose']=adj;factor=x.AdjClose/x.close
 for c in ['open','high','low','close']:x[c.title()]=x[c]*factor
 x=x[['Open','High','Low','Close']].dropna();return x
def sim(sym,d,start,end):
 x=d[(d.index>=start)&(d.index<=pd.Timestamp(end)+pd.Timedelta(days=28))].copy();trade_days=x[x.index<=end].copy();trade_days['week']=trade_days.index.to_period('W-MON');entries=trade_days.groupby('week').head(1);rv=d.Close.pct_change().rolling(20).std()*math.sqrt(252);led=[]
 for ed,r in entries.iterrows():
  s=float(r.Close);v=float(rv.loc[ed]) if pd.notna(rv.loc[ed]) else .60;v=min(max(v,.25),1.75);k=round(s*1.05,2);ep=call(s,k,28/365,v);contracts=math.floor(500/(ep*100))
  if contracts<1:led.append([sym,ed,s,k,ep,0,None,0,'SKIP']);continue
  fut=x[(x.index>ed)&(x.index<=ed+pd.Timedelta(days=28))];ev=None;xd=None;reason='EXPIRY'
  for dt,z in fut.iterrows():
   rem=max((ed+pd.Timedelta(days=28)-dt).days,0)/365;hv=call(float(z.High),k,rem,v)
   if hv>=ep*1.95:ev=ep*1.95;xd=dt;reason='TARGET_95';break
  if ev is None:
   xd=fut.index[-1] if len(fut) else ed;ev=max(float(fut.iloc[-1].Close)-k,0) if len(fut) else 0
  led.append([sym,ed,s,k,ep,contracts,xd,(ev-ep)*100*contracts,reason])
 return pd.DataFrame(led,columns=['symbol','entry_date','spot','strike','entry_option_price','contracts','exit_date','pnl','reason'])
def main():
 data={s:fetch(s) for s in TICKERS};rows=[];allx=[]
 for crash,(st,en) in WINDOWS.items():
  for s in TICKERS:
   x=sim(s,data[s],st,en);x['crash']=crash;allx.append(x);e=x[x.contracts>0];prem=float((e.entry_option_price*e.contracts*100).sum());rows.append([crash,s,st,en,len(e),int((e.pnl>0).sum()),int((e.pnl<=0).sum()),float((e.pnl>0).mean()*100),float(e.pnl.sum()),prem,float(e.pnl.sum()/prem*100)])
 out=Path('backtest_results/crash_weekly_options_top5');out.mkdir(parents=True,exist_ok=True);r=pd.DataFrame(rows,columns=['crash','symbol','start','end','executed','wins','losses','win_rate_pct','profit','premium_deployed','profit_on_premium_pct']);r.to_csv(out/'results.csv',index=False);pd.concat(allx).to_csv(out/'all_trades.csv',index=False);agg=r.groupby('crash').agg(profit=('profit','sum'),executed=('executed','sum'),wins=('wins','sum'),losses=('losses','sum'),premium_deployed=('premium_deployed','sum')).reset_index();agg['win_rate_pct']=agg.wins/agg.executed*100;agg['profit_on_premium_pct']=agg.profit/agg.premium_deployed*100;agg.to_csv(out/'crash_summary.csv',index=False);print(agg.to_string(index=False));print(r.to_string(index=False))
if __name__=='__main__':main()
