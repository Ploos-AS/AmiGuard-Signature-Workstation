import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("asw_backup",ROOT/"tools"/"asw_backup.py")
b=importlib.util.module_from_spec(spec); spec.loader.exec_module(b)

class BackupTests(unittest.TestCase):
    def make_root(self, p):
        (p/"manifests").mkdir(); (p/"queue").mkdir(); (p/"audit").mkdir(); (p/"evidence").mkdir(); (p/"originals").mkdir()
        (p/"manifests"/"a.json").write_text("{}\n")
        (p/"queue"/"q.json").write_text("{}\n")
        (p/"audit"/"audit.jsonl").write_text("event\n")
        (p/"originals"/"sample.bin").write_bytes(b"harmless synthetic bytes")
    def test_default_excludes_originals(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); self.make_root(p); m=b.build_manifest(p)
            self.assertFalse(m["include_originals"]); self.assertFalse(any(x["path"].startswith("originals/") for x in m["files"]))
    def test_explicit_originals(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); self.make_root(p); m=b.build_manifest(p,True)
            self.assertTrue(any(x["path"]=="originals/sample.bin" for x in m["files"]))
    def test_verify_detects_change(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); self.make_root(p); m=b.build_manifest(p); (p/"queue"/"q.json").write_text("changed\n")
            with self.assertRaisesRegex(ValueError,"content mismatch"): b.verify_manifest(p,m)
    def test_verify_detects_extra(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); self.make_root(p); m=b.build_manifest(p); (p/"evidence"/"extra").write_text("x")
            with self.assertRaisesRegex(ValueError,"file set mismatch"): b.verify_manifest(p,m)
    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); self.make_root(p); (p/"queue"/"link").symlink_to(p/"queue"/"q.json")
            with self.assertRaisesRegex(ValueError,"non-regular"): b.build_manifest(p)
    def test_manifest_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); self.make_root(p); out=p/"backup-manifest.json"; b.write_manifest(out,b.build_manifest(p))
            with self.assertRaises(FileExistsError): b.write_manifest(out,b.build_manifest(p))

if __name__=="__main__": unittest.main()
