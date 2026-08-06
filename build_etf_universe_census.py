#!/usr/bin/env python
"""Validate and materialize dated snapshots of the JayBot ETF census.

This is an auditable *observed research census*, not a historical-security master.
It never infers launch/closure from missing prices and never claims that delisted
or closed funds are exhaustively represented.
"""
from __future__ import annotations
import argparse, csv, hashlib, json
from datetime import date
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DEFAULT_INPUT=ROOT/'data'/'etf_universe_census.csv'
DEFAULT_OUT=ROOT/'backtest_results'/'universe_census'
REQUIRED={'symbol','fund_name','issuer','leverage','direction','asset_scope','economic_family','underlying','source_url','source_kind','census_status','first_observed_price_date','inception_date','inception_date_basis','eligible_frozen_recent','eligibility_note'}

def parse_date(value, field, symbol):
    if not value: return None
    try: return date.fromisoformat(value)
    except ValueError as exc: raise ValueError(f'{symbol}: invalid {field}={value!r}') from exc

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',type=Path,default=DEFAULT_INPUT); ap.add_argument('--out',type=Path,default=DEFAULT_OUT); ap.add_argument('--as-of',action='append',default=[]); args=ap.parse_args()
    raw=args.input.read_bytes(); rows=list(csv.DictReader(raw.decode('utf-8').splitlines()))
    missing=REQUIRED-set(rows[0] if rows else []); assert not missing,f'missing columns: {sorted(missing)}'
    seen=set()
    for r in rows:
        s=r['symbol'].strip().upper(); assert s and s not in seen,f'duplicate/empty symbol {s!r}'; seen.add(s); r['symbol']=s
        assert r['leverage']=='2' and r['direction']=='long',f'{s}: census row violates objective long 2x rule'
        assert r['source_url'].startswith('https://'),f'{s}: durable source URL required'
        first=parse_date(r['first_observed_price_date'],'first_observed_price_date',s); inception=parse_date(r['inception_date'],'inception_date',s)
        if inception and first: assert first>=inception,f'{s}: price observation predates asserted inception'
    dates=[date.fromisoformat(x) for x in args.as_of] if args.as_of else [date(2023,8,6),date(2026,8,6)]
    args.out.mkdir(parents=True,exist_ok=True)
    fields=list(rows[0]) + ['snapshot_as_of','point_in_time_eligible']
    counts={}
    for d in dates:
        snap=[]
        for r in rows:
            x=dict(r); first=parse_date(r['first_observed_price_date'],'first_observed_price_date',r['symbol'])
            x['snapshot_as_of']=d.isoformat(); x['point_in_time_eligible']='yes' if first and first<=d and r['census_status']!='known_closed_before_snapshot' else 'no'; snap.append(x)
        p=args.out/f'census_as_of_{d.isoformat()}.csv'
        with p.open('w',newline='',encoding='utf-8') as f: w=csv.DictWriter(f,fields); w.writeheader(); w.writerows(snap)
        counts[d.isoformat()]=sum(x['point_in_time_eligible']=='yes' for x in snap)
    manifest={'schema_version':1,'objective_rule':'US-listed exchange-traded fund targeting +2x DAILY return of a US equity index, sector, or single stock','input':str(args.input.relative_to(ROOT)),'input_sha256':hashlib.sha256(raw).hexdigest(),'row_count':len(rows),'snapshots':counts,'coverage_class':'observed_research_census','historical_completeness_claimed':False,'known_limitations':['Seed contains the 20 products actually used by JayBot frozen current/unseen tests; it is not every product ever launched.','No exhaustive closed/delisted product registry was available from the durable sponsor/SEC sources used here.','first_observed_price_date is an availability bound, not an asserted legal inception date unless inception_date_basis=sponsor.','Current sponsor or SEC evidence cannot prove a fund was listed on an earlier date.']}
    (args.out/'census_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest,indent=2))
if __name__=='__main__': main()
