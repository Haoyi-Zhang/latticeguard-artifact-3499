#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[0]
sys.path.insert(0, str(ROOT))
from latticeguard.github_sync import build_sync_manifest, write_manifest

def main():
    entries=build_sync_manifest(REPO)
    out=ROOT/'results'/'github_sync_manifest.csv'
    write_manifest(REPO, out)
    counts={}
    for e in entries:
        counts[e.upload_mode]=counts.get(e.upload_mode,0)+1
    report={'status':'PASS','entries':len(entries),'upload_modes':counts,'manifest':'results/github_sync_manifest.csv'}
    print(json.dumps(report, indent=2, sort_keys=True))
if __name__=='__main__': main()
