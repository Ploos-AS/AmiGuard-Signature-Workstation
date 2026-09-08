import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("asw_audit",ROOT/"tools"/"asw_audit.py")
a=importlib.util.module_from_spec(spec); spec.loader.exec_module(a)
SHA="cd"*32

class AuditTests(unittest.TestCase):
    def test_chain_verifies(self):
        events=[]
        for action in ("imported","static-analysis-started","candidate-created"):
            e=a.make_event(events,"sample-1",SHA,"analyst",action); events.append(e)
        r=a.verify_events(events); self.assertEqual(r["events"],3); self.assertEqual(r["head"],events[-1]["event_hash"])
    def test_tamper_detected(self):
        events=[]; events.append(a.make_event(events,"sample-1",SHA,"analyst","imported")); events[0]["action"]="changed"
        with self.assertRaisesRegex(ValueError,"hash mismatch"): a.verify_events(events)
    def test_reorder_detected(self):
        events=[]
        for action in ("one","two"): events.append(a.make_event(events,"sample-1",SHA,"analyst",action))
        with self.assertRaises(ValueError): a.verify_events(list(reversed(events)))
    def test_append_and_read(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"audit.jsonl"; events=[]
            e=a.make_event(events,"sample-1",SHA,"analyst","imported"); a.append(p,e)
            self.assertEqual(a.read_events(p)[0]["event_hash"],e["event_hash"])
            self.assertEqual(p.stat().st_mode & 0o777,0o600)
    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); real=p/"real"; real.write_text(""); link=p/"audit"; link.symlink_to(real)
            with self.assertRaisesRegex(ValueError,"non-symlink"): a.read_events(link)
    def test_bad_identity_rejected(self):
        with self.assertRaisesRegex(ValueError,"sha256"): a.make_event([],"sample-1","bad","analyst","imported")
    def test_previous_hash_tamper_detected(self):
        events=[]; events.append(a.make_event(events,"sample-1",SHA,"analyst","one")); events.append(a.make_event(events,"sample-1",SHA,"analyst","two")); events[1]["previous_hash"]="0"*64; events[1]["event_hash"]=a.event_hash(events[1])
        with self.assertRaisesRegex(ValueError,"broken hash chain"): a.verify_events(events)

if __name__=="__main__": unittest.main()
