"""
Application layer for EverCompass: sits between the FastAPI API layer and
the pure Assessment Engine (Architecture v1.2's own boundary -- see
src/engine/errors.py's own docstring, which already anticipates an "API
layer" above the engine doing exactly this kind of translation).

Responsibilities living here, and nowhere else:
  - loading/selecting the requested diagnostic definition and version
    (repository.py)
  - orchestrating one assessment: resolve definition -> validate ->
    evaluate -> return the Structured Result (assessment.py)
  - building the public-safe view of a diagnostic definition, i.e. what
    a frontend needs to render questions and collect responses, with no
    proprietary scoring/weighting/rule internals (public_view.py)

This layer contains no scoring/aggregation/priority logic of its own --
it calls straight through to engine.evaluate() and otherwise only moves
data around. It has no HTTP awareness (no FastAPI/Starlette import
anywhere in this package).
"""
