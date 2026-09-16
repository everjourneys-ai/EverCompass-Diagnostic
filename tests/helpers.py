"""Shared test helpers -- load the real diagnostic definition and build
synthetic (but schema-valid) response sets against it."""

from __future__ import annotations

import json
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_REPO_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from engine.types import Response  # noqa: E402

DEFINITION_PATH = os.path.join(_REPO_ROOT, "src", "definitions", "diagnostic.json")


def load_definition() -> dict:
    with open(DEFINITION_PATH) as f:
        return json.load(f)


def all_applicable_responses(definition: dict, value: int = 3) -> list[Response]:
    """One response per criterion, all applicable, all the same value."""
    return [
        Response(
            criterion_id=c["id"],
            value=value,
            evidence=f"synthetic test evidence for {c['id']}",
            applicability="applicable",
        )
        for c in definition["criteria"]
    ]


def varied_responses(definition: dict) -> list[Response]:
    """One response per criterion, cycling values 1-5 so every
    classification band is exercised at least once."""
    responses = []
    for i, c in enumerate(definition["criteria"]):
        value = (i % 5) + 1
        responses.append(
            Response(
                criterion_id=c["id"],
                value=value,
                evidence=f"synthetic test evidence for {c['id']}",
                applicability="applicable",
            )
        )
    return responses
