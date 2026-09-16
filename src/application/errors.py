"""
Application-layer errors -- distinct from engine.errors.

These cover a different failure category than engine.errors.
DiagnosticValidationError (and its subclasses, e.g.
UnknownDiagnosticVersionError) means "the engine was handed a definition
and a response set that don't agree." The errors here mean "the caller
asked for a diagnostic id/version this application doesn't have at
all" -- a routing/lookup failure that happens before the engine is ever
invoked. Kept separate so the API layer can map them to 404 (not found)
independently of how it maps engine validation errors (400).
"""

from __future__ import annotations


class ApplicationError(Exception):
    """Base class for all application-layer errors."""


class DiagnosticNotFoundError(ApplicationError):
    """No diagnostic with this diagnostic_id is known to this application."""

    def __init__(self, diagnostic_id: str):
        super().__init__(f"No diagnostic {diagnostic_id!r} is available.")
        self.diagnostic_id = diagnostic_id


class DiagnosticVersionNotFoundError(ApplicationError):
    """diagnostic_id exists, but not at the requested version."""

    def __init__(self, diagnostic_id: str, version: str, available_versions: list[str]):
        super().__init__(
            f"Diagnostic {diagnostic_id!r} has no version {version!r} "
            f"(available: {sorted(available_versions)})."
        )
        self.diagnostic_id = diagnostic_id
        self.version = version
        self.available_versions = available_versions
