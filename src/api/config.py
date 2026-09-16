"""
API configuration, read from environment variables. No secrets, no
persistence config -- Phase 1 has neither.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

#: Local dev origins allowed out of the box (a plain Vite/Next dev
#: server and a local Framer preview both commonly run on one of
#: these). No production domain is hardcoded here because none is
#: defined anywhere else in this repository -- set EVERCOMPASS_CORS_ORIGINS
#: to add the real Framer/production origin(s) when they exist.
_DEFAULT_DEV_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


@dataclass(frozen=True)
class Settings:
    cors_allowed_origins: list[str] = field(default_factory=lambda: list(_DEFAULT_DEV_ORIGINS))


def load_settings() -> Settings:
    raw_origins = os.environ.get("EVERCOMPASS_CORS_ORIGINS")
    if raw_origins is None:
        return Settings()
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return Settings(cors_allowed_origins=origins)
