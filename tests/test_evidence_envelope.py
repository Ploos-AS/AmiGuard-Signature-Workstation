import copy
import unittest

from tools.asw_evidence_envelope import validate

PLATFORMS = {
    "amiga": {"storage_namespace": "amiga"},
    "atari-st": {"storage_namespace": "atari"},
    "mac68k": {"storage_namespace": "mac68k"},
}


def envelope(platform="amiga", namespace="amiga"):
    return {
        "schema": "asw.core.evidence/1",
        "platform": platform,
        "namespace": namespace,
        "sample": {"sha256": "a" * 64, "size": 123},
        "producer": {"kind": "runtime-backend", "name": "sandbox", "revision": "deadbeef"},
        "evidence": [{"role": "events", "sha256": "b" * 64, "size": 42}],
        "analysis_started": False,
    }


class EvidenceEnvelopeTests(unittest.TestCase):
    def test_platforms_share_same_cpu_agnostic_contract(self):
        for platform, namespace in (("amiga", "amiga"), ("atari-st", "atari"), ("mac68k", "mac68k")):
            validate(envelope(platform, namespace), PLATFORMS)

    def test_namespace_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "namespace mismatch"):
            validate(envelope("atari-st", "amiga"), PLATFORMS)

    def test_unknown_platform_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "unknown platform"):
            validate(envelope("unknown", "unknown"), PLATFORMS)

    def test_analysis_authorization_is_forbidden(self):
        doc = envelope()
        doc["analysis_started"] = True
        with self.assertRaisesRegex(ValueError, "must not authorize analysis"):
            validate(doc, PLATFORMS)

    def test_duplicate_evidence_role_fails_closed(self):
        doc = envelope()
        doc["evidence"].append(copy.deepcopy(doc["evidence"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate evidence role"):
            validate(doc, PLATFORMS)

    def test_cpu_specific_core_field_is_rejected(self):
        doc = envelope()
        doc["cpu"] = "68000"
        with self.assertRaisesRegex(ValueError, "field set mismatch"):
            validate(doc, PLATFORMS)


if __name__ == "__main__":
    unittest.main()
