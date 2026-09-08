import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec_c = importlib.util.spec_from_file_location("asw_candidate", ROOT / "tools" / "asw_candidate.py")
c = importlib.util.module_from_spec(spec_c)
spec_c.loader.exec_module(c)
sys.modules["asw_candidate"] = c
spec = importlib.util.spec_from_file_location("asw_qualify", ROOT / "tools" / "asw_qualify.py")
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)

SHA = "11" * 32


def candidate():
    return {"schema":1,"id":"test.candidate","name":"Test","family":"Test","kind":"file","status":"candidate","sample_sha256":SHA,"evidence":{"sample_sha256":SHA,"sources":["static.json"]},"signature":{"type":"exact-sha256","sha256":SHA},"gates":{"clean_corpus":"pending","native_runtime":"pending","manual_review":"pending"}}


def ev(gate, result="pass"):
    return {"schema":1,"gate":gate,"candidate_id":"test.candidate","sample_sha256":SHA,"result":result,"evidence":["qualification artifact"]}


class QualifyTests(unittest.TestCase):
    def test_clean_corpus_pass(self):
        out = q.apply_gate(candidate(), "clean_corpus", ev("clean_corpus"))
        self.assertEqual(out["gates"]["clean_corpus"], "pass")

    def test_native_requires_clean(self):
        with self.assertRaisesRegex(ValueError, "clean corpus"):
            q.apply_gate(candidate(), "native_runtime", ev("native_runtime"))

    def test_manual_requires_native(self):
        x = candidate(); x["gates"]["clean_corpus"] = "pass"
        with self.assertRaisesRegex(ValueError, "native runtime"):
            q.apply_gate(x, "manual_review", ev("manual_review"))

    def test_full_gate_sequence(self):
        x = q.apply_gate(candidate(), "clean_corpus", ev("clean_corpus"))
        x = q.apply_gate(x, "native_runtime", ev("native_runtime"))
        x = q.apply_gate(x, "manual_review", ev("manual_review"))
        self.assertEqual(x["gates"], {"clean_corpus":"pass","native_runtime":"pass","manual_review":"pass"})

    def test_hash_mismatch_rejected(self):
        e = ev("clean_corpus"); e["sample_sha256"] = "22" * 32
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            q.apply_gate(candidate(), "clean_corpus", e)

    def test_fail_is_recorded(self):
        out = q.apply_gate(candidate(), "clean_corpus", ev("clean_corpus", "fail"))
        self.assertEqual(out["gates"]["clean_corpus"], "fail")


if __name__ == "__main__":
    unittest.main()
