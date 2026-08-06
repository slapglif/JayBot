#!/usr/bin/env python
from __future__ import annotations
import argparse,json,math
from dataclasses import asdict,dataclass
from pathlib import Path
import numpy as np,pandas as pd,requests
from datetime import datetime,timezone
DEFAULT_WATCHLIST="AAPL MSFT NVDA AMZN GOOGL META TSLA AVGO BRK-B JPM V MA UNH XOM COST NFLX AMD QQQ SPY TQQQ SQQQ UPRO SPXU SOXL SOXS TECL TECS".split()
@dataclass
class Position:
 symbol:str; qty:float=0.; cost:float=0.; entries:int=0; last_entry_session:int=-999999; opened:str=""
 def avg(self): return self.cost/self.qty if self.qty else 0.
@dataclass
class Config:
 initial_capital:float=100000.; entry_pct:float=.0125; max_entries:int=4; max_alloc_pct:float=.05; max_positions:int=10; wait_sessions:int=2; pause_sessions:int=5; target_pct:float=.05; commission_per_order:float=0.; slippage_bps:float=5.
def load(symbols,start,end,cache):
 cache.mkdir(parents=True,exist_ok=True); out={}
 for s in symbols:
  p=cache/f"{s}_{start}_{end}_1h.csv"
  if p.exists(): d=pd.read_csv(p,index_col=0,parse_dates=True)
  else:
   p1=int(datetime.fromisoformat(start).replace(tzinfo=timezone.utc).timestamp());p2=int(datetime.fromisoformat(end).replace(tzinfo=timezone.utc).timestamp())
   u=f"https://query1.finance.yahoo.com/v8/finance/chart/{s}"
   j=requests.get(u,params={"period1":p1,"period2":p2,"interval":"1h","events":"div,splits"},headers={"User-Agent":"Mozilla/5.0"},timeout=60).json()["chart"]["result"][0]
   q=j["indicators"]["quote"][0];d=pd.DataFrame(q,index=pd.to_datetime(j["timestamp"],unit="s",utc=True));d=d.rename(columns={"open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume"}).dropna(subset=["Open","High","Low","Close"])
   if not d.empty:d.to_csv(p)
  if d.empty:continue
  d.index=pd.to_datetime(d.index,utc=True).tz_convert("America/New_York")
  # Yahoo intraday OHLC is already split-adjusted to the current share basis.
  d=d.between_time("09:30","15:59").copy()
  d["session"]=d.index.date.astype(str);d["day_open"]=d.groupby("session")["Open"].transform("first");d["sma_proxy"]=d.Close.rolling(50,min_periods=50).mean()
  out[s]=(d,d[(d.index.hour==13)&(d.index.minute==30)].copy())
 return out
def run(data,cfg):
 decisions=sorted(set().union(*(set(p.index) for _,p in data.values())));sessions=sorted({x.date().isoformat() for x in decisions});sid={s:i for i,s in enumerate(sessions)}
 cash=cfg.initial_capital;positions={};trades=[];curve=[];pause_until=-1;prev_ts=None
 for ts in decisions:
  sn=sid[ts.date().isoformat()]
  for sym,pos in list(positions.items()):
   bars=data[sym][0]; bars=bars[(bars.index<=ts)&((bars.index>prev_ts) if prev_ts is not None else True)];target=pos.avg()*(1+cfg.target_pct)
   if not bars.empty and float(bars.High.max())>=target:
    fill=target*(1-cfg.slippage_bps/1e4);proceeds=pos.qty*fill-cfg.commission_per_order;cash+=proceeds
    trades.append(dict(timestamp=str(ts),symbol=sym,side="EXIT",qty=pos.qty,price=fill,pnl=proceeds-pos.cost,entries=pos.entries));del positions[sym]
  mv=sum(p.qty*float(data[s][0][data[s][0].index<=ts].iloc[-1].Close) for s,p in positions.items());equity=cash+mv;candidates=[]
  for sym,(_,pick) in data.items():
   if ts not in pick.index:continue
   r=pick.loc[ts];r=r.iloc[-1] if isinstance(r,pd.DataFrame) else r;close,op,sma=map(float,(r.Close,r.day_open,r.sma_proxy))
   if math.isfinite(sma) and close<sma and close<op:candidates.append((close/op-1,sym,close))
  candidates.sort();opened_new=False
  for decline,sym,close in candidates:
   if sn<pause_until:break
   pos=positions.get(sym)
   if pos is None and (opened_new or len(positions)>=cfg.max_positions):continue
   if pos and(pos.entries>=cfg.max_entries or sn-pos.last_entry_session<cfg.wait_sessions):continue
   order=equity*cfg.entry_pct
   if (pos.qty*close if pos else 0)+order>equity*cfg.max_alloc_pct+1e-8:continue
   fill=close*(1+cfg.slippage_bps/1e4);qty=order/fill;total=qty*fill+cfg.commission_per_order
   if total>cash:continue
   cash-=total
   if pos is None:pos=Position(sym,opened=str(ts));positions[sym]=pos;opened_new=True
   pos.qty+=qty;pos.cost+=total;pos.entries+=1;pos.last_entry_session=sn
   trades.append(dict(timestamp=str(ts),symbol=sym,side="BUY",qty=qty,price=fill,pnl=0.,entries=pos.entries,decline_from_open=decline))
  if len(positions)>=cfg.max_positions:pause_until=max(pause_until,sn+cfg.pause_sessions)
  mv=sum(p.qty*float(data[s][0][data[s][0].index<=ts].iloc[-1].Close) for s,p in positions.items());curve.append(dict(timestamp=str(ts),equity=cash+mv,cash=cash,positions=len(positions)));prev_ts=ts
 eq=pd.DataFrame(curve);tr=pd.DataFrame(trades);final=float(eq.iloc[-1].equity);rets=eq.equity.pct_change().dropna();dd=eq.equity/eq.equity.cummax()-1;years=max(len(sessions)/252,1/252);ex=tr[tr.side=="EXIT"] if not tr.empty else tr
 stats=dict(start=sessions[0],end=sessions[-1],sessions=len(sessions),initial_equity=cfg.initial_capital,final_equity=final,total_return_pct=(final/cfg.initial_capital-1)*100,cagr_pct=((final/cfg.initial_capital)**(1/years)-1)*100,max_drawdown_pct=float(dd.min()*100),decision_sharpe=float(np.sqrt(252)*rets.mean()/rets.std()) if len(rets)>1 and rets.std()>0 else 0,orders=len(tr),buys=int((tr.side=="BUY").sum()) if not tr.empty else 0,closed_positions=len(ex),realized_win_rate_pct=float((ex.pnl>0).mean()*100) if len(ex) else None,open_positions=len(positions),data_mode="yahoo-1h-proxy",slippage_bps=cfg.slippage_bps,commission_per_order=cfg.commission_per_order,watchlist=sorted(data))
 return stats,tr,eq,positions
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--start",required=True);ap.add_argument("--end",required=True);ap.add_argument("--out",default="backtest_results");ap.add_argument("--slippage-bps",type=float,default=5);ap.add_argument("--commission",type=float,default=0);ap.add_argument("--symbols",nargs="*",default=DEFAULT_WATCHLIST);a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True);cfg=Config(slippage_bps=a.slippage_bps,commission_per_order=a.commission);stats,tr,eq,pos=run(load(a.symbols,a.start,a.end,Path("data_cache")),cfg);tr.to_csv(out/"trades.csv",index=False);eq.to_csv(out/"equity_curve.csv",index=False);(out/"summary.json").write_text(json.dumps(dict(stats=stats,config=asdict(cfg),open_positions={k:asdict(v) for k,v in pos.items()}),indent=2));print(json.dumps(stats,indent=2))
if __name__=="__main__":main()
