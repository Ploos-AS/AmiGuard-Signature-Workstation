import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("asw_candidate", Path(__file__).parents[1] / "tools" / "asw_candidate.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

SHA = "11" * 32
BOOT_SHA = "22" * 32


def base_candidate():
    return {
        "schema": 1,
        "id": "synthetic-candidate-001",
        "name": "Synthetic Candidate",
        "family": "Synthetic",
        "kind": "file",
        "status": "candidate",
        "sample_sha256": SHA,
        "sample_size": 4096,
        "format": "hunk",
        "created_at": "2026-09-13T06:30:00Z",
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

    def test_export_aaa_file_sha256(self):
        out = MOD.export_aaa(base_candidate())
        self.assertEqual(out["schema"], 1)
        self.assertEqual(out["kind"], "file-sha256")
        self.assertEqual(out["sample_sha256"], SHA)
        self.assertEqual(out["sample_size"], 4096)
        self.assertEqual(out["source_engine"], "AmiGuard-Signature-Workstation")
        self.assertEqual(out["confidence"], "single-engine")
        self.assertTrue(out["id"].startswith("AAA.Amiga.Synthetic."))

    def test_export_aaa_confirmed_after_all_gates(self):
        c = base_candidate()
        c["gates"] = {"clean_corpus": "pass", "native_runtime": "pass", "manual_review": "pass"}
        self.assertEqual(MOD.export_aaa(c)["confidence"], "confirmed")

    def test_export_aaa_pattern_requires_exact_mask(self):
        c = base_candidate()
        c["signature"] = {
            "type": "masked-pattern",
            "offset": 16,
            "pattern_hex": "0011223344556677",
            "mask_hex": "ffffffff00ffffff"
        }
        with self.assertRaises(ValueError):
            MOD.export_aaa(c)
        c["signature"]["mask_hex"] = "ff" * 8
        out = MOD.export_aaa(c)
        self.assertEqual(out["kind"], "pattern")
        self.assertEqual(out["pattern"]["offset"], 16)

    def test_export_aaa_bootblock_hash(self):
        c = base_candidate()
        c["kind"] = "bootblock"
        c["bootblock_sha256"] = BOOT_SHA
        c["signature"] = {"type": "exact-sha256", "sha256": BOOT_SHA}
        out = MOD.export_aaa(c)
        self.assertEqual(out["kind"], "bootblock-sha256")
        self.assertEqual(out["bootblock_sha256"], BOOT_SHA)

    def test_export_clamav_sha256_hsb(self):
        ext, line = MOD.export_clamav(base_candidate())
        self.assertEqual(ext, ".hsb")
        self.assertTrue(line.startswith(f"{SHA}:4096:"))
        self.assertIn("Amiga.Synthetic.synthetic-candidate-001", line)

    def test_export_clamav_masked_ndb(self):
        c = base_candidate()
        c["signature"] = {
            "type": "masked-pattern",
            "offset": 32,
            "pattern_hex": "a1b2c3d4e5f60718",
            "mask_hex": "ffff00fff00fffff"
        }
        ext, line = MOD.export_clamav(c)
        self.assertEqual(ext, ".ndb")
        self.assertTrue(line.endswith(":32:a1b2??d4e?f?0718"))

    def test_export_clamav_rejects_unrepresentable_mask(self):
        c = base_candidate()
        c["signature"] = {
            "type": "masked-pattern",
            "offset": 0,
            "pattern_hex": "0011223344556677",
            "mask_hex": "ff7fffffffffffff"
        }
        with self.assertRaises(ValueError):
            MOD.export_clamav(c)

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
