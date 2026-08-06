#!/usr/bin/env python
"""10-symbol hourly system: arm +5%, lock +2.5%, recheck market 2h after exit."""
from dataclasses import dataclass
from pathlib import Path
import pandas as pd,json
from validate_best_2y_hourly import PAIRS,stitch
@dataclass
class P: qty:float=0.;cost:float=0.;entries:int=0;last_session:int=-999;opened:str='';armed:bool=False
def run(data,tp=29,wait=1,slip=5):
 bars=sorted(set().union(*(set(d.index) for d in data.values())));sessions=sorted({x.date().isoformat() for x in bars});sid={s:i for i,s in enumerate(sessions)};cash=100000.;pos={};tr=[];curve=[];reeval={};arms=[]
 def buy_at(dt,limit,reason,excluded=set()):
  nonlocal cash
  sn=sid[dt.date().isoformat()];equity=cash+sum(p.qty*float(data[s][data[s].index<=dt].iloc[-1].Close) for s,p in pos.items());elig=[]
  for s,d in data.items():
   if s in excluded or dt not in d.index:continue
   r=d.loc[dt]
   if r.Close<r.day_open:elig.append((float(r.Close/r.day_open-1),s,float(r.Close)))
  bought=0
  for drop,s,px in sorted(elig):
   if bought>=limit:break
   p=pos.get(s)
   if p is not None and (p.entries>=4 or sn-p.last_session<wait):continue
   order=equity*.0125;fill=px*(1+slip/10000);qty=order/fill
   if order>cash:continue
   cash-=order
   if p is None:p=P(opened=str(dt));pos[s]=p
   p.qty+=qty;p.cost+=order;p.entries+=1;p.last_session=sn;tr.append([dt,s,'BUY',qty,fill,0.,p.entries,reason]);bought+=1
  return bought
 for dt in bars:
  closed=[]
  for s,p in list(pos.items()):
   if dt not in data[s].index:continue
   r=data[s].loc[dt];avg=p.cost/p.qty;target=avg*(1+tp/100);stop=avg*1.025
   if r.High>=target:
    fill=target*(1-slip/10000);pro=p.qty*fill;cash+=pro;tr.append([dt,s,'EXIT',p.qty,fill,pro-p.cost,p.entries,'TP29']);del pos[s];closed.append(s);continue
   if not p.armed and r.High>=avg*1.05:p.armed=True;arms.append([dt,s,avg,stop])
   if p.armed and r.Low<=stop:
    fill=stop*(1-slip/10000);pro=p.qty*fill;cash+=pro;tr.append([dt,s,'EXIT',p.qty,fill,pro-p.cost,p.entries,'PROFIT_LOCK_2_5']);del pos[s];closed.append(s)
  # Each close earns one recheck two hours later, only if that bar remains in same session.
  if closed:
   rt=dt+pd.Timedelta(hours=2)
   if rt.date()==dt.date() and rt.hour<=15:reeval.setdefault(rt,[]).extend(closed)
  # Main daily evaluation: up to two different assets.
  if dt.hour==13 and dt.minute==30:buy_at(dt,2,'DAILY_1330')
  # Post-exit evaluation: one replacement per closed slot; do not immediately rebuy exited names.
  if dt in reeval:
   excluded=set(reeval[dt]);n=buy_at(dt,len(reeval[dt]),'POST_EXIT_2H',excluded)
   if n==0:tr.append([dt,'','NO_BUY',0,0,0,0,'POST_EXIT_NO_QUALIFIER'])
  equity=cash+sum(p.qty*float(data[s][data[s].index<=dt].iloc[-1].Close) for s,p in pos.items());curve.append([dt,equity,cash,len(pos),sum(p.armed for p in pos.values())])
 eq=pd.DataFrame(curve,columns=['timestamp','equity','cash','positions','armed_positions']).set_index('timestamp');td=pd.DataFrame(tr,columns=['timestamp','symbol','side','qty','price','pnl','entries','reason']);ar=pd.DataFrame(arms,columns=['timestamp','symbol','avg_price','stop_price']);final=float(eq.iloc[-1].equity);dd=float((eq.equity/eq.equity.cummax()-1).min());years=len(sessions)/252
 stats={'start':sessions[0],'end':sessions[-1],'final':final,'return_pct':(final/100000-1)*100,'cagr_pct':((final/100000)**(1/years)-1)*100,'max_dd_pct':dd*100,'orders':int((td.side!='NO_BUY').sum()),'buys':int((td.side=='BUY').sum()),'exits':int((td.side=='EXIT').sum()),'tp_exits':int((td.reason=='TP29').sum()),'profit_lock_exits':int((td.reason=='PROFIT_LOCK_2_5').sum()),'post_exit_buys':int((td.reason=='POST_EXIT_2H').sum()),'post_exit_no_qualifier':int((td.reason=='POST_EXIT_NO_QUALIFIER').sum()),'open':len(pos),'arms':len(ar)}
 return stats,td,eq,ar
if __name__=='__main__':
 data={e:stitch(e,u)[0] for e,u in PAIRS.items()};s,t,e,a=run(data);out=Path('backtest_results/ten_stock_5_2_5_reentry');out.mkdir(parents=True,exist_ok=True);t.to_csv(out/'orders_and_checks.csv',index=False);e.to_csv(out/'equity.csv');a.to_csv(out/'stop_activations.csv',index=False);(out/'summary.json').write_text(json.dumps(s,indent=2));print(json.dumps(s,indent=2));print(t.reason.value_counts().to_string())
