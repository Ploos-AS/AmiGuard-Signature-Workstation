import hashlib
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "asw_amiforensics.py"


class AmiForensicsAdapterTests(unittest.TestCase):
    def _fixture(self, root: Path):
        evidence = root / "evidence"
        evidence.mkdir()
        session = evidence / "session.json"
        events = evidence / "events.jsonl"
        session.write_text(json.dumps({"machine_profile": "a500-ks13"}) + "\n", encoding="utf-8")
        events.write_text(json.dumps({"type": "session.start"}) + "\n", encoding="utf-8")
        manifest = root / "runtime.json"
        manifest.write_text(json.dumps({
            "schema_version": 1,
            "kind": "asw.amisandbox.runtime-evidence",
            "sample": {"id": "synthetic-001", "sha256": "1" * 64},
            "artifacts": [
                {"name": session.name, "path": str(session), "sha256": hashlib.sha256(session.read_bytes()).hexdigest()},
                {"name": events.name, "path": str(events), "sha256": hashlib.sha256(events.read_bytes()).hexdigest()},
            ],
        }, sort_keys=True) + "\n", encoding="utf-8")
        return manifest, session, events

    def _fake_report_tool(self, root: Path) -> Path:
        tool = root / "report.py"
        tool.write_text(textwrap.dedent("""
            import argparse, hashlib, json
            from pathlib import Path
            def h(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
            ap = argparse.ArgumentParser()
            ap.add_argument('--manifest', required=True)
            ap.add_argument('--evidence', action='append', default=[])
            ap.add_argument('--output', required=True)
            a = ap.parse_args()
            out = {
                'schema': 'amiforensics.workstation.report/1',
                'manifest': {'name': Path(a.manifest).name, 'sha256': h(a.manifest), 'data': json.loads(Path(a.manifest).read_text())},
                'evidence': [{'name': Path(p).name, 'size': Path(p).stat().st_size, 'sha256': h(p), 'format': 'text', 'data': Path(p).read_text()} for p in a.evidence],
                'summary': {'evidence_count': len(a.evidence)},
            }
            Path(a.output).write_text(json.dumps(out, sort_keys=True) + '\\n')
        """), encoding="utf-8")
        return tool

    def test_generates_verified_binding(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest, _, _ = self._fixture(root)
            report_tool = self._fake_report_tool(root)
            report = root / "report.json"
            binding = root / "binding.json"
            cp = subprocess.run([
                sys.executable, str(TOOL),
                "--runtime-manifest", str(manifest),
                "--amiforensics-report-tool", str(report_tool),
                "--report", str(report),
                "--binding-manifest", str(binding),
                "--amiforensics-revision", "abc123",
            ], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(cp.returncode, 0, cp.stderr)
            data = json.loads(binding.read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], "asw.amiforensics.analysis")
            self.assertEqual(data["sample"]["id"], "synthetic-001")
            self.assertEqual(data["amiforensics"]["revision"], "abc123")
            self.assertEqual(data["amiforensics"]["report_sha256"], hashlib.sha256(report.read_bytes()).hexdigest())

    def test_rejects_tampered_runtime_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest, session, _ = self._fixture(root)
            session.write_text("tampered\n", encoding="utf-8")
            cp = subprocess.run([
                sys.executable, str(TOOL),
                "--runtime-manifest", str(manifest),
                "--amiforensics-report-tool", str(self._fake_report_tool(root)),
                "--report", str(root / "report.json"),
                "--binding-manifest", str(root / "binding.json"),
                "--amiforensics-revision", "abc123",
            ], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertNotEqual(cp.returncode, 0)
            self.assertIn("artifact SHA-256 mismatch", cp.stderr)


if __name__ == "__main__":
    unittest.main()
