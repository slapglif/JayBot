#!/usr/bin/env python
"""Family/issuer concentration and leave-one-family-out audit.

P&L is additive because the audited simulator uses fixed premium and independent
per-symbol pause state. LOFO therefore removes a family's trades from the frozen
ledger; it does not re-optimize parameters or manufacture missing constituents.
"""
from __future__ import annotations
import argparse,csv,json,math
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def f(x):
    try:return float(x)
    except (TypeError,ValueError):return 0.0

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--ledger',type=Path,default=ROOT/'backtest_results'/'falsification_audit'/'frozen_test_ledgers.csv'); ap.add_argument('--census',type=Path,default=ROOT/'data'/'etf_universe_census.csv'); ap.add_argument('--out',type=Path,default=ROOT/'backtest_results'/'universe_family_audit'); ap.add_argument('--scenario',action='append',default=[]); args=ap.parse_args()
    census={r['symbol']:r for r in csv.DictReader(args.census.open(encoding='utf-8'))}; trades=list(csv.DictReader(args.ledger.open(encoding='utf-8')))
    required={'symbol','pnl','scenario'}; assert trades and required<=set(trades[0]),'ledger must contain symbol,pnl,scenario'
    missing=sorted({r['symbol'] for r in trades}-set(census)); assert not missing,f'ledger symbols missing census mapping: {missing}'
    scenarios=args.scenario or sorted({r['scenario'] for r in trades})
    args.out.mkdir(parents=True,exist_ok=True); summary=[]; group_rows=[]; lofo=[]
    for sc in scenarios:
        selected=[r for r in trades if r['scenario']==sc]; assert selected,f'no trades for scenario {sc}'
        by_family=defaultdict(float); by_issuer=defaultdict(float); by_symbol=defaultdict(float)
        for r in selected:
            p=f(r['pnl']); c=census[r['symbol']]; by_family[c['economic_family']]+=p; by_issuer[c['issuer']]+=p; by_symbol[r['symbol']]+=p
        total=sum(by_family.values()); abs_total=sum(abs(v) for v in by_family.values()); positive=sum(v>0 for v in by_family.values()); n=len(by_family)
        max_family=max(by_family,key=lambda k:abs(by_family[k])); max_issuer=max(by_issuer,key=lambda k:abs(by_issuer[k]))
        max_positive_family=max(by_family,key=by_family.get)
        max_positive_share=(100*by_family[max_positive_family]/total) if total>0 else None
        row={'scenario':sc,'trades':len(selected),'symbols':len(by_symbol),'families':n,'total_pnl':total,'positive_families':positive,'positive_family_pct':100*positive/n,'largest_abs_family':max_family,'largest_abs_family_pnl':by_family[max_family],'largest_abs_family_share_of_abs_pnl_pct':100*abs(by_family[max_family])/abs_total if abs_total else 0,'largest_positive_family':max_positive_family,'largest_positive_family_share_of_total_profit_pct':max_positive_share,'largest_issuer':max_issuer,'largest_issuer_pnl':by_issuer[max_issuer],'largest_issuer_share_of_abs_pnl_pct':100*abs(by_issuer[max_issuer])/sum(abs(v) for v in by_issuer.values()),'passes_70pct_positive_families':positive/n>=.70,'passes_25pct_max_family_profit_contribution':max_positive_share is not None and max_positive_share<=25.0}
        summary.append(row)
        for kind,groups in [('family',by_family),('issuer',by_issuer),('symbol',by_symbol)]:
            denom=sum(abs(v) for v in groups.values())
            for name,pnl in groups.items():group_rows.append({'scenario':sc,'group_type':kind,'group':name,'pnl':pnl,'share_of_total_pnl_pct':100*pnl/total if total else None,'share_of_abs_group_pnl_pct':100*abs(pnl)/denom if denom else None})
        for family,pnl in by_family.items():lofo.append({'scenario':sc,'left_out_family':family,'left_out_pnl':pnl,'remaining_pnl':total-pnl,'remaining_profitable':total-pnl>0,'remaining_pnl_change_pct':(-pnl/total*100) if total else None})
    def write(name,rows):
        with (args.out/name).open('w',newline='',encoding='utf-8') as h:w=csv.DictWriter(h,rows[0].keys());w.writeheader();w.writerows(rows)
    write('scenario_summary.csv',summary);write('group_concentration.csv',group_rows);write('leave_one_family_out.csv',lofo)
    result={'schema_version':1,'ledger':str(args.ledger.relative_to(ROOT)),'census':str(args.census.relative_to(ROOT)),'scenarios':summary,'method':'Frozen-ledger additive leave-one-economic-family-out; no parameter reselection.','limitations':['Synthetic option P&L only; no historical option-chain fills.','Only census-mapped observed research symbols are audited.','Issuer concentration is not an independent-family test.']}
    (args.out/'audit_summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
