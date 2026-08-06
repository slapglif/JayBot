#!/usr/bin/env python
"""Two-year hourly validation of best discovered strategy."""
import requests,json
from pathlib import Path
from dataclasses import dataclass
import pandas as pd,numpy as np
START='2024-08-07';END='2026-08-06'
PAIRS={'NVDU':'NVDA','AAPU':'AAPL','MSTU':'MSFT','METU':'META','AMZU':'AMZN','NFXL':'NFLX','PLTR':'PLTR','GGLL':'GOOGL','TSMX':'TSM','IBX':'IBM'}
def fetch(t):
 p=Path('data_cache')/f'{t}_{START}_{END}_1h.csv'
 if p.exists():
  d=pd.read_csv(p,index_col=0,parse_dates=True);d.index=pd.to_datetime(d.index,utc=True).tz_convert('US/Eastern');return d
 p1=int(pd.Timestamp(START,tz='UTC').timestamp());p2=int(pd.Timestamp(END,tz='UTC').timestamp());u=f'https://query1.finance.yahoo.com/v8/finance/chart/{t}'
 r=requests.get(u,params={'period1':p1,'period2':p2,'interval':'1h','events':'div,splits'},headers={'User-Agent':'Mozilla/5.0'},timeout=60).json()['chart']['result']
 if not r:return pd.DataFrame()
 j=r[0];q=j['indicators']['quote'][0];d=pd.DataFrame(q,index=pd.to_datetime(j['timestamp'],unit='s',utc=True).tz_convert('US/Eastern')).rename(columns={'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'}).dropna(subset=['Open','High','Low','Close']);d=d.between_time('09:30','15:59');d.to_csv(p);return d
def stitch(etf,under):
 e,u=fetch(etf),fetch(under);first=e.index.min() if etf!=under and len(e) else None;dates=u.index.union(e.index).sort_values();rows=[];level=100.;prev={}
 for dt in dates:
  src=e if first is not None and dt>=first and dt in e.index else u;tag='ETF' if src is e else 'UNDERLYING'
  if dt not in src.index:continue
  r=src.loc[dt];prior=prev.get(tag)
  if prior is None:so=level;sc=level*float(r.Close/r.Open);sh=level*float(r.High/r.Open);sl=level*float(r.Low/r.Open)
  else:so=level*float(r.Open/prior);sc=level*float(r.Close/prior);sh=level*float(r.High/prior);sl=level*float(r.Low/prior)
  rows.append([dt,so,sh,sl,sc,tag]);level=sc;prev[tag]=float(r.Close)
  # update previous close for the other source when it has a simultaneous bar
  if dt in e.index:prev['ETF']=float(e.loc[dt].Close)
  if dt in u.index:prev['UNDERLYING']=float(u.loc[dt].Close)
 d=pd.DataFrame(rows,columns=['timestamp','Open','High','Low','Close','source']).set_index('timestamp');d['session']=d.index.date.astype(str);d['day_open']=d.groupby('session').Open.transform('first');return d,first
@dataclass
class P: qty:float=0.;cost:float=0.;entries:int=0;last_session:int=-999;opened:str=''
def run(data,tp=29,wait=1,slip=5):
 decisions=sorted(set().union(*(set(d[(d.index.hour==13)&(d.index.minute==30)].index) for d in data.values())));sessions=sorted({x.date().isoformat() for x in decisions});sid={s:i for i,s in enumerate(sessions)};cash=100000.;pos={};tr=[];curve=[];prev=None
 for dt in decisions:
  sn=sid[dt.date().isoformat()]
  for s,p in list(pos.items()):
   bars=data[s][(data[s].index<=dt)&((data[s].index>prev) if prev is not None else True)];target=p.cost/p.qty*(1+tp/100)
   if len(bars) and bars.High.max()>=target:
    fill=target*(1-slip/10000);pro=p.qty*fill;cash+=pro;tr.append([dt,s,'EXIT',p.qty,fill,pro-p.cost,p.entries]);del pos[s]
  equity=cash+sum(p.qty*float(data[s][data[s].index<=dt].iloc[-1].Close) for s,p in pos.items());elig=[]
  for s,d in data.items():
   if dt in d.index:
    r=d.loc[dt]
    if r.Close<r.day_open:elig.append((float(r.Close/r.day_open-1),s,float(r.Close)))
  bought=0
  for drop,s,px in sorted(elig):
   if bought>=2:break
   p=pos.get(s)
   if p is not None and (p.entries>=4 or sn-p.last_session<wait):continue
   order=equity*.0125;fill=px*(1+slip/10000);qty=order/fill
   if order>cash:continue
   cash-=order
   if p is None:p=P(opened=str(dt));pos[s]=p
   p.qty+=qty;p.cost+=order;p.entries+=1;p.last_session=sn;tr.append([dt,s,'BUY',qty,fill,0.,p.entries]);bought+=1
  equity=cash+sum(p.qty*float(data[s][data[s].index<=dt].iloc[-1].Close) for s,p in pos.items());curve.append([dt,equity,cash,len(pos)]);prev=dt
 eq=pd.DataFrame(curve,columns=['timestamp','equity','cash','positions']).set_index('timestamp');td=pd.DataFrame(tr,columns=['timestamp','symbol','side','qty','price','pnl','entries']);final=float(eq.iloc[-1].equity);dd=float((eq.equity/eq.equity.cummax()-1).min());years=len(sessions)/252
 stats={'start':sessions[0],'end':sessions[-1],'sessions':len(sessions),'final':final,'return_pct':(final/100000-1)*100,'cagr_pct':((final/100000)**(1/years)-1)*100,'max_dd_pct':dd*100,'orders':len(td),'buys':int((td.side=='BUY').sum()),'exits':int((td.side=='EXIT').sum()),'open':len(pos),'tp':tp,'wait':wait,'purchases_per_day':2}
 return stats,td,eq,pos
def main():
 data={};inc={}
 for e,u in PAIRS.items():data[e],f=stitch(e,u);inc[e]=str(f.date()) if f is not None else None
 s,t,e,p=run(data);out=Path('backtest_results/best_strategy_2y_hourly');out.mkdir(parents=True,exist_ok=True);t.assign(order_date_et=pd.to_datetime(t.timestamp,utc=True).dt.tz_convert('US/Eastern').dt.strftime('%Y-%m-%d')).to_csv(out/'orders_with_dates.csv',index=False);e.to_csv(out/'equity_curve.csv');(out/'summary.json').write_text(json.dumps({'stats':s,'inceptions':inc},indent=2));print(json.dumps(s,indent=2));print('inceptions',inc)
if __name__=='__main__':main()
