#!/usr/bin/env python
"""Separate portfolio-state overlay requested by Kitty; daily-bar proxy."""
import pandas as pd, numpy as np, json
from pathlib import Path
from optimize_kitty_strategy import PAIRS,stitch,test

def variant(data,wait,tp,slip_bps=5):
 cash=100000.;pos={};tr=[];curve=[];dates=sorted(set().union(*(set(d.index) for d in data.values())));closes={s:d.Close.reindex(dates).ffill() for s,d in data.items()}
 pause_until=-1;cooldown_until=-1;profitable_streak=0;events=[]
 class P:
  def __init__(self,dt):self.qty=0.;self.cost=0.;self.entries=0;self.last_i=-999;self.opened=str(dt)
 for i,dt in enumerate(dates):
  for s,p in list(pos.items()):
   if dt not in data[s].index:continue
   r=data[s].loc[dt];target=p.cost/p.qty*(1+tp/100)
   if r.High>=target:
    fill=target*(1-slip_bps/10000);pro=p.qty*fill;cash+=pro;tr.append([dt,s,'EXIT',p.qty,fill,pro-p.cost,p.entries,'TARGET']);del pos[s]
  mv=sum(p.qty*float(closes[s].loc[dt]) for s,p in pos.items());equity=cash+mv
  states={s:(p.qty*float(closes[s].loc[dt])-p.cost) for s,p in pos.items()};wins=sum(v>0 for v in states.values());losses=sum(v<0 for v in states.values());active=len(pos)
  if active and wins/active>=.8:profitable_streak+=1
  else:profitable_streak=0
  # Evaluate pause rules only when not already paused/cooling down, avoiding endless reset.
  if i>=pause_until and i>=cooldown_until:
   if active==10 and losses==10:
    pause_until=i+5;events.append([dt,'PAUSE_ALL_10_LOSING',wins,losses]);profitable_streak=0
   elif active>0 and wins==losses:
    pause_until=i+5;events.append([dt,'PAUSE_EVEN_WIN_LOSS',wins,losses]);profitable_streak=0
  acted=False
  # Five consecutive sessions at >=80% profitable: add to biggest active loser.
  if i>=pause_until and i>=cooldown_until and profitable_streak>=5 and losses>0:
   s=min(states,key=states.get);p=pos[s]
   if states[s]<0 and p.entries<4:
    px=float(data[s].loc[dt].Close) if dt in data[s].index else float(closes[s].loc[dt]);order=equity*.0125;fill=px*(1+slip_bps/10000);qty=order/fill
    if order<=cash:
     cash-=order;p.qty+=qty;p.cost+=order;p.entries+=1;p.last_i=i;tr.append([dt,s,'BUY',qty,fill,0.,p.entries,'80PCT_ADD']);events.append([dt,'80PCT_ADD_'+s,wins,losses]);cooldown_until=i+2;profitable_streak=0;acted=True
  if not acted and i>=pause_until and i>=cooldown_until:
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
      if p is None:p=P(dt);pos[s]=p
      p.qty+=qty;p.cost+=order;p.entries+=1;p.last_i=i;tr.append([dt,s,'BUY',qty,fill,0.,p.entries,'NORMAL'])
  mv=sum(p.qty*float(closes[s].loc[dt]) for s,p in pos.items());curve.append([dt,cash+mv,wins,losses,pause_until>i])
 eq=pd.DataFrame(curve,columns=['date','equity','winning_positions','losing_positions','paused']).set_index('date');td=pd.DataFrame(tr,columns=['date','symbol','side','qty','price','pnl','entries','reason']);ev=pd.DataFrame(events,columns=['date','event','wins','losses'])
 final=float(eq.iloc[-1].equity);dd=float((eq.equity/eq.equity.cummax()-1).min())
 return {'tp':tp,'wait':wait,'final':final,'return_pct':(final/100000-1)*100,'max_dd_pct':dd*100,'orders':len(td),'exits':int((td.side=='EXIT').sum()),'open':len(pos),'pause_events':int(ev.event.str.startswith('PAUSE').sum()) if len(ev) else 0,'special_adds':int(ev.event.str.startswith('80PCT').sum()) if len(ev) else 0,'paused_sessions':int(eq.paused.sum())},td,eq,ev

def main():
 data={e:stitch(e,u)[0] for e,u in PAIRS.items()};out=Path('backtest_results/kitty_portfolio_rules');out.mkdir(parents=True,exist_ok=True);rows=[]
 for tp in [22,29]:
  base=test(data,1,tp)[0];v,t,e,ev=variant(data,1,tp);rows.append({'version':f'baseline_tp{tp}',**base});rows.append({'version':f'rules_tp{tp}',**v});t.to_csv(out/f'orders_tp{tp}.csv',index=False);e.to_csv(out/f'equity_tp{tp}.csv');ev.to_csv(out/f'rule_events_tp{tp}.csv',index=False)
 pd.DataFrame(rows).to_csv(out/'comparison.csv',index=False);print(pd.DataFrame(rows).to_string(index=False))
if __name__=='__main__':main()
