# M7.10 — Verified AmiGuard route import

M7.10 is the ASW-side half of the public AmiGuard handoff. The public intake/export side is not trusted merely because routing succeeded. ASW independently validates the routing manifest and sample before placing the sample into its immutable originals store and platform queue.

## Command

`python3 tools/asw_route_import.py --asw-root <root> --sample <id>.sample --route-manifest <id>.route.json`

The importer:

1. requires an existing non-symlink ASW root;
2. validates the strict `amiguard-asw-routing-manifest` schema;
3. validates platform-to-ASW namespace mapping;
4. requires sample and manifest filenames to match the submission ID;
5. re-hashes the routed sample and verifies exact size;
6. imports through the existing verified immutable intake path;
7. stores the immutable original under the selected platform root;
8. creates a new platform queue record with `status: new`;
9. writes an acknowledgement record;
10. leaves `analysis_started: false` and does not invoke any sandbox.

## Platform mapping

- `amiga` -> ASW namespace `amiga`
- `atari-st` -> ASW namespace `atari`
- `mac68k` -> ASW namespace `mac68k`

The ASW host layout therefore expects existing platform roots such as `<asw-root>/amiga`, `<asw-root>/atari`, and `<asw-root>/mac68k`. Missing roots fail closed instead of being silently activated.

## Queue and acknowledgement

For submission `<id>` the selected platform root receives:

- `queue/<id>.json` using schema `asw.platform.queue/1`
- `acks/<id>.json` using schema `asw.route.ack/1`

Both records bind platform, namespace, submission ID, ASW sample ID, SHA-256, exact size and import state. A successful acknowledgement means only that ASW accepted and re-verified the handoff. It does not mean the sample is infected, analysed, approved, signed, or publishable.

Duplicate queue registration fails closed. Existing immutable content may be de-duplicated by SHA-256 only after its bytes are re-verified by the existing ASW intake implementation.

## Qualification gate

Repository tests must prove successful import for Amiga, Atari ST and Mac 68k, correct platform queue placement, read-only immutable originals, no automatic analysis, rejection of tampered samples, rejection of platform/namespace mismatch, rejection of inactive platform roots and refusal of duplicate queue registration.
