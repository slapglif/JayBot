#!/usr/bin/env python
import requests,json,math
from pathlib import Path
from dataclasses import dataclass
import pandas as pd,numpy as np
END='2026-08-06';START='2023-08-05'
PAIRS={'NVDU':'NVDA','AAPU':'AAPL','MSTU':'MSFT','METU':'META','AMZU':'AMZN','NFXL':'NFLX','PLTR':'PLTR','GGLL':'GOOGL','TSMX':'TSM','IBX':'IBM'}

def fetch(t):
 p=Path('data_cache')/f'{t}_{START}_{END}_1d.csv'
 if p.exists():return pd.read_csv(p,index_col=0,parse_dates=True)
 u=f'https://query1.finance.yahoo.com/v8/finance/chart/{t}';p1=int(pd.Timestamp(START,tz='UTC').timestamp());p2=int(pd.Timestamp(END,tz='UTC').timestamp())
 j=requests.get(u,params={'period1':p1,'period2':p2,'interval':'1d','events':'div,splits'},headers={'User-Agent':'Mozilla/5.0'},timeout=60).json()['chart']['result']
 if not j:return pd.DataFrame()
 j=j[0];q=j['indicators']['quote'][0];d=pd.DataFrame(q,index=pd.to_datetime(j['timestamp'],unit='s',utc=True).tz_convert('US/Eastern'))
 d=d.rename(columns={'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'}).dropna(subset=['Open','High','Low','Close']);d.to_csv(p);return d

def stitch(etf,under):
 e,u=fetch(etf),fetch(under)
 if etf==under:return u.copy(),None
 first=e.index.min() if len(e) else None
 dates=u.index.union(e.index).sort_values();rows=[];level=100.;prev_src=None
 for dt in dates:
  src=e if first is not None and dt>=first and dt in e.index else u
  if dt not in src.index:continue
  r=src.loc[dt];ret=float(r.Close/r.Open-1);rng_hi=float(r.High/r.Open);rng_lo=float(r.Low/r.Open)
  op=level;cl=op*(1+ret);hi=op*rng_hi;lo=op*rng_lo;rows.append((dt,op,hi,lo,cl,ret,'ETF' if src is e else 'UNDERLYING'));level=cl
 return pd.DataFrame(rows,columns=['Date','Open','High','Low','Close','drop','source']).set_index('Date'),first

@dataclass
class Pos: qty:float=0.;cost:float=0.;entries:int=0;last_i:int=-999;opened:str=''
def test(data,wait,tp,slip_bps=5):
 cash=100000.;pos={};tr=[];curve=[];dates=sorted(set().union(*(set(d.index) for d in data.values())));closes={s:d.Close.reindex(dates).ffill() for s,d in data.items()}
 for i,dt in enumerate(dates):
  # exits first, using daily high; conservative target minus sell slippage
  for s,p in list(pos.items()):
   if dt not in data[s].index:continue
   r=data[s].loc[dt];target=p.cost/p.qty*(1+tp/100)
   if r.High>=target:
    fill=target*(1-slip_bps/10000);pro=p.qty*fill;cash+=pro;tr.append([dt,s,'EXIT',p.qty,fill,pro-p.cost,p.entries]);del pos[s]
  mv=sum(p.qty*float(closes[s].loc[dt]) for s,p in pos.items());equity=cash+mv
  elig=[]
  for s,d in data.items():
   if dt in d.index:
    r=d.loc[dt]
    if r.Close<r.Open:elig.append((float(r.Close/r.Open-1),s,float(r.Close)))
  if elig:
   _,s,px=min(elig);p=pos.get(s)
   if p is None or (p.entries<4 and i-p.last_i>=wait):
    order=equity*.0125;fill=px*(1+slip_bps/10000);qty=order/fill
    if order<=cash:
     cash-=order
     if p is None:p=Pos(opened=str(dt));pos[s]=p
     p.qty+=qty;p.cost+=order;p.entries+=1;p.last_i=i;tr.append([dt,s,'BUY',qty,fill,0.,p.entries])
  mv=sum(p.qty*float(closes[s].loc[dt]) for s,p in pos.items());curve.append([dt,cash+mv])
 eq=pd.DataFrame(curve,columns=['date','equity']).set_index('date');td=pd.DataFrame(tr,columns=['date','symbol','side','qty','price','pnl','entries'])
 final=float(eq.iloc[-1].equity);dd=float((eq.equity/eq.equity.cummax()-1).min());ret=final/100000-1;cagr=(final/100000)**(1/3)-1
 attr=[]
 for s in data:
  realized=float(td[(td.symbol==s)&(td.side=='EXIT')].pnl.sum()) if len(td) else 0
  p=pos.get(s);unreal=0
  if p:unreal=p.qty*float(data[s].iloc[-1].Close)-p.cost
  attr.append([s,realized,unreal,realized+unreal,int((td[(td.symbol==s)&(td.side=='BUY')]).shape[0])])
 return {'wait':wait,'tp':tp,'final':final,'return_pct':ret*100,'cagr_pct':cagr*100,'max_dd_pct':dd*100,'orders':len(td),'exits':int((td.side=='EXIT').sum()) if len(td) else 0,'open':len(pos)},td,eq,pd.DataFrame(attr,columns=['symbol','realized','unrealized','total_pnl','buys'])

def main():
 data={};inc={}
 for e,u in PAIRS.items():data[e],first=stitch(e,u);inc[e]=str(first.date()) if first is not None else None
 results=[]
 for w in [1,2,3]:
  for tp in range(10,31):results.append(test(data,w,tp)[0])
 rank=pd.DataFrame(results).sort_values(['final','max_dd_pct'],ascending=[False,False]).reset_index(drop=True);out=Path('backtest_results/kitty_3y_optimizer');out.mkdir(parents=True,exist_ok=True);rank.to_csv(out/'all_63_combinations.csv',index=False);rank.head(10).to_csv(out/'top_10_samples.csv',index=False)
 best=rank.iloc[0];stats,tr,eq,attr=test(data,int(best.wait),int(best.tp));tr.assign(order_date_et=pd.to_datetime(tr.date,utc=True).dt.tz_convert('US/Eastern').dt.strftime('%Y-%m-%d')).to_csv(out/'best_orders_with_dates.csv',index=False);eq.to_csv(out/'best_equity_curve.csv');attr.sort_values('total_pnl',ascending=False).to_csv(out/'symbol_attribution.csv',index=False)
 (out/'summary.json').write_text(json.dumps({'best':stats,'inception_switches':inc,'method':'Daily real-data proxy; underlying before ETF inception, ETF returns after inception; continuous return index.'},indent=2));print(rank.head(10).to_string(index=False));print('\nATTRIBUTION\n',attr.sort_values('total_pnl',ascending=False).to_string(index=False));print('\nINCEPTIONS',inc)
if __name__=='__main__':main()
