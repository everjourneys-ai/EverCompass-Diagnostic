"""
Response-set validation (Design Spec v1.0 section 24).

"The system must reject:
 - missing required responses
 - unknown criterion IDs
 - invalid values
 - duplicate criterion responses
 - contradictory N/A state
 - unknown diagnostic versions
 For maturity 1-5, values outside 1-5 are invalid."

This module only checks; it never repairs or guesses at a response on
the caller's behalf.
"""

from __future__ import annotations

from .errors import (
    ContradictoryApplicabilityError,
    DuplicateResponseError,
    InvalidValueError,
    MissingResponseError,
    UnknownCriterionError,
    UnknownDiagnosticVersionError,
)
from .types import Response

VALID_APPLICABILITY = {"applicable", "not_applicable"}


def validate_responses(
    definition: dict,
    responses: list[Response],
    diagnostic_version: str,
) -> None:
    """
    Raise on the first violated category, in this order: version,
    duplicates, unknown criteria, missing criteria, per-response value
    and applicability shape. Raises nothing if the response set is
    fully valid against `definition`.
    """
    if diagnostic_version != definition["version"]:
        raise UnknownDiagnosticVersionError(
            f"Requested diagnostic_version {diagnostic_version!r} does not match "
            f"loaded definition version {definition['version']!r}",
            details=[diagnostic_version],
        )

    known_ids = {c["id"] for c in definition["criteria"]}

    seen: dict[str, int] = {}
    for r in responses:
        seen[r.criterion_id] = seen.get(r.criterion_id, 0) + 1
    duplicates = sorted(cid for cid, n in seen.items() if n > 1)
    if duplicates:
        raise DuplicateResponseError(
            f"{len(duplicates)} criterion_id(s) submitted more than once",
            details=duplicates,
        )

    submitted_ids = set(seen.keys())
    unknown = sorted(submitted_ids - known_ids)
    if unknown:
        raise UnknownCriterionError(
            f"{len(unknown)} response(s) reference a criterion_id not in "
            f"diagnostic {definition['diagnostic_id']!r} v{definition['version']}",
            details=unknown,
        )

    missing = sorted(known_ids - submitted_ids)
    if missing:
        raise MissingResponseError(
            f"{len(missing)} required criterion(s) have no response",
            details=missing,
        )

    invalid_value_ids: list[str] = []
    contradictory_ids: list[str] = []
    for r in responses:
        if r.applicability not in VALID_APPLICABILITY:
            invalid_value_ids.append(r.criterion_id)
            continue

        if r.applicability == "not_applicable":
            if r.value is not None:
                contradictory_ids.append(r.criterion_id)
            continue

        # applicable: value must be an int (not bool) in [1, 5]
        value_ok = (
            isinstance(r.value, int)
            and not isinstance(r.value, bool)
            and 1 <= r.value <= 5
        )
        if not value_ok:
            invalid_value_ids.append(r.criterion_id)

    if invalid_value_ids:
        raise InvalidValueError(
            f"{len(invalid_value_ids)} response(s) have an invalid value "
            f"(must be an integer 1-5 when applicable)",
            details=sorted(invalid_value_ids),
        )

    if contradictory_ids:
        raise ContradictoryApplicabilityError(
            f"{len(contradictory_ids)} response(s) marked not_applicable "
            f"but carry a non-null value",
            details=sorted(contradictory_ids),
        )
