"""The marker `/finalize`'s attestation comment leads with
(`.claude/skills/finalize/attest.md`), on its own so the merge gate reads it
without `lib.github`, whose name `scripts/lib/` shares."""

from __future__ import annotations

import re

# `revoked` and a marker with no SHA are attestations that no longer hold.
MARKER = re.compile(r"<!-- finalize-attestation(?: ([0-9a-f]{40}|revoked))? -->")
