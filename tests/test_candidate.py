import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("asw_candidate", Path(__file__).parents[1] / "tools" / "asw_candidate.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

SHA = "11" * 32


def base_candidate():
    return {
        "schema": 1,
        "id": "synthetic-candidate-001",
        "name": "Synthetic Candidate",
        "family": "Synthetic",
        "kind": "file",
        "status": "candidate",
        "sample_sha256": SHA,
        "derivation": "synthetic unit-test fixture",
        "evidence": {
            "sample_sha256": SHA,
            "sources": ["static-analysis", "manual-review"]
        },
        "signature": {"type": "exact-sha256", "sha256": SHA},
        "gates": {
            "clean_corpus": "pending",
            "native_runtime": "pending",
            "manual_review": "pending"
        }
    }


class CandidateTests(unittest.TestCase):
    def test_exact_candidate_valid(self):
        self.assertEqual(MOD.validate_candidate(base_candidate())["id"], "synthetic-candidate-001")

    def test_hash_mismatch_rejected(self):
        c = base_candidate()
        c["signature"]["sha256"] = "22" * 32
        with self.assertRaises(ValueError):
            MOD.validate_candidate(c)

    def test_masked_pattern_valid(self):
        c = base_candidate()
        c["signature"] = {
            "type": "masked-pattern",
            "offset": 16,
            "pattern_hex": "0011223344556677",
            "mask_hex": "ffffffff00ffffff"
        }
        MOD.validate_candidate(c)

    def test_short_masked_pattern_rejected(self):
        c = base_candidate()
        c["signature"] = {"type": "masked-pattern", "offset": 0, "pattern_hex": "0011", "mask_hex": "ffff"}
        with self.assertRaises(ValueError):
            MOD.validate_candidate(c)

    def test_gate_order_enforced(self):
        c = base_candidate()
        c["gates"]["native_runtime"] = "pass"
        with self.assertRaises(ValueError):
            MOD.validate_candidate(c)

    def test_export_is_research_only(self):
        out = MOD.export_amiguard(base_candidate())
        self.assertEqual(out["status"], "research")
        self.assertEqual(out["sample_sha256"], SHA)
        self.assertTrue(out["research"]["asw_candidate"])
        self.assertEqual(out["cleaner"], "none")

    def test_load_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "c.json"
            target.write_text(json.dumps(base_candidate()), encoding="utf-8")
            link = root / "link.json"
            link.symlink_to(target)
            with self.assertRaises(ValueError):
                MOD.load(link)


if __name__ == "__main__":
    unittest.main()
