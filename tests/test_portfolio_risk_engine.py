import pandas as pd
from portfolio_risk_engine import RiskLimits, simulate_shared_cash

def c(s,f,ed="2024-01-02",xd="2024-01-05",p=500,x=600):
 return {"symbol":s,"family":f,"entry_date":ed,"exit_date":xd,"entry_price":p/100,"exit_price":x/100,"contracts":1,"strike":100.,"expiry_date":"2024-03-26","entry_iv":.5}

def test_caps():
 q=pd.DataFrame([c("AAA","A"),c("BBB","B"),c("CCC","C")]); px={s:pd.Series([100.,100.],index=pd.to_datetime(["2024-01-02","2024-01-05"])) for s in q.symbol}
 r=simulate_shared_cash(q,px,10000,RiskLimits(max_positions=2,max_premium_at_risk_pct=.1,max_family_risk_pct=1,max_symbol_risk_pct=1))
 assert len(r.accepted)==2 and r.rejected.iloc[0].reason=="max_positions"
 assert r.summary["max_open_positions"]==2 and r.summary["max_premium_at_risk_pct"]<=.1

def test_family_symbol_caps():
 q=pd.DataFrame([c("AAA","TECH"),c("AAA","TECH"),c("BBB","TECH"),c("CCC","OTHER")]);px={s:pd.Series([100.],index=pd.to_datetime(["2024-01-02"])) for s in q.symbol.unique()}
 r=simulate_shared_cash(q,px,10000,RiskLimits(max_premium_at_risk_pct=1,max_family_risk_pct=.05,max_symbol_risk_pct=.05))
 assert list(r.accepted.symbol)==["AAA","CCC"] and set(r.rejected.reason)=={"symbol_cap","family_cap"}

def test_cash_and_kill():
 q=pd.DataFrame([c("AAA","A")]);px={"AAA":pd.Series([100.],index=pd.to_datetime(["2024-01-02"]))}
 r=simulate_shared_cash(q,px,400,RiskLimits(max_premium_at_risk_pct=1,max_family_risk_pct=1,max_symbol_risk_pct=1));assert r.rejected.iloc[0].reason=="insufficient_cash"
 q=pd.DataFrame([c("AAA","A",xd="2024-01-03",x=0),c("BBB","B",ed="2024-01-04")]);px={"AAA":pd.Series([100.,50.],index=pd.to_datetime(["2024-01-02","2024-01-03"])),"BBB":pd.Series([100.],index=pd.to_datetime(["2024-01-04"]))}
 r=simulate_shared_cash(q,px,10000,RiskLimits(max_premium_at_risk_pct=1,max_family_risk_pct=1,max_symbol_risk_pct=1,drawdown_kill_pct=.04))
 assert r.summary["kill_switch_triggered"] and r.summary["kill_switch_date"]=="2024-01-03" and r.rejected.iloc[0].reason=="drawdown_kill"
