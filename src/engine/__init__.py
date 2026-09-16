"""
EverCompass Assessment Engine.

Pure Python, standard library only. Single public entrypoint:

    from engine import evaluate, ENGINE_VERSION
    result = evaluate(definition, responses, assessment_id="asm_001",
                       diagnostic_version="1.0.0")

See ENGINE_STATUS.md for what is fully implemented versus stubbed
pending undefined methodology decisions (DECISIONS.md).
"""

from .engine import ENGINE_VERSION, evaluate
from .errors import (
    ContradictoryApplicabilityError,
    DiagnosticEngineError,
    DiagnosticValidationError,
    DuplicateResponseError,
    InvalidValueError,
    MissingResponseError,
    UndefinedDiagnosticRuleError,
    UnknownCriterionError,
    UnknownDiagnosticVersionError,
    UnsupportedRuleTypeError,
)
from .types import (
    AggregateResult,
    AssessmentResult,
    CriterionResult,
    Finding,
    Priority,
    Response,
    SystemSummary,
)

__all__ = [
    "evaluate",
    "ENGINE_VERSION",
    "Response",
    "CriterionResult",
    "Finding",
    "AggregateResult",
    "Priority",
    "SystemSummary",
    "AssessmentResult",
    "DiagnosticEngineError",
    "DiagnosticValidationError",
    "UnknownDiagnosticVersionError",
    "UnknownCriterionError",
    "MissingResponseError",
    "DuplicateResponseError",
    "InvalidValueError",
    "ContradictoryApplicabilityError",
    "UnsupportedRuleTypeError",
    "UndefinedDiagnosticRuleError",
]
