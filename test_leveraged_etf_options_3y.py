#!/usr/bin/env python
"""Three-year test of successful crash-grid option rules on 2x single-stock ETFs."""
import requests,math
from pathlib import Path
import pandas as pd
from optimize_crash_option_variables import sim,prep
TICKERS=['METU','AAPU','MSFU','NFXL','PLTU','IBX','NVDU','GGLL','AMZU','TSLT']
CONFIGS={'raw_winner':(10,84,500),'balanced_winner':(12.5,28,250)}
START='2023-08-06';END='2026-08-05'
def fetch(sym):
 p=Path(f'data_cache/three_year_{sym}_1d.csv')
 if p.exists():return pd.read_csv(p,index_col=0,parse_dates=True)
 p1=int(pd.Timestamp(START,tz='UTC').timestamp());p2=int((pd.Timestamp(END,tz='UTC')+pd.Timedelta(days=200)).timestamp());u=f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1={p1}&period2={p2}&interval=1d&events=div%2Csplits&includeAdjustedClose=true';j=requests.get(u,headers={'User-Agent':'Mozilla/5.0'},timeout=45).json();res=j.get('chart',{}).get('result');
 if not res:return pd.DataFrame()
 z=res[0];q=z['indicators']['quote'][0];adj=z['indicators'].get('adjclose',[{}])[0].get('adjclose',q['close']);x=pd.DataFrame(q,index=pd.to_datetime(z['timestamp'],unit='s',utc=True).tz_convert('US/Eastern').tz_localize(None));x['AdjClose']=adj;fac=x.AdjClose/x.close
 for c in ['open','high','low','close']:x[c.title()]=x[c]*fac
 x=x[['Open','High','Low','Close']].dropna();x.to_csv(p);return x
def main():
 out=Path('backtest_results/leveraged_etf_options_3y');out.mkdir(parents=True,exist_ok=True);rows=[];logs=[]
 for s in TICKERS:
  d=fetch(s)
  if d.empty:
   for n,c in CONFIGS.items():rows.append([n,*c,s,None,None,0,0,0,0,0,0,0,0])
   continue
  actual_start=max(pd.Timestamp(START),d.index.min());actual_end=min(pd.Timestamp(END),d.index.max())
  for name,(sp,dte,tp) in CONFIGS.items():
   r=sim(*prep(d,actual_start,actual_end),sp,dte,tp,True);rows.append([name,sp,dte,tp,s,str(actual_start.date()),str(actual_end.date()),r['profit'],r['executed'],r['wins'],r['losses'],r['win_rate_pct'],r['premium'],r['paused'],r['triggers']]);z=pd.DataFrame(r['ledger'],columns=['entry_date','spot','strike','entry_option_price','contracts','exit_date','pnl','reason']);z['configuration']=name;z['symbol']=s;logs.append(z)
 cols=['configuration','strike_otm_pct','dte_days','tp_pct','symbol','start','end','profit','executed','wins','losses','win_rate_pct','premium_deployed','paused_entries','pause_triggers'];res=pd.DataFrame(rows,columns=cols);res.to_csv(out/'by_symbol.csv',index=False);pd.concat(logs).to_csv(out/'all_trades.csv',index=False);agg=res.groupby('configuration').agg(profit=('profit','sum'),executed=('executed','sum'),wins=('wins','sum'),losses=('losses','sum'),premium_deployed=('premium_deployed','sum'),paused_entries=('paused_entries','sum'),pause_triggers=('pause_triggers','sum')).reset_index();agg['win_rate_pct']=agg.wins/agg.executed*100;agg['profit_on_premium_pct']=agg.profit/agg.premium_deployed*100;agg.to_csv(out/'summary.csv',index=False);print(agg.to_string(index=False));print(res.sort_values(['configuration','profit'],ascending=[True,False]).to_string(index=False))
if __name__=='__main__':main()
