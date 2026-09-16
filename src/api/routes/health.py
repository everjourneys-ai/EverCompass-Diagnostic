"""GET /health -- liveness only. No Supabase or other dependency exists
in Phase 1 to report readiness for (see this task's health/dependency
design note): this deliberately doesn't pretend to check anything."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}
