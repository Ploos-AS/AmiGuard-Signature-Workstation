from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
import asw_route_import as route_import  # noqa: E402


class RouteImportTests(unittest.TestCase):
    def make_handoff(self, base: Path, platform: str, namespace: str, submission_id: str, payload: bytes):
        inbox = base / "handoff" / namespace
        inbox.mkdir(parents=True)
        sample = inbox / f"{submission_id}.sample"
        sample.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        route = {
            "schema_version": 1,
            "kind": "amiguard-asw-routing-manifest",
            "submission_id": submission_id,
            "platform": platform,
            "asw_namespace": namespace,
            "sha256": digest,
            "size": len(payload),
            "received_at": "2026-09-12T10:00:00Z",
            "routed_at": "2026-09-12T10:05:00Z",
            "source": "amiguard-public-quarantine",
        }
        route_path = inbox / f"{submission_id}.route.json"
        route_path.write_text(json.dumps(route) + "\n", encoding="utf-8")
        return sample, route_path, digest

    def prepare_asw(self, base: Path):
        root = base / "asw"
        root.mkdir()
        for ns in ("amiga", "atari", "mac68k"):
            (root / ns).mkdir()
        return root

    def test_imports_all_supported_platforms(self):
        cases = (("amiga", "amiga"), ("atari-st", "atari"), ("mac68k", "mac68k"))
        for idx, (platform, namespace) in enumerate(cases, 1):
            with self.subTest(platform=platform), tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp)
                asw = self.prepare_asw(base)
                sid = f"{idx:032x}"
                sample, route, digest = self.make_handoff(base, platform, namespace, sid, platform.encode())
                ack = route_import.import_route(asw, sample, route)
                self.assertEqual(ack["result"], "ACCEPTED")
                self.assertEqual(ack["asw_namespace"], namespace)
                self.assertEqual(ack["sha256"], digest)
                self.assertFalse(ack["analysis_started"])
                queue = json.loads((asw / namespace / "queue" / f"{sid}.json").read_text())
                self.assertEqual(queue["status"], "new")
                self.assertFalse(queue["analysis_started"])
                original = asw / namespace / "originals" / "sha256" / digest[:2] / f"{digest}.sample"
                self.assertEqual(original.read_bytes(), platform.encode())
                self.assertEqual(original.stat().st_mode & 0o777, 0o400)

    def test_rejects_tampered_sample(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            asw = self.prepare_asw(base)
            sid = "a" * 32
            sample, route, _ = self.make_handoff(base, "atari-st", "atari", sid, b"original")
            sample.write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "hash/size"):
                route_import.import_route(asw, sample, route)
            self.assertFalse((asw / "atari" / "queue").exists())

    def test_rejects_platform_namespace_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            asw = self.prepare_asw(base)
            sid = "b" * 32
            sample, route, _ = self.make_handoff(base, "mac68k", "amiga", sid, b"fixture")
            with self.assertRaisesRegex(ValueError, "platform/namespace mismatch"):
                route_import.import_route(asw, sample, route)

    def test_rejects_missing_platform_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            asw = base / "asw"
            asw.mkdir()
            sid = "c" * 32
            sample, route, _ = self.make_handoff(base, "atari-st", "atari", sid, b"fixture")
            with self.assertRaises((FileNotFoundError, ValueError)):
                route_import.import_route(asw, sample, route)

    def test_duplicate_import_fails_closed_at_queue_registration(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            asw = self.prepare_asw(base)
            sid = "d" * 32
            sample, route, _ = self.make_handoff(base, "amiga", "amiga", sid, b"fixture")
            route_import.import_route(asw, sample, route)
            with self.assertRaises(FileExistsError):
                route_import.import_route(asw, sample, route)


if __name__ == "__main__":
    unittest.main()
