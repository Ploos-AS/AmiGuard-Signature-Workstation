import importlib.util
import json
import os
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("asw_retention", ROOT / "tools" / "asw_retention.py")
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
SHA = "ef" * 32


def setup(root: Path, state="closed", age_days=10):
    (root / "queue").mkdir(parents=True)
    ws = root / "work" / "sample-1"; ws.mkdir(parents=True)
    marker = ws / r.MARKER
    marker.write_text(json.dumps({"schema":1,"sample_id":"sample-1","sample_sha256":SHA}))
    (ws / "copy.bin").write_bytes(b"harmless fixture")
    (root / "queue" / "sample-1.json").write_text(json.dumps({"schema":1,"sample_id":"sample-1","sample_sha256":SHA,"state":state,"history":[{}]}))
    old = time.time() - age_days * 86400
    os.utime(marker, (old, old))
    return ws


class RetentionTests(unittest.TestCase):
    def test_closed_old_workspace_eligible(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); setup(root)
            self.assertTrue(r.inspect_workspace(root,"sample-1")["eligible"])
    def test_active_workspace_not_eligible(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); setup(root,state="qualification")
            self.assertFalse(r.inspect_workspace(root,"sample-1")["eligible"])
    def test_too_new_not_eligible(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); setup(root,age_days=1)
            self.assertFalse(r.inspect_workspace(root,"sample-1",min_age_days=7)["eligible"])
    def test_sha_confirmation_required(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); setup(root)
            with self.assertRaisesRegex(ValueError,"confirmation sha256"):
                r.purge_workspace(root,"sample-1","00"*32)
    def test_purge_removes_only_workspace(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); ws=setup(root); (root/"originals").mkdir(); protected=root/"originals"/"keep.sample"; protected.write_bytes(b"keep")
            r.purge_workspace(root,"sample-1",SHA)
            self.assertFalse(ws.exists()); self.assertTrue(protected.exists()); self.assertTrue((root/"queue"/"sample-1.json").exists())
    def test_workspace_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); setup(root); target=root/"outside"; target.mkdir(); link=root/"work"/"sample-1"/"link"; link.symlink_to(target,target_is_directory=True)
            with self.assertRaisesRegex(ValueError,"contains symlink"):
                r.inspect_workspace(root,"sample-1")
    def test_marker_identity_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); ws=setup(root); (ws/r.MARKER).write_text(json.dumps({"schema":1,"sample_id":"other","sample_sha256":SHA}))
            with self.assertRaisesRegex(ValueError,"identity mismatch"):
                r.inspect_workspace(root,"sample-1")

if __name__ == "__main__": unittest.main()
