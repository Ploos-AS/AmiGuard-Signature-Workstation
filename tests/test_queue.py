import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("asw_queue", ROOT / "tools" / "asw_queue.py")
q = importlib.util.module_from_spec(spec); spec.loader.exec_module(q)
SHA = "ab" * 32

class QueueTests(unittest.TestCase):
    def test_new_is_imported(self):
        self.assertEqual(q.new_record("sample-1", SHA)["state"], "imported")
    def test_happy_path(self):
        r = q.new_record("sample-1", SHA)
        for state in ("static-analysis", "runtime-analysis", "candidate", "qualification", "reviewed", "closed"):
            r = q.transition(r, state)
        self.assertEqual(r["state"], "closed")
        self.assertEqual(len(r["history"]), 7)
    def test_static_can_skip_runtime(self):
        r = q.transition(q.new_record("sample-1", SHA), "static-analysis")
        self.assertEqual(q.transition(r, "candidate")["state"], "candidate")
    def test_illegal_skip_rejected(self):
        with self.assertRaisesRegex(ValueError, "not allowed"):
            q.transition(q.new_record("sample-1", SHA), "qualification")
    def test_reject_terminal(self):
        r = q.transition(q.new_record("sample-1", SHA), "rejected")
        with self.assertRaisesRegex(ValueError, "not allowed"):
            q.transition(r, "static-analysis")
    def test_closed_terminal(self):
        r = q.new_record("sample-1", SHA)
        for state in ("static-analysis", "candidate", "qualification", "reviewed", "closed"): r = q.transition(r, state)
        with self.assertRaisesRegex(ValueError, "not allowed"):
            q.transition(r, "reviewed")
    def test_symlink_record_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); real=p/"real.json"; q.atomic_write(real, q.new_record("sample-1", SHA), create=True); link=p/"link.json"; link.symlink_to(real)
            with self.assertRaisesRegex(ValueError, "non-symlink"):
                q.load(link)
    def test_create_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"x.json"; q.atomic_write(p, q.new_record("sample-1", SHA), create=True)
            with self.assertRaises(FileExistsError): q.atomic_write(p, q.new_record("sample-1", SHA), create=True)

if __name__ == "__main__": unittest.main()
