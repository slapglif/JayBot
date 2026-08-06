#!/usr/bin/env python
"""Append-only prospective Cboe delayed option-chain evidence collector.

No credentials are required. This records public delayed data; it is not OPRA
historical NBBO and cannot retroactively validate the backtest. Raw responses are
gzip-compressed and linked by SHA-256 in an append-only manifest.
"""
import argparse,datetime as dt,gzip,hashlib,json,re,sys,time
from pathlib import Path
import requests
SYMBOLS=['METU','AAPU','MSFU','NFXL','PLTU','IBX','NVDU','GGLL','AMZU','TSLT']
ROOT=Path('prospective_shadow'); RAW=ROOT/'raw'; MANIFEST=ROOT/'evidence_chain.jsonl'; PICKS=ROOT/'contract_selections.csv'
PAT=re.compile(r'^([A-Z]+)(\d{6})([CP])(\d{8})$')
HEAD={'User-Agent':'JayBot-research/1.0'}
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def parse_contract(s):
 m=PAT.match(s or '')
 if not m:return None
 return {'root':m.group(1),'expiry':dt.datetime.strptime(m.group(2),'%y%m%d').date(),'right':m.group(3),'strike':int(m.group(4))/1000}
def choose(data,asof):
 spot=float(data['current_price']);target_strike=spot*1.10;c=[]
 for q in data['options']:
  z=parse_contract(q.get('option'))
  if not z or z['right']!='C':continue
  dte=(z['expiry']-asof).days
  if dte<70 or dte>105:continue
  bid=float(q.get('bid') or 0);ask=float(q.get('ask') or 0)
  if ask<=0:continue
  c.append((abs(dte-84),abs(z['strike']-target_strike),-float(q.get('open_interest') or 0),z,q))
 if not c:return {'status':'NO_CONTRACT','spot':spot,'target_strike':target_strike}
 _,_,_,z,q=min(c,key=lambda x:x[:3]);bid=float(q.get('bid') or 0);ask=float(q.get('ask') or 0);mid=(bid+ask)/2 if bid>0 else ask;spread=(ask-bid)/mid*100 if mid else None;contracts=int(500//(ask*100))
 return {'status':'MAPPED' if contracts>=1 else 'PREMIUM_TOO_HIGH','spot':spot,'target_strike':target_strike,'contract':q['option'],'expiry':str(z['expiry']),'dte':(z['expiry']-asof).days,'strike':z['strike'],'bid':bid,'ask':ask,'mid':mid,'spread_pct':spread,'bid_size':q.get('bid_size'),'ask_size':q.get('ask_size'),'open_interest':q.get('open_interest'),'volume':q.get('volume'),'iv':q.get('iv'),'delta':q.get('delta'),'contracts_under_500_at_ask':contracts}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--quiet',action='store_true');a=ap.parse_args();now=dt.datetime.now(dt.timezone.utc);day=now.date();capture_id=now.strftime('%Y%m%dT%H%M%S%fZ');outdir=RAW/day.isoformat()/capture_id;outdir.mkdir(parents=True,exist_ok=True);prev='GENESIS'
 if MANIFEST.exists():
  lines=MANIFEST.read_text().splitlines();prev=json.loads(lines[-1])['record_hash'] if lines else prev
 picks=[];fail=[]
 for s in SYMBOLS:
  try:
   u=f'https://cdn.cboe.com/api/global/delayed_quotes/options/{s}.json';r=requests.get(u,headers=HEAD,timeout=45);r.raise_for_status();payload=r.content;j=r.json();gz=gzip.compress(payload,compresslevel=9);fn=outdir/f'{s}.json.gz';fn.write_bytes(gz);data=j['data'];feed_time=j.get('timestamp') or data.get('last_trade_time');pick=choose(data,day);pick.update({'capture_utc':now.isoformat(),'symbol':s,'feed_timestamp':feed_time,'raw_sha256':sha(payload),'gzip_sha256':sha(gz),'source_url':u});picks.append(pick)
  except Exception as e:fail.append({'symbol':s,'error':repr(e)})
 record={'schema_version':1,'capture_utc':now.isoformat(),'date':day.isoformat(),'symbols_requested':SYMBOLS,'symbols_captured':[x['symbol'] for x in picks],'failures':fail,'raw_files':[{'symbol':x['symbol'],'path':f"raw/{day.isoformat()}/{capture_id}/{x['symbol']}.json.gz",'raw_sha256':x['raw_sha256'],'gzip_sha256':x['gzip_sha256']} for x in picks],'previous_record_hash':prev};record['record_hash']=sha(canonical(record));ROOT.mkdir(exist_ok=True);withline=json.dumps(record,sort_keys=True);MANIFEST.open('a',encoding='utf-8').write(withline+'\n')
 import csv
 new=not PICKS.exists()
 with PICKS.open('a',newline='',encoding='utf-8') as f:
  fields=['capture_utc','symbol','feed_timestamp','status','spot','target_strike','contract','expiry','dte','strike','bid','ask','mid','spread_pct','bid_size','ask_size','open_interest','volume','iv','delta','contracts_under_500_at_ask','raw_sha256','gzip_sha256','source_url'];w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');
  if new:w.writeheader()
  w.writerows(picks)
 if not a.quiet:print(json.dumps({'record_hash':record['record_hash'],'captured':len(picks),'failures':fail,'mapped':sum(x.get('status')=='MAPPED' for x in picks),'selections':picks},indent=2))
 return 1 if not picks else 0
if __name__=='__main__':sys.exit(main())
