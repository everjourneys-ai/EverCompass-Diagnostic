"""
DiagnosticRepository -- owns loading diagnostic definitions from disk and
resolving (diagnostic_id, version) to one, so nothing above this layer
touches the filesystem or re-implements that lookup.

v1.0 has exactly one diagnostic definition file. The repository is built
to hold more than one anyway (keyed by (diagnostic_id, version), loaded
from an explicit list of paths) so that adding a second file later -- a
new diagnostic, or a new version of this one -- is a one-line change
where the repository is constructed, not a repository rewrite.

Only "published" definitions are ever returned. Design Spec section 24 /
Architecture v1.2 treat a published diagnostic version as immutable;
this application enforces that at the boundary by simply not resolving
a draft or deprecated definition at all -- from the API's perspective, a
diagnostic that isn't published doesn't exist yet (or no longer exists),
which is what "unknown diagnostic" / "unknown diagnostic version" (404)
already means. The engine itself has no opinion on `status` (Architecture
v1.2 section 3: the engine is a pure function of definition + responses)
-- this is a deliberate application-layer decision, not an engine change.
"""

from __future__ import annotations

import json
from pathlib import Path


class DiagnosticRepository:
    def __init__(self, definition_paths: list[Path]):
        self._by_id_version: dict[tuple[str, str], dict] = {}
        self._latest_published: dict[str, str] = {}

        for path in definition_paths:
            with open(path) as f:
                definition = json.load(f)
            diagnostic_id = definition["diagnostic_id"]
            version = definition["version"]
            self._by_id_version[(diagnostic_id, version)] = definition
            if definition["status"] == "published":
                current_latest = self._latest_published.get(diagnostic_id)
                if current_latest is None or _version_key(version) > _version_key(current_latest):
                    self._latest_published[diagnostic_id] = version

    def list_published(self) -> list[dict]:
        """All published definitions, one per diagnostic_id (its latest
        published version), for discovery (GET /api/v1/diagnostics)."""
        return [
            self._by_id_version[(diagnostic_id, version)]
            for diagnostic_id, version in self._latest_published.items()
        ]

    def get(self, diagnostic_id: str, version: str | None = None) -> dict | None:
        """
        The published definition for `diagnostic_id`, at `version` if
        given, else its latest published version. Returns None if
        `diagnostic_id` is unknown, or if it's known but not published
        at the requested version (or not published at all) -- callers
        distinguish those two cases with `is_known_id` below to choose
        between "unknown diagnostic" and "unknown diagnostic version".
        """
        if version is None:
            version = self._latest_published.get(diagnostic_id)
            if version is None:
                return None
            return self._by_id_version[(diagnostic_id, version)]

        definition = self._by_id_version.get((diagnostic_id, version))
        if definition is None or definition["status"] != "published":
            return None
        return definition

    def is_known_id(self, diagnostic_id: str) -> bool:
        return diagnostic_id in self._latest_published

    def known_published_versions(self, diagnostic_id: str) -> list[str]:
        return sorted(
            version
            for (did, version) in self._by_id_version
            if did == diagnostic_id and self._by_id_version[(did, version)]["status"] == "published"
        )


def _version_key(version: str) -> tuple[int, ...]:
    """Semver-ish major.minor.patch -> a tuple that sorts correctly."""
    return tuple(int(part) for part in version.split("."))
