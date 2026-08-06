#!/usr/bin/env python
"""Verify the append-only prospective evidence hash chain and raw snapshot hashes."""
import gzip,hashlib,json,sys
from pathlib import Path
ROOT=Path('prospective_shadow');MANIFEST=ROOT/'evidence_chain.jsonl'
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 prev='GENESIS';n=0;errors=[]
 for line in MANIFEST.read_text().splitlines():
  r=json.loads(line);claimed=r.pop('record_hash',None)
  if r.get('previous_record_hash')!=prev:errors.append(f'record {n}: previous hash mismatch')
  actual=sha(canonical(r))
  if claimed!=actual:errors.append(f'record {n}: record hash mismatch')
  day=r['date']
  for f in r['raw_files']:
   p=ROOT/f['path']
   if not p.exists():errors.append(f'missing {p}');continue
   gz=p.read_bytes()
   if sha(gz)!=f['gzip_sha256']:errors.append(f'gzip hash mismatch {p}')
   if sha(gzip.decompress(gz))!=f['raw_sha256']:errors.append(f'raw hash mismatch {p}')
  prev=claimed;n+=1
 print(json.dumps({'records':n,'valid':not errors,'latest_hash':prev,'errors':errors},indent=2));return 1 if errors else 0
if __name__=='__main__':sys.exit(main())
