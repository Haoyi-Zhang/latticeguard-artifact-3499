#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
RESULTS=ROOT/'results'; EVIDENCE=ROOT/'evidence'; SCRIPT=ROOT/'scripts'/'run_full_evaluation.py'; SEEDS=['0','1','42']

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def read_hash_ledger() -> dict[str,str]:
    with (EVIDENCE/'SHA256SUMS.csv').open('r',encoding='utf-8',newline='') as f: return {r['path']:r['sha256'] for r in csv.DictReader(f)}

def write_json(path: Path, data) -> None: path.write_text(json.dumps(data,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')

def authoritative_hash_rows():
    sys.path.insert(0,str(ROOT/'scripts'))
    import run_full_evaluation as rfe  # type: ignore
    return rfe.write_hashes()

def write_robustness(status, compared, mismatches, mode, seed_hashes=None):
    write_json(RESULTS/'robustness.json', {'status':status,'mode':mode,'seeds':SEEDS if seed_hashes else [],'baseline_seed':SEEDS[0],'compared_files':compared,'mismatches':mismatches,'seed_hashes':seed_hashes or {},'note':'Default mode recomputes the authoritative SHA-256 ledger. Set LATTICEGUARD_FULL_ROBUSTNESS=1 for expensive multi-seed reruns.'})
    with (RESULTS/'robustness.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['seed','status','compared_files','mismatches','mode']); w.writeheader()
        if seed_hashes:
            for seed in SEEDS: w.writerow({'seed':seed,'status':status,'compared_files':len(compared),'mismatches':len([m for m in mismatches if m.get('seed')==seed]),'mode':mode})
        else: w.writerow({'seed':'ledger','status':status,'compared_files':len(compared),'mismatches':len(mismatches),'mode':mode})

def fast_mode():
    rows=authoritative_hash_rows(); mismatches=[]
    for r in rows:
        obs=sha256_file(ROOT/r['path'])
        if obs!=r['sha256']: mismatches.append({'path':r['path'],'expected':r['sha256'],'observed':obs})
    status='passed' if not mismatches else 'failed'
    write_robustness(status,[r['path'] for r in rows],mismatches,'ledger-hash-replay')
    rows=authoritative_hash_rows()
    print(json.dumps({'status':status,'mode':'ledger-hash-replay','compared_files':len(rows),'hash_rows':len(rows),'mismatches':len(mismatches)},indent=2,sort_keys=True))
    if mismatches: raise SystemExit(1)

def full_mode():
    seed_hashes={}
    for seed in SEEDS:
        env=os.environ.copy(); env['PYTHONHASHSEED']=seed; env['PYTHONDONTWRITEBYTECODE']='1'
        subprocess.run([sys.executable,'-B',str(SCRIPT)],cwd=str(ROOT),env=env,check=True,stdout=subprocess.DEVNULL)
        seed_hashes[seed]=read_hash_ledger()
    keys=set(seed_hashes[SEEDS[0]]); mismatches=[]
    for seed in SEEDS[1:]:
        if set(seed_hashes[seed])!=keys: mismatches.append({'seed':seed,'reason':'path-set differs'})
        for path in sorted(keys & set(seed_hashes[seed])):
            if seed_hashes[seed][path]!=seed_hashes[SEEDS[0]][path]: mismatches.append({'seed':seed,'path':path,'baseline_hash':seed_hashes[SEEDS[0]][path],'observed_hash':seed_hashes[seed][path]})
    status='passed' if not mismatches else 'failed'; write_robustness(status,sorted(keys),mismatches,'full-multi-seed-rerun',seed_hashes); rows=authoritative_hash_rows()
    print(json.dumps({'status':status,'mode':'full-multi-seed-rerun','compared_files':len(keys),'hash_rows':len(rows),'mismatches':len(mismatches)},indent=2,sort_keys=True))
    if mismatches: raise SystemExit(1)

def main():
    full_mode() if os.environ.get('LATTICEGUARD_FULL_ROBUSTNESS')=='1' else fast_mode()
if __name__=='__main__': main()
