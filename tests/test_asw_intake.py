import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

from tools.asw_intake import import_sample


SUBMISSION_ID = "0123456789abcdef0123456789abcdef"


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.base = Path(self.td.name)
        self.sample = self.base / "transport.bin"
        self.payload = b"ASW harmless M1 qualification fixture\n"
        self.sample.write_bytes(self.payload)
        self.sha = hashlib.sha256(self.payload).hexdigest()
        self.root = self.base / "private"

    def tearDown(self):
        self.td.cleanup()

    def do_import(self):
        return import_sample(
            self.root,
            self.sample,
            SUBMISSION_ID,
            self.sha,
            len(self.payload),
            "synthetic unit-test export",
        )

    def test_verified_import_seals_original_and_manifest(self):
        manifest = self.do_import()
        original = self.root / "originals" / "sha256" / self.sha[:2] / f"{self.sha}.sample"
        metadata = self.root / "manifests" / f"{self.sha}.json"
        self.assertEqual(original.read_bytes(), self.payload)
        self.assertEqual(os.stat(original).st_mode & 0o777, 0o400)
        on_disk = json.loads(metadata.read_text())
        self.assertEqual(on_disk["sha256"], self.sha)
        self.assertEqual(on_disk["asw_sample_id"], self.sha)
        self.assertEqual(on_disk["source_submission_id"], SUBMISSION_ID)
        self.assertTrue(on_disk["export_verified"])
        self.assertTrue(on_disk["import_verified"])
        self.assertFalse(on_disk["executed_on_host"])
        self.assertNotIn("transport.bin", json.dumps(on_disk))
        self.assertEqual(manifest["analysis_status"], "new")

    def test_sha_mismatch_fails_before_private_commit(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            import_sample(
                self.root,
                self.sample,
                SUBMISSION_ID,
                "0" * 64,
                len(self.payload),
                "synthetic unit-test export",
            )
        self.assertFalse(self.root.exists())

    def test_size_mismatch_fails_before_private_commit(self):
        with self.assertRaisesRegex(ValueError, "size"):
            import_sample(
                self.root,
                self.sample,
                SUBMISSION_ID,
                self.sha,
                len(self.payload) + 1,
                "synthetic unit-test export",
            )
        self.assertFalse(self.root.exists())

    def test_symlink_source_rejected(self):
        link = self.base / "link.bin"
        link.symlink_to(self.sample)
        with self.assertRaisesRegex(ValueError, "symlink"):
            import_sample(
                self.root,
                link,
                SUBMISSION_ID,
                self.sha,
                len(self.payload),
                "synthetic unit-test export",
            )
        self.assertFalse(self.root.exists())

    def test_repeat_import_does_not_overwrite_original(self):
        self.do_import()
        self.do_import()
        original = self.root / "originals" / "sha256" / self.sha[:2] / f"{self.sha}.sample"
        self.assertEqual(original.read_bytes(), self.payload)
        self.assertEqual(os.stat(original).st_mode & 0o777, 0o400)


if __name__ == "__main__":
    unittest.main()
