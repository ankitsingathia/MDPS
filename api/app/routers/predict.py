"""Screening endpoints.

Two routes carry the whole feature:

``GET /api/diseases``
    The registry, serialised. The client renders every form from this, so
    adding a disease or a field is a Python change with no TypeScript to match.

``POST /api/predict/{slug}``
    Score one submission. The body is validated against that disease's schema
    at runtime, because a static Pydantic model per disease would mean nine
    hand-written models restating what `domain.schemas` already knows.

The response deliberately includes how the score was reached — the rule score,
the model probability when one exists, and every factor's contribution. A
screening tool that shows a number without showing its work is not reviewable.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

import numpy as np
from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
from pydantic import Field as PydanticField

from app.domain import scoring
from app.domain.schemas import REGISTRY, Disease, get_disease
from app.services.models import LoadedModel, model_for

router = APIRouter(prefix="/api", tags=["screening"])


# ── Response models ────────────────────────────────────────────────────────
# Declared explicitly rather than returning bare dicts so they appear in the
# OpenAPI schema, which is what `npm run api:types` turns into the client's
# TypeScript types. The contract is generated from this file, never retyped.


class ChoiceOut(BaseModel):
    value: int
    label: str


class FieldOut(BaseModel):
    name: str
    label: str
    kind: Literal["int", "float", "bool", "choice"]
    default: float
    minimum: float
    maximum: float
    step: float
    unit: str | None = None
    help: str | None = None
    choices: list[ChoiceOut] = []
    group: str


class DiseaseOut(BaseModel):
    slug: str
    name: str
    blurb: str
    threshold: int
    field_count: int
    model_available: bool
    # False when the estimator cannot produce a calibrated probability, so the
    # client can label the result "rule-based" instead of implying precision.
    probability_available: bool
    caveat: str | None = None
    fields: list[FieldOut]


class FactorOut(BaseModel):
    label: str
    points: float
    max_points: float


class PredictionOut(BaseModel):
    disease: str
    slug: str
    risk_score: int = PydanticField(ge=0, le=100)
    band: Literal["low", "moderate", "high", "critical"]
    threshold: int
    flagged: bool
    reasons: list[str]
    factors: list[FactorOut]

    # How the number was reached, so the client can be honest about it.
    rule_score: int
    model_probability: float | None
    model_prediction: int | None
    model_available: bool
    method: str
    caveat: str | None = None


# ── Serialisation ──────────────────────────────────────────────────────────


def _serialise_disease(disease: Disease, model: LoadedModel | None) -> DiseaseOut:
    return DiseaseOut(
        slug=disease.slug,
        name=disease.name,
        blurb=disease.blurb,
        threshold=disease.threshold,
        field_count=disease.field_count,
        model_available=model is not None,
        probability_available=model is not None and model.has_proba,
        caveat=disease.caveat,
        fields=[
            FieldOut(
                name=f.name,
                label=f.label,
                kind=f.kind,
                default=f.default,
                minimum=f.minimum,
                maximum=f.maximum,
                step=f.step,
                unit=f.unit,
                help=f.help,
                choices=[ChoiceOut(value=c.value, label=c.label) for c in f.choices],
                group=f.group,
            )
            for f in disease.fields
        ],
    )


# ── Request validation ─────────────────────────────────────────────────────


def _coerce_payload(disease: Disease, payload: dict[str, Any]) -> dict[str, float]:
    """Validate `payload` against `disease`'s schema, in schema order.

    Order matters and is easy to get wrong: the estimator was trained on a
    positional feature array, so a dict that happens to serialise differently
    would silently feed glucose into the BMI column. Building the list by
    walking `disease.fields` makes the order structural rather than incidental.

    Errors are collected rather than raised on the first bad field, so a form
    with three mistakes reports three.
    """
    values: dict[str, float] = {}
    errors: list[dict[str, str]] = []

    for f in disease.fields:
        if f.name not in payload:
            errors.append({"field": f.name, "message": "This field is required."})
            continue

        raw = payload[f.name]
        if isinstance(raw, bool) or not isinstance(raw, int | float | str):
            errors.append({"field": f.name, "message": "Expected a number."})
            continue

        try:
            value = float(raw)
        except (TypeError, ValueError):
            errors.append({"field": f.name, "message": "Expected a number."})
            continue

        if value != value or value in (float("inf"), float("-inf")):
            errors.append({"field": f.name, "message": "Expected a finite number."})
            continue

        if not f.minimum <= value <= f.maximum:
            errors.append({
                "field": f.name,
                "message": f"Must be between {f.minimum:g} and {f.maximum:g}.",
            })
            continue

        if f.kind == "choice":
            allowed = {c.value for c in f.choices}
            if int(value) not in allowed:
                allowed_text = ", ".join(str(v) for v in sorted(allowed))
                errors.append({"field": f.name, "message": f"Must be one of: {allowed_text}."})
                continue

        values[f.name] = value

    if errors:
        raise HTTPException(status_code=422, detail=errors)

    unknown = sorted(set(payload) - {f.name for f in disease.fields})
    if unknown:
        raise HTTPException(
            status_code=422,
            detail=[{"field": name, "message": "Unknown field."} for name in unknown],
        )

    return values


# ── Routes ─────────────────────────────────────────────────────────────────

SlugPath = Annotated[str, Path(description="Disease slug, e.g. `diabetes`.")]


@router.get("/diseases", response_model=list[DiseaseOut], summary="List screenable conditions")
async def list_diseases() -> list[DiseaseOut]:
    """Every disease with its full form schema and model capabilities."""
    return [_serialise_disease(d, model_for(d)) for d in REGISTRY]


@router.get("/diseases/{slug}", response_model=DiseaseOut, summary="One condition's schema")
async def get_disease_route(slug: SlugPath) -> DiseaseOut:
    disease = get_disease(slug)
    if disease is None:
        raise HTTPException(status_code=404, detail=f"No such disease: {slug!r}")
    return _serialise_disease(disease, model_for(disease))


@router.post("/predict/{slug}", response_model=PredictionOut, summary="Score a submission")
async def predict(slug: SlugPath, payload: dict[str, Any]) -> PredictionOut:
    disease = get_disease(slug)
    if disease is None:
        raise HTTPException(status_code=404, detail=f"No such disease: {slug!r}")

    values = _coerce_payload(disease, payload)
    rule = scoring.clinical_score(disease.slug, values)

    model = model_for(disease)
    probability: float | None = None
    model_prediction: int | None = None

    if model is not None:
        # Positional, in schema order — see `_coerce_payload`.
        row = np.array([[values[f.name] for f in disease.fields]], dtype=float)
        model_prediction = model.predict(row)
        probability = model.positive_probability(row, disease.positive_class)

    score, method = scoring.blend(rule.score, probability)
    band = scoring.band_for(score)

    return PredictionOut(
        disease=disease.name,
        slug=disease.slug,
        risk_score=score,
        band=band.value,
        threshold=disease.threshold,
        flagged=score >= disease.threshold,
        reasons=list(rule.reasons),
        factors=[
            FactorOut(label=f.label, points=f.points, max_points=f.max_points)
            for f in rule.factors
        ],
        rule_score=rule.score,
        model_probability=probability,
        model_prediction=model_prediction,
        model_available=model is not None,
        method=method,
        caveat=disease.caveat,
    )
