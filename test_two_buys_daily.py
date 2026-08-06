#!/usr/bin/env python
import pandas as pd
from pathlib import Path
from optimize_kitty_strategy import PAIRS,stitch

def run(data,wait,tp=29,slip=5):
 cash=100000.;pos={};tr=[];curve=[];dates=sorted(set().union(*(set(d.index) for d in data.values())));closes={s:d.Close.reindex(dates).ffill() for s,d in data.items()}
 class P:
  def __init__(self,dt):self.qty=0.;self.cost=0.;self.entries=0;self.last_i=-999;self.opened=str(dt)
 for i,dt in enumerate(dates):
  for s,p in list(pos.items()):
   if dt not in data[s].index:continue
   r=data[s].loc[dt];target=p.cost/p.qty*(1+tp/100)
   if r.High>=target:
    fill=target*(1-slip/10000);pro=p.qty*fill;cash+=pro;tr.append([dt,s,'EXIT',p.qty,fill,pro-p.cost,p.entries]);del pos[s]
  equity=cash+sum(p.qty*float(closes[s].loc[dt]) for s,p in pos.items());elig=[]
  for s,d in data.items():
   if dt in d.index:
    r=d.loc[dt]
    if r.Close<r.Open:elig.append((float(r.Close/r.Open-1),s,float(r.Close)))
  bought=0
  for drop,s,px in sorted(elig):
   if bought>=2:break
   p=pos.get(s)
   if p is not None and (p.entries>=4 or i-p.last_i<wait):continue
   order=equity*.0125;fill=px*(1+slip/10000);qty=order/fill
   if order>cash:continue
   cash-=order
   if p is None:p=P(dt);pos[s]=p
   p.qty+=qty;p.cost+=order;p.entries+=1;p.last_i=i;tr.append([dt,s,'BUY',qty,fill,0.,p.entries]);bought+=1
  equity=cash+sum(p.qty*float(closes[s].loc[dt]) for s,p in pos.items());curve.append([dt,equity])
 eq=pd.DataFrame(curve,columns=['date','equity']).set_index('date');td=pd.DataFrame(tr,columns=['date','symbol','side','qty','price','pnl','entries']);final=float(eq.iloc[-1].equity);dd=float((eq.equity/eq.equity.cummax()-1).min())
 return {'wait_days':wait,'final':final,'return_pct':(final/100000-1)*100,'max_dd_pct':dd*100,'orders':len(td),'buys':int((td.side=='BUY').sum()),'exits':int((td.side=='EXIT').sum()),'open':len(pos)},td,eq

def main():
 data={e:stitch(e,u)[0] for e,u in PAIRS.items()};out=Path('backtest_results/kitty_two_buys_daily');out.mkdir(parents=True,exist_ok=True);rows=[]
 for w in range(1,6):
  s,t,e=run(data,w);rows.append(s);t.to_csv(out/f'wait{w}_orders.csv',index=False);e.to_csv(out/f'wait{w}_equity.csv')
 r=pd.DataFrame(rows);r.to_csv(out/'comparison.csv',index=False);print(r.to_string(index=False))
if __name__=='__main__':main()
