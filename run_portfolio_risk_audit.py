#!/usr/bin/env python
"""Execute +500/+800 JayBot signals through integrated shared-cash risk controls.

Underlying OHLC is real; option premiums, marks, and exits remain synthetic Black-Scholes
research outputs and are not represented as historical option fills.
"""
import json,os
from pathlib import Path
import pandas as pd
from falsification_audit import CURRENT,UNSEEN,Scenario,fetch,run_universe
from portfolio_risk_engine import RiskLimits,simulate_shared_cash
OUT=Path("backtest_results/portfolio_risk_engine")
FAMILY={"METU":"META","AAPU":"AAPL","MSFU":"MSFT","NFXL":"NFLX","PLTU":"PLTR","IBX":"semiconductors","NVDU":"semiconductors","GGLL":"GOOGL","AMZU":"AMZN","TSLT":"TSLA","SSO":"broad_market","QLD":"nasdaq_100","USD":"semiconductors","ROM":"technology","UCC":"consumer_discretionary","UYG":"financials","DDM":"dow_30","MVV":"midcap_400","RXL":"healthcare","DIG":"energy"}
LIMITS=RiskLimits(max_positions=20,max_premium_at_risk_pct=.10,max_family_risk_pct=.025,max_symbol_risk_pct=.01,drawdown_kill_pct=.25)
SAMPLES=[("current_mature",CURRENT,"2023-08-06","2026-08-05"),("unseen_recent",UNSEEN,"2023-08-06","2026-08-05")]
def main():
 OUT.mkdir(parents=True,exist_ok=True);data={s:fetch(s) for s in sorted(set(CURRENT+UNSEEN))};summaries=[]
 for tp in ([int(os.environ["TP_ONLY"])] if os.environ.get("TP_ONLY") else (500,800)):
  for name,syms,start,end in SAMPLES:
   if os.environ.get("SAMPLE_ONLY") and name!=os.environ["SAMPLE_ONLY"]: continue
   scenario=Scenario(f"risk_{name}_tp{tp}",tp_pct=tp);raw,by_symbol,candidates=run_universe(data,syms,start,end,scenario)
   candidates["family"]=candidates.symbol.map(FAMILY);prices={s:data[s].Close for s in syms}
   result=simulate_shared_cash(candidates,prices,100000.,LIMITS);stem=f"{name}_tp{tp}"
   candidates.to_csv(OUT/f"{stem}_candidate_ledger.csv",index=False);result.accepted.to_csv(OUT/f"{stem}_accepted_ledger.csv",index=False);result.rejected.to_csv(OUT/f"{stem}_rejected_ledger.csv",index=False);result.equity_curve.to_csv(OUT/f"{stem}_equity_curve.csv",index=False);by_symbol.to_csv(OUT/f"{stem}_independent_symbol_diagnostics.csv",index=False)
   row={"sample":name,"tp_pct":tp,**result.summary,"raw_independent_profit":raw["profit"],"candidate_trades":raw["trades"]};summaries.append(row)
 old=OUT/"summary.csv"; frame=pd.DataFrame(summaries); frame=pd.concat([pd.read_csv(old),frame],ignore_index=True).drop_duplicates(["sample","tp_pct"],keep="last") if old.exists() else frame; frame.to_csv(old,index=False)
 manifest={"research_only":True,"synthetic_option_warning":"Option values/fills are Black-Scholes simulations over real adjusted underlying OHLC; no historical chains, NBBO, spreads, liquidity, exact contract availability, or verified fills.","parameters":{"starting_cash":100000,"tp_pct":[500,800],"strike_otm_pct":10,"dte":84,"premium_per_signal_cap":500,"limits":LIMITS.__dict__,"family_map":FAMILY},"results":frame.to_dict(orient="records")}
 (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2));print(pd.DataFrame(summaries).to_string(index=False))
if __name__=="__main__":main()
