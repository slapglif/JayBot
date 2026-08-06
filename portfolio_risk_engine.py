"""Shared-cash, mark-to-model portfolio risk engine for JayBot synthetic option research."""
from dataclasses import dataclass
import math
import pandas as pd
from falsification_audit import call

@dataclass(frozen=True)
class RiskLimits:
 max_positions:int=20
 max_premium_at_risk_pct:float=.10
 max_family_risk_pct:float=.025
 max_symbol_risk_pct:float=.01
 drawdown_kill_pct:float=.25

@dataclass
class PortfolioResult:
 accepted:pd.DataFrame
 rejected:pd.DataFrame
 equity_curve:pd.DataFrame
 summary:dict

def simulate_shared_cash(candidates, prices, starting_cash=100000., limits=RiskLimits()):
 q=candidates.copy()
 for col in ("entry_date","exit_date","expiry_date"): q[col]=pd.to_datetime(q[col])
 q=q.sort_values(["entry_date","symbol"],kind="stable").reset_index(drop=True)
 dates=set(q.entry_date)|set(q.exit_date)
 for x in prices.values(): dates.update(pd.to_datetime(x.index))
 cash=float(starting_cash); peak=cash; killed=False; kill_date=None; open_pos=[]; accepted=[]; rejected=[]; curve=[]; max_open=0; max_risk=0.
 def mark(p,date):
  if date>=p["exit_date"]: return p["exit_price"]*100*p["contracts"]
  s=prices.get(p["symbol"])
  if s is None or len(s.loc[:date])==0: return p["cost"]
  spot=float(s.loc[:date].iloc[-1]); rem=max((p["expiry_date"]-date).days,0)/365
  return call(spot,p["strike"],rem,p["entry_iv"])*100*p["contracts"]
 for date in sorted(dates):
  still=[]
  for p in open_pos:
   if p["exit_date"]<=date: cash+=p["exit_price"]*100*p["contracts"]
   else: still.append(p)
  open_pos=still
  pre_equity=cash+sum(mark(p,date) for p in open_pos)
  peak=max(peak,pre_equity); dd=(pre_equity/peak-1) if peak else -1
  if not killed and dd<=-limits.drawdown_kill_pct: killed=True;kill_date=date
  for _,row in q[q.entry_date==date].iterrows():
   p=row.to_dict(); cost=p["entry_price"]*100*p["contracts"]; p["cost"]=cost
   equity=cash+sum(mark(x,date) for x in open_pos); total=sum(x["cost"] for x in open_pos)
   family=sum(x["cost"] for x in open_pos if x["family"]==p["family"]); symbol=sum(x["cost"] for x in open_pos if x["symbol"]==p["symbol"])
   reason=None
   if killed: reason="drawdown_kill"
   elif cost>cash+1e-9: reason="insufficient_cash"
   elif len(open_pos)>=limits.max_positions: reason="max_positions"
   elif total+cost>equity*limits.max_premium_at_risk_pct+1e-9: reason="premium_cap"
   elif symbol+cost>equity*limits.max_symbol_risk_pct+1e-9: reason="symbol_cap"
   elif family+cost>equity*limits.max_family_risk_pct+1e-9: reason="family_cap"
   if reason: rejected.append({**p,"reason":reason})
   else: cash-=cost;open_pos.append(p);accepted.append(p)
  equity=cash+sum(mark(p,date) for p in open_pos);risk=sum(p["cost"] for p in open_pos)
  peak=max(peak,equity);dd=equity/peak-1 if peak else -1
  if not killed and dd<=-limits.drawdown_kill_pct:killed=True;kill_date=date
  max_open=max(max_open,len(open_pos));max_risk=max(max_risk,risk/equity if equity else math.inf)
  curve.append({"date":date,"cash":cash,"open_value":equity-cash,"equity":equity,"drawdown_pct":dd*100,"open_positions":len(open_pos),"premium_at_risk":risk,"premium_at_risk_pct":risk/equity if equity else math.inf,"killed":killed})
 eq=pd.DataFrame(curve); final=float(eq.equity.iloc[-1]) if len(eq) else cash
 summary={"starting_cash":starting_cash,"ending_equity":final,"profit":final-starting_cash,"return_pct":(final/starting_cash-1)*100,"max_drawdown_pct":float(eq.drawdown_pct.min()) if len(eq) else 0.,"minimum_cash":float(eq.cash.min()) if len(eq) else cash,"max_open_positions":max_open,"max_premium_at_risk_pct":max_risk,"accepted_trades":len(accepted),"rejected_trades":len(rejected),"kill_switch_triggered":killed,"kill_switch_date":str(kill_date.date()) if kill_date is not None else None}
 return PortfolioResult(pd.DataFrame(accepted),pd.DataFrame(rejected),eq,summary)
