import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "asw_amisandbox.py"


class AmiSandboxAdapterTests(unittest.TestCase):
    def test_ingest_only_binds_sample_and_hashes_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sample = root / "sample.bin"
            sample.write_bytes(b"harmless synthetic sample\n")
            sample_sha = hashlib.sha256(sample.read_bytes()).hexdigest()

            analysis = root / "analysis"
            analysis.mkdir()
            (analysis / "session.json").write_text(
                json.dumps({"jit_enabled": False, "machine_profile": "a500-ks13"}) + "\n",
                encoding="utf-8",
            )
            (analysis / "events.jsonl").write_text(
                json.dumps({"type": "session.start", "schema_version": 1}) + "\n" +
                json.dumps({"type": "future.event", "payload": {"opaque": True}}) + "\n",
                encoding="utf-8",
            )

            evidence = root / "evidence"
            manifest = root / "runtime.json"
            cp = subprocess.run(
                [
                    sys.executable, str(TOOL),
                    "--sample", str(sample),
                    "--sample-id", "synthetic-001",
                    "--sample-sha256", sample_sha,
                    "--profile", "a500-ks13-68000",
                    "--analysis-dir", str(analysis),
                    "--evidence-dir", str(evidence),
                    "--manifest", str(manifest),
                    "--amisandbox-revision", "1bdf593d511b11cb4c400a6adeb622b9ab43ea4f",
                    "--amisandbox-build", "github-actions-runtime-qualified",
                    "--ingest-only",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(cp.returncode, 0, cp.stderr)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], "asw.amisandbox.runtime-evidence")
            self.assertEqual(data["sample"]["sha256"], sample_sha)
            self.assertEqual(data["runtime"]["backend"], "amisandbox")
            self.assertEqual(data["runtime"]["jit"], "disabled")
            self.assertEqual(data["runtime"]["network"], "disabled")
            self.assertEqual(data["runtime"]["asw_profile"], "a500-ks13-68000")
            self.assertEqual(data["runtime"]["amisandbox_profile"], "a500-ks13")
            self.assertEqual({a["name"] for a in data["artifacts"]}, {"session.json", "events.jsonl"})
            for artifact in data["artifacts"]:
                copied = Path(artifact["path"])
                self.assertTrue(copied.is_file())
                self.assertEqual(hashlib.sha256(copied.read_bytes()).hexdigest(), artifact["sha256"])

    def test_rejects_wrong_sample_hash(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sample = root / "sample.bin"
            sample.write_bytes(b"synthetic")
            analysis = root / "analysis"
            analysis.mkdir()
            (analysis / "session.json").write_text("{}\n", encoding="utf-8")
            (analysis / "events.jsonl").write_text("{}\n", encoding="utf-8")
            cp = subprocess.run(
                [
                    sys.executable, str(TOOL),
                    "--sample", str(sample),
                    "--sample-id", "x",
                    "--sample-sha256", "0" * 64,
                    "--profile", "a500-ks13-68000",
                    "--analysis-dir", str(analysis),
                    "--evidence-dir", str(root / "evidence"),
                    "--manifest", str(root / "manifest.json"),
                    "--amisandbox-revision", "deadbeef",
                    "--amisandbox-build", "test",
                    "--ingest-only",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(cp.returncode, 0)
            self.assertIn("SHA-256 mismatch", cp.stderr)

    def test_rejects_symlink_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sample = root / "sample.bin"
            sample.write_bytes(b"synthetic")
            analysis = root / "analysis"
            analysis.mkdir()
            outside = root / "outside.json"
            outside.write_text("{}\n", encoding="utf-8")
            (analysis / "session.json").symlink_to(outside)
            (analysis / "events.jsonl").write_text("{}\n", encoding="utf-8")
            cp = subprocess.run(
                [
                    sys.executable, str(TOOL),
                    "--sample", str(sample),
                    "--sample-id", "x",
                    "--profile", "a500-ks13-68000",
                    "--analysis-dir", str(analysis),
                    "--evidence-dir", str(root / "evidence"),
                    "--manifest", str(root / "manifest.json"),
                    "--amisandbox-revision", "deadbeef",
                    "--amisandbox-build", "test",
                    "--ingest-only",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(cp.returncode, 0)


if __name__ == "__main__":
    unittest.main()
