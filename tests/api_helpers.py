"""
Shared helpers for the API test modules (tests/test_api_*.py) -- kept
separate from tests/helpers.py deliberately, so the existing 73 engine
tests never need fastapi/httpx installed to run; only the API tests do
(see requirements-dev.txt). No mocking of the engine anywhere here or in
the API tests that use it -- TestClient runs the real app, real
application layer, and real engine end to end.
"""

from __future__ import annotations

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_REPO_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from fastapi.testclient import TestClient  # noqa: E402

from api.main import create_app  # noqa: E402


def make_client() -> TestClient:
    return TestClient(create_app())


def valid_response_payload(definition: dict, value: int = 3) -> list[dict]:
    """One response per criterion, all applicable, all the same value --
    the JSON-request equivalent of tests/helpers.py::all_applicable_responses."""
    return [
        {
            "criterion_id": c["id"],
            "value": value,
            "evidence": f"api test evidence for {c['id']}",
            "applicability": "applicable",
        }
        for c in definition["criteria"]
    ]
