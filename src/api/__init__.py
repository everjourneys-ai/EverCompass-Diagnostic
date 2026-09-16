"""
FastAPI API layer for EverCompass. Responsible for HTTP only -- request
parsing, response serialization, status codes, API-level (shape) request
validation, CORS, and routing. Contains no assessment/scoring
methodology; every route delegates to src/application, which in turn
delegates to src/engine. See src/application/__init__.py and
src/engine/errors.py for the layering this package sits on top of.
"""
