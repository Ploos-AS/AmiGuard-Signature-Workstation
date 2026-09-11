import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config" / "platforms.json"


class PlatformRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.platforms = cls.data["platforms"]

    def test_platform_ids_and_storage_namespaces_are_unique(self):
        ids = [p["id"] for p in self.platforms]
        namespaces = [p["storage_namespace"] for p in self.platforms]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(namespaces), len(set(namespaces)))

    def test_expected_initial_platforms_exist(self):
        by_id = {p["id"]: p for p in self.platforms}
        self.assertEqual(set(by_id), {"amiga", "atari-st", "mac68k"})
        self.assertEqual(by_id["amiga"]["runtime_backend"], "amisandbox")
        self.assertEqual(by_id["atari-st"]["runtime_backend"], "atarisandbox")
        self.assertEqual(by_id["mac68k"]["runtime_backend"], "macsandbox")

    def test_storage_namespaces_cannot_alias_other_platforms(self):
        by_id = {p["id"]: p for p in self.platforms}
        self.assertNotEqual(by_id["amiga"]["storage_namespace"], by_id["atari-st"]["storage_namespace"])
        self.assertNotEqual(by_id["amiga"]["storage_namespace"], by_id["mac68k"]["storage_namespace"])
        self.assertNotEqual(by_id["atari-st"]["storage_namespace"], by_id["mac68k"]["storage_namespace"])

    def test_security_defaults_are_deny_by_default(self):
        inv = self.data["invariants"]
        self.assertEqual(inv["cross_platform_writable_storage"], "forbidden")
        self.assertEqual(inv["external_guest_network_default"], "disabled")
        self.assertEqual(inv["shared_guest_host_folders_default"], "disabled")
        self.assertTrue(inv["immutable_originals"])
        self.assertEqual(inv["hash_algorithm"], "sha256")


if __name__ == "__main__":
    unittest.main()
