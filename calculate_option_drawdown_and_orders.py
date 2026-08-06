#!/usr/bin/env python
"""Build raw-winner option order ledger and mark-to-model portfolio drawdown."""
from pathlib import Path
import math,pandas as pd
from optimize_crash_option_variables import call
ROOT=Path('backtest_results/leveraged_etf_options_3y')
raw=pd.read_csv(ROOT/'all_trades.csv');raw=raw[(raw.configuration=='raw_winner')&(raw.contracts>0)].copy();raw.entry_date=pd.to_datetime(raw.entry_date);raw.exit_date=pd.to_datetime(raw.exit_date);raw['cost']=raw.entry_option_price*raw.contracts*100;raw['exit_option_price']=raw.entry_option_price+raw.pnl/(raw.contracts*100);raw['expiry']=raw.entry_date+pd.Timedelta(days=84)
data={}
for s in raw.symbol.unique():
 d=pd.read_csv(f'data_cache/three_year_{s}_1d.csv',index_col=0,parse_dates=True);d['rv']=d.Close.pct_change().rolling(20).std()*math.sqrt(252);d.rv=d.rv.clip(.25,1.75).fillna(.80);data[s]=d
raw['entry_vol']=[float(data[s].loc[dt,'rv']) for s,dt in zip(raw.symbol,raw.entry_date)]
orders=[]
for i,r in raw.iterrows():
 orders.append([r.entry_date,r.symbol,'BUY_CALL',int(r.contracts),r.strike,84,r.spot,r.entry_option_price,r.cost,'ENTRY',0])
 orders.append([r.exit_date,r.symbol,'SELL_CALL',int(r.contracts),r.strike,max((r.expiry-r.exit_date).days,0),None,r.exit_option_price,r.exit_option_price*r.contracts*100,r.reason,r.pnl])
o=pd.DataFrame(orders,columns=['date','symbol','side','contracts','strike','dte_remaining','underlying_price','option_price','gross_amount','reason','realized_pnl']).sort_values(['date','side','symbol']);o.to_csv(ROOT/'raw_winner_option_orders.csv',index=False)
# Shared $100k mark-to-model portfolio, honoring the already-generated independent trade schedule.
dates=sorted(set().union(*(set(d.index[(d.index>=raw.entry_date.min())&(d.index<=raw.exit_date.max())]) for d in data.values())));cash=100000.;openids=set();curve=[]
for dt in dates:
 exits=raw.index[raw.exit_date==dt]
 for i in exits:
  if i in openids:
   r=raw.loc[i];cash+=r.exit_option_price*r.contracts*100;openids.remove(i)
 entries=raw.index[raw.entry_date==dt]
 for i in entries:
  r=raw.loc[i];cash-=r.cost;openids.add(i)
 mtm=0.
 for i in openids:
  r=raw.loc[i];d=data[r.symbol];avail=d.index[d.index<=dt]
  if not len(avail):continue
  spot=float(d.loc[avail[-1],'Close']);rem=max((r.expiry-dt).days,0)/365;mtm+=call(spot,float(r.strike),rem,float(r.entry_vol),.03)*r.contracts*100
 equity=cash+mtm;curve.append([dt,equity,cash,mtm,len(openids)])
eq=pd.DataFrame(curve,columns=['date','equity','cash','open_option_value','open_positions']).set_index('date');eq['peak']=eq.equity.cummax();eq['drawdown_pct']=(eq.equity/eq.peak-1)*100;eq.to_csv(ROOT/'raw_winner_option_equity_curve.csv');trough=eq.drawdown_pct.idxmin();peak=eq.loc[:trough].equity.idxmax();summary={'starting_equity':100000,'ending_equity':float(eq.iloc[-1].equity),'max_drawdown_pct':float(eq.drawdown_pct.min()),'max_drawdown_dollars':float(eq.loc[trough].equity-eq.loc[peak].equity),'peak_date':str(peak.date()),'trough_date':str(trough.date()),'peak_equity':float(eq.loc[peak].equity),'trough_equity':float(eq.loc[trough].equity),'minimum_cash':float(eq.cash.min()),'max_open_positions':int(eq.open_positions.max()),'orders':len(o),'round_trips':len(raw)}
import json;(ROOT/'raw_winner_drawdown_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));print(o.head(20).to_string(index=False))
