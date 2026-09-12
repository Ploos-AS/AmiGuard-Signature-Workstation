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
        priorities = [p["priority"] for p in self.platforms]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(namespaces), len(set(namespaces)))
        self.assertEqual(len(priorities), len(set(priorities)))

    def test_expected_platform_roadmap_exists(self):
        by_id = {p["id"]: p for p in self.platforms}
        expected = {
            "amiga",
            "atari-st",
            "mac68k",
            "x68000",
            "next68k",
            "sun3",
            "sinclair-ql",
        }
        self.assertEqual(set(by_id), expected)
        self.assertEqual(by_id["amiga"]["runtime_backend"], "amisandbox")
        self.assertEqual(by_id["atari-st"]["runtime_backend"], "atarisandbox")
        self.assertEqual(by_id["mac68k"]["runtime_backend"], "macsandbox")
        self.assertEqual(by_id["x68000"]["runtime_backend"], "x68ksandbox")

    def test_canonical_sandbox_repositories_are_explicit(self):
        by_id = {p["id"]: p for p in self.platforms}
        expected = {
            "amiga": "https://github.com/Ploos-AS/AmiSandbox",
            "atari-st": "https://github.com/Ploos-AS/AtariSandbox",
            "mac68k": "https://github.com/Ploos-AS/MacSandbox",
        }
        for platform_id, repository in expected.items():
            self.assertEqual(by_id[platform_id]["runtime_backend_repository"], repository)
            self.assertEqual(by_id[platform_id]["runtime_backend_role"], "canonical")

    def test_roadmap_backends_are_reserved_not_fake_repositories(self):
        by_id = {p["id"]: p for p in self.platforms}
        for platform_id in ("x68000", "next68k", "sun3", "sinclair-ql"):
            self.assertIsNone(by_id[platform_id]["runtime_backend_repository"])
            self.assertEqual(by_id[platform_id]["runtime_backend_role"], "reserved")

    def test_only_qualified_platform_is_active(self):
        by_id = {p["id"]: p for p in self.platforms}
        self.assertEqual(by_id["amiga"]["status"], "active")
        self.assertEqual(by_id["atari-st"]["status"], "planned")
        self.assertEqual(by_id["mac68k"]["status"], "planned")
        for platform_id in ("x68000", "next68k", "sun3", "sinclair-ql"):
            self.assertEqual(by_id[platform_id]["status"], "roadmap")

    def test_all_platforms_have_explicit_backend_and_family(self):
        for platform in self.platforms:
            self.assertTrue(platform["runtime_backend"])
            self.assertTrue(platform["family"])
            self.assertTrue(platform["emulator_base"])
            self.assertTrue(platform["storage_namespace"])

    def test_storage_namespaces_are_cross_platform_unique(self):
        namespaces = [p["storage_namespace"] for p in self.platforms]
        self.assertEqual(len(namespaces), len(set(namespaces)))

    def test_security_defaults_are_deny_by_default(self):
        inv = self.data["invariants"]
        self.assertEqual(inv["cross_platform_writable_storage"], "forbidden")
        self.assertEqual(inv["external_guest_network_default"], "disabled")
        self.assertEqual(inv["shared_guest_host_folders_default"], "disabled")
        self.assertTrue(inv["immutable_originals"])
        self.assertEqual(inv["hash_algorithm"], "sha256")
        self.assertTrue(inv["core_must_not_assume_cpu_family"])
        self.assertTrue(inv["platform_activation_requires_backend_contract"])
        self.assertTrue(inv["canonical_backend_must_be_repository_pinned"])


if __name__ == "__main__":
    unittest.main()
