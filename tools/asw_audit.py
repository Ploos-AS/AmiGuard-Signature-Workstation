#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{64}$")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
ACTOR_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._@-]{0,127}$")
ZERO = "0" * 64


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def event_hash(event):
    body = dict(event); body.pop("event_hash", None)
    return hashlib.sha256(canonical(body)).hexdigest()


def validate_input(sample_id, sha256, actor, action, note=None):
    if not ID_RE.fullmatch(sample_id): raise ValueError("invalid sample id")
    if not SHA_RE.fullmatch(sha256): raise ValueError("invalid sample sha256")
    if not ACTOR_RE.fullmatch(actor): raise ValueError("invalid actor")
    if not action or len(action) > 128 or any(ord(c) < 32 for c in action): raise ValueError("invalid action")
    if note is not None and (len(note) > 1024 or any(ord(c) < 32 and c not in "\t" for c in note)): raise ValueError("invalid note")


def read_events(path):
    if not path.exists(): return []
    if path.is_symlink() or not path.is_file(): raise ValueError("audit log must be regular non-symlink file")
    events=[]
    with path.open("r", encoding="utf-8") as f:
        for n,line in enumerate(f,1):
            try: e=json.loads(line)
            except json.JSONDecodeError as exc: raise ValueError(f"invalid JSON at line {n}") from exc
            events.append(e)
    verify_events(events)
    return events


def verify_events(events):
    prev=ZERO
    for i,e in enumerate(events,1):
        if e.get("schema") != 1 or e.get("sequence") != i: raise ValueError(f"invalid sequence at event {i}")
        if e.get("previous_hash") != prev: raise ValueError(f"broken hash chain at event {i}")
        if not SHA_RE.fullmatch(e.get("event_hash", "")) or event_hash(e) != e["event_hash"]: raise ValueError(f"event hash mismatch at event {i}")
        validate_input(e.get("sample_id",""),e.get("sample_sha256",""),e.get("actor",""),e.get("action",""),e.get("note"))
        prev=e["event_hash"]
    return {"events":len(events),"head":prev}


def make_event(events, sample_id, sha256, actor, action, note=None):
    validate_input(sample_id,sha256,actor,action,note)
    prev=events[-1]["event_hash"] if events else ZERO
    e={"schema":1,"sequence":len(events)+1,"at":datetime.now(timezone.utc).isoformat(),"sample_id":sample_id,"sample_sha256":sha256,"actor":actor,"action":action,"previous_hash":prev}
    if note: e["note"]=note
    e["event_hash"]=event_hash(e)
    return e


def append(path,event):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.is_symlink(): raise ValueError("audit log must not be symlink")
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
    with os.fdopen(fd,"a",encoding="utf-8") as f:
        f.write(canonical(event).decode("ascii")+"\n"); f.flush(); os.fsync(f.fileno())


def main():
    p=argparse.ArgumentParser(description="ASW append-only hash-chained audit log")
    sub=p.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("append"); a.add_argument("--log",type=Path,required=True); a.add_argument("--sample-id",required=True); a.add_argument("--sha256",required=True); a.add_argument("--actor",required=True); a.add_argument("--action",required=True); a.add_argument("--note")
    v=sub.add_parser("verify"); v.add_argument("--log",type=Path,required=True)
    args=p.parse_args()
    if args.cmd=="verify":
        r=verify_events(read_events(args.log)); print(f"ASW audit: PASS events={r['events']} head={r['head']}"); return 0
    events=read_events(args.log); e=make_event(events,args.sample_id,args.sha256,args.actor,args.action,args.note); append(args.log,e); print(f"event {e['sequence']} {e['event_hash']}"); return 0

if __name__=="__main__": raise SystemExit(main())
