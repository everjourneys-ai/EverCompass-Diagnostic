"""
Typed validation errors for the Assessment Engine.

Maps directly to Design Spec v1.0 section 24 ("The system must
reject...") and to Architecture v1.2 section 5 step 2, where an API
layer is expected to turn these into a 422 with field-level errors --
that translation happens above the engine, not inside it.
"""

from __future__ import annotations


class DiagnosticEngineError(Exception):
    """Base class for all engine errors."""


class DiagnosticValidationError(DiagnosticEngineError):
    """
    Base class for response-set validation failures (Design Spec section 24).

    `details` carries the offending criterion_ids (or other identifiers)
    so a caller can build a field-level error response without re-deriving
    what went wrong.
    """

    def __init__(self, message: str, details: list[str] | None = None):
        super().__init__(message)
        self.details = details or []


class UnknownDiagnosticVersionError(DiagnosticValidationError):
    """The requested diagnostic_version does not match the loaded definition's version."""


class UnknownCriterionError(DiagnosticValidationError):
    """A response references a criterion_id not present in the diagnostic definition."""


class MissingResponseError(DiagnosticValidationError):
    """A criterion in the diagnostic definition has no corresponding response."""


class DuplicateResponseError(DiagnosticValidationError):
    """The same criterion_id appears more than once in the submitted responses."""


class InvalidValueError(DiagnosticValidationError):
    """A response value is out of range, wrong type, or otherwise invalid."""


class ContradictoryApplicabilityError(DiagnosticValidationError):
    """applicability and value disagree (Design Spec section 7)."""


class UnsupportedRuleTypeError(DiagnosticEngineError):
    """
    A criterion's evaluation.rule.type is not implemented by this engine build.

    Design Spec section 8 defines five rule types; V1's 51 criteria all
    use `threshold`. This is raised rather than silently guessing at
    behavior for a rule type no current criterion exercises.
    """


class UndefinedDiagnosticRuleError(DiagnosticEngineError):
    """
    Raised when code would otherwise have to invent proprietary logic
    the diagnostic definition marks "TBD" (severity derivation, finding
    generation, aggregation method, priority scoring formula -- see
    DECISIONS.md). Functions that hit a real TBD in the definition
    return an empty/pending result instead of raising this in normal
    operation; it exists for callers that explicitly ask the engine to
    produce a value it cannot yet produce.
    """
