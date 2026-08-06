#!/usr/bin/env python
"""Best 2-year hourly strategy plus +4% arm / +2% profit-lock stop."""
from dataclasses import dataclass
from pathlib import Path
import pandas as pd,json
from validate_best_2y_hourly import PAIRS,stitch
@dataclass
class P: qty:float=0.;cost:float=0.;entries:int=0;last_session:int=-999;opened:str='';armed:bool=False
def run(data,tp=29,wait=1,slip=5):
 decisions=sorted(set().union(*(set(d[(d.index.hour==13)&(d.index.minute==30)].index) for d in data.values())));sessions=sorted({x.date().isoformat() for x in decisions});sid={s:i for i,s in enumerate(sessions)};cash=100000.;pos={};tr=[];curve=[];prev=None;arms=[]
 for dt in decisions:
  sn=sid[dt.date().isoformat()]
  for s,p in list(pos.items()):
   bars=data[s][(data[s].index<=dt)&((data[s].index>prev) if prev is not None else True)].sort_index();avg=p.cost/p.qty;target=avg*(1+tp/100);stop=avg*1.02;done=False
   for bt,r in bars.iterrows():
    if r.High>=target:
     fill=target*(1-slip/10000);pro=p.qty*fill;cash+=pro;tr.append([bt,s,'EXIT',p.qty,fill,pro-p.cost,p.entries,'TP29']);del pos[s];done=True;break
    if not p.armed and r.High>=avg*1.04:
     p.armed=True;arms.append([bt,s,avg,stop])
    if p.armed and r.Low<=stop:
     fill=stop*(1-slip/10000);pro=p.qty*fill;cash+=pro;tr.append([bt,s,'EXIT',p.qty,fill,pro-p.cost,p.entries,'PROFIT_LOCK_2']);del pos[s];done=True;break
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
   p.qty+=qty;p.cost+=order;p.entries+=1;p.last_session=sn;tr.append([dt,s,'BUY',qty,fill,0.,p.entries,'ENTRY']);bought+=1
  equity=cash+sum(p.qty*float(data[s][data[s].index<=dt].iloc[-1].Close) for s,p in pos.items());curve.append([dt,equity,cash,len(pos),sum(p.armed for p in pos.values())]);prev=dt
 eq=pd.DataFrame(curve,columns=['timestamp','equity','cash','positions','armed_positions']).set_index('timestamp');td=pd.DataFrame(tr,columns=['timestamp','symbol','side','qty','price','pnl','entries','reason']);ar=pd.DataFrame(arms,columns=['timestamp','symbol','avg_price','stop_price']);final=float(eq.iloc[-1].equity);dd=float((eq.equity/eq.equity.cummax()-1).min());years=len(sessions)/252
 stats={'start':sessions[0],'end':sessions[-1],'final':final,'return_pct':(final/100000-1)*100,'cagr_pct':((final/100000)**(1/years)-1)*100,'max_dd_pct':dd*100,'orders':len(td),'buys':int((td.side=='BUY').sum()),'exits':int((td.side=='EXIT').sum()),'tp_exits':int((td.reason=='TP29').sum()),'profit_lock_exits':int((td.reason=='PROFIT_LOCK_2').sum()),'open':len(pos),'arms':len(ar)}
 return stats,td,eq,ar
if __name__=='__main__':
 data={e:stitch(e,u)[0] for e,u in PAIRS.items()};s,t,e,a=run(data);out=Path('backtest_results/best_strategy_2y_profit_lock');out.mkdir(parents=True,exist_ok=True);t.to_csv(out/'orders.csv',index=False);e.to_csv(out/'equity.csv');a.to_csv(out/'stop_activations.csv',index=False);(out/'summary.json').write_text(json.dumps(s,indent=2));print(json.dumps(s,indent=2));print(t[t.side=='EXIT'].reason.value_counts().to_string())
