"""Lab-report ingestion: PDF or text in, normalised analyte values out.

This router deliberately knows nothing about the estimators. It turns a
document into numbers; scoring those numbers stays entirely in
:mod:`app.routers.predict`, so a change here can never alter a prediction.

Two extraction strategies, in order of preference:

**Pattern matching** (always available). Aliases per analyte, matched against
the flattened text. Deterministic and auditable — the same report always
yields the same numbers, which matters when the output feeds a risk score.

**LLM assist** (only when ``GROQ_API_KEY`` is set). Real reports are messy:
values in tables, split across columns, named a dozen ways. A language model
reads that far better than a regex. It runs *in addition* to the patterns,
never instead — every value it returns is bounds-checked, and the pattern
result wins any disagreement, because a hallucinated bilirubin is worse than
a missing one.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.config import get_settings

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["extraction"])

MAX_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class Analyte:
    """One measurable quantity and the names reports give it."""

    key: str
    label: str
    unit: str
    aliases: tuple[str, ...]
    lo: float
    hi: float


# Bounds are "physically possible", not "normal" — they exist to reject a
# misparse (a date read as a glucose), not to judge the patient.
ANALYTES: tuple[Analyte, ...] = (
    Analyte("glucose", "Glucose", "mg/dL",
            ("fasting blood glucose", "fasting blood sugar", "blood glucose fasting",
             "fasting glucose", "blood sugar", "glucose", "fbs"), 20, 900),
    Analyte("bmi", "BMI", "", ("body mass index", "bmi"), 8, 90),
    Analyte("systolic", "Systolic BP", "mmHg",
            ("systolic blood pressure", "systolic bp", "blood pressure", "systolic"), 50, 260),
    Analyte("insulin", "Insulin", "uU/mL", ("serum insulin", "insulin"), 0, 1000),
    Analyte("age", "Age", "yrs", ("age",), 1, 120),
    Analyte("chol", "Total cholesterol", "mg/dL",
            ("total cholesterol", "serum cholesterol", "cholesterol"), 50, 700),
    Analyte("tbil", "Total bilirubin", "mg/dL",
            ("total bilirubin", "bilirubin total", "serum bilirubin", "bilirubin"), 0, 90),
    Analyte("dbil", "Direct bilirubin", "mg/dL",
            ("direct bilirubin", "conjugated bilirubin", "bilirubin direct"), 0, 50),
    Analyte("alp", "Alkaline phosphatase", "U/L",
            ("alkaline phosphatase", "alkaline phosphotase", "alk phos", "alp"), 10, 3000),
    Analyte("alt", "ALT (SGPT)", "U/L",
            ("alanine aminotransferase", "sgpt (alt)", "alt (sgpt)", "sgpt", "alt"), 1, 3000),
    Analyte("ast", "AST (SGOT)", "U/L",
            ("aspartate aminotransferase", "sgot (ast)", "ast (sgot)", "sgot", "ast"), 1, 3000),
    Analyte("tprot", "Total protein", "g/dL",
            ("total protein", "total protiens", "total proteins"), 1, 12),
    Analyte("alb", "Albumin", "g/dL", ("serum albumin", "albumin"), 0.5, 7),
    Analyte("agr", "A/G ratio", "",
            ("albumin globulin ratio", "a/g ratio", "ag ratio"), 0.1, 5),
    Analyte("creat", "Serum creatinine", "mg/dL", ("serum creatinine", "creatinine"), 0.1, 25),
    Analyte("urea", "Blood urea", "mg/dL",
            ("blood urea nitrogen", "blood urea", "urea", "bun"), 1, 400),
    Analyte("hemo", "Haemoglobin", "g/dL", ("haemoglobin", "hemoglobin", "hgb", "hb"), 2, 25),
    Analyte("sod", "Sodium", "mEq/L", ("sodium", "na+"), 90, 200),
    Analyte("pot", "Potassium", "mEq/L", ("potassium", "k+"), 1, 12),
    Analyte("pcv", "PCV / haematocrit", "%",
            ("packed cell volume", "haematocrit", "hematocrit", "pcv"), 5, 70),
    Analyte("wbc", "WBC count", "/uL",
            ("white blood cell count", "total leucocyte count", "wbc count", "wbc", "tlc"), 500, 60000),
    Analyte("rbc", "RBC count", "M/uL", ("red blood cell count", "rbc count", "rbc"), 1, 10),
    Analyte("sg", "Urine specific gravity", "", ("specific gravity", "sp gravity"), 1.0, 1.06),
)

BY_KEY = {a.key: a for a in ANALYTES}


class ExtractIn(BaseModel):
    text: str


class Value(BaseModel):
    key: str
    label: str
    unit: str
    value: float
    source: str          # "pattern" | "assisted"
    evidence: str | None = None


class ExtractOut(BaseModel):
    source: str          # "pdf" | "text"
    pages: int
    characters: int
    method: str
    values: list[Value]
    unmatched: list[str]


# ---------------------------------------------------------------- PDF


def _pdf_to_text(blob: bytes) -> tuple[str, int]:
    """Text and page count from a PDF, or 422 if it is not readable."""
    text = ""
    pages = 0

    # 1. Try PyMuPDF (fitz)
    try:
        import fitz
        with fitz.open(stream=blob, filetype="pdf") as doc:
            if doc.needs_pass:
                raise HTTPException(422, "That PDF is password-protected.")
            pages = doc.page_count
            text = "\n".join(page.get_text() for page in doc)
    except (ImportError, Exception):
        # 2. Try pypdf
        try:
            import io
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(blob))
            if reader.is_encrypted:
                raise HTTPException(422, "That PDF is password-protected.")
            pages = len(reader.pages)
            text = "\n".join(p.extract_text() or "" for p in reader.pages)
        except (ImportError, Exception):
            # 3. Try PyPDF2
            try:
                import io
                import PyPDF2
                reader = PyPDF2.PdfReader(io.BytesIO(blob))
                pages = len(reader.pages)
                text = "\n".join(p.extract_text() or "" for p in reader.pages)
            except Exception as exc:
                log.warning("PDF parse failed: %s", exc)
                raise HTTPException(422, "That file could not be read as a PDF. Please paste the text instead.") from exc

    if not text.strip():
        raise HTTPException(
            422,
            "No text layer found — this looks like a scanned image rather than a digital PDF. Paste the values in as text instead.",
        )
    return text, pages


# ---------------------------------------------------------------- patterns


def _pattern_extract(text: str) -> dict[str, Value]:
    flat = re.sub(r"[ \t]+", " ", text.lower())
    out: dict[str, Value] = {}

    for a in ANALYTES:
        # longest alias first, so "total bilirubin" beats bare "bilirubin"
        for alias in sorted(a.aliases, key=len, reverse=True):
            # The alias must not sit inside a longer word. Without this guard
            # "ast" matches inside "F-ast-ing Blood Glucose" and steals its
            # number; "alt", "hb", "bun" and "alp" all fail the same way.
            # Letter lookarounds rather than \b, because several aliases end
            # in a bracket ("sgpt (alt)") where \b would not apply.
            pattern = (
                r"(?<![a-z])" + re.escape(alias) + r"(?![a-z])"
                r"[^0-9\n\r]{0,40}?([0-9]+(?:\.[0-9]+)?)"
            )
            m = re.search(pattern, flat)
            if not m:
                continue
            try:
                v = float(m.group(1))
            except ValueError:
                continue
            if not (a.lo <= v <= a.hi):
                continue          # out of physical range: a misparse, not a value
            line = flat[max(0, m.start()) : m.end() + 12].strip()
            out[a.key] = Value(key=a.key, label=a.label, unit=a.unit, value=v,
                               source="pattern", evidence=line[:90])
            break

    # Sex is categorical, so it needs its own pass. Several models encode it
    # as 1=male / 0=female, which is what the registry expects.
    if re.search(r"(?<![a-z])female(?![a-z])", flat):
        out["sex"] = Value(key="sex", label="Sex", unit="female", value=0.0, source="pattern")
    elif re.search(r"(?<![a-z])male(?![a-z])", flat):
        out["sex"] = Value(key="sex", label="Sex", unit="male", value=1.0, source="pattern")
    return out


# ---------------------------------------------------------------- LLM assist

_SYSTEM = (
    "You read clinical laboratory reports and return structured values. "
    "Return ONLY a JSON object of the form {\"values\": {\"<key>\": <number>}}. "
    "Use only these keys: " + ", ".join(a.key for a in ANALYTES) + ". "
    "Omit any key you cannot find. Never guess, never infer, never compute. "
    "Report numbers exactly as printed, without units."
)


async def _llm_extract(text: str) -> dict[str, float]:
    """Ask the model for anything the patterns missed. Best effort only."""
    settings = get_settings()
    if not settings.has_groq:
        return {}

    body = {
        "model": settings.groq_model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": text[:14000]},
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                json=body,
            )
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content).get("values", {})
    except Exception as exc:
        # An assist that fails must never fail the request.
        log.warning("assisted extraction unavailable: %s", exc)
        return {}

    clean: dict[str, float] = {}
    for k, v in parsed.items():
        a = BY_KEY.get(k)
        if a is None:
            continue
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if a.lo <= f <= a.hi:      # same bounds check as the patterns
            clean[k] = f
    return clean


# ---------------------------------------------------------------- route


async def _build(text: str, source: str, pages: int) -> ExtractOut:
    found = _pattern_extract(text)

    assisted = await _llm_extract(text)
    added = 0
    for key, v in assisted.items():
        if key in found:
            continue               # deterministic result wins any disagreement
        a = BY_KEY[key]
        found[key] = Value(key=key, label=a.label, unit=a.unit, value=v,
                           source="assisted", evidence=None)
        added += 1

    method = "pattern matching"
    if added:
        method = f"pattern matching (+{added} recovered by assisted reading)"
    elif assisted:
        method = "pattern matching (assisted reading agreed, added nothing)"

    # `sex` is not in ANALYTES (it is categorical, not measured), so it has to
    # be appended explicitly or the ordering step would silently drop it.
    ordered = [found[a.key] for a in ANALYTES if a.key in found]
    if "sex" in found:
        ordered.append(found["sex"])
    unmatched = [a.label for a in ANALYTES if a.key not in found]
    return ExtractOut(source=source, pages=pages, characters=len(text),
                      method=method, values=ordered, unmatched=unmatched)


@router.post("/extract", response_model=ExtractOut, summary="Read analytes from a report")
async def extract_file(file: UploadFile = File(...)) -> ExtractOut:
    blob = await file.read()
    if len(blob) > MAX_BYTES:
        raise HTTPException(413, "That file is larger than 8 MB.")
    if not blob:
        raise HTTPException(422, "That file is empty.")

    name = (file.filename or "").lower()
    if name.endswith(".pdf") or blob[:5] == b"%PDF-":
        text, pages = _pdf_to_text(blob)
        return await _build(text, "pdf", pages)

    try:
        text = blob.decode("utf-8", errors="replace")
    except Exception as exc:
        raise HTTPException(422, "That file could not be read as text.") from exc
    return await _build(text, "text", 1)


@router.post("/extract/text", response_model=ExtractOut, summary="Read analytes from pasted text")
async def extract_text(payload: ExtractIn) -> ExtractOut:
    if not payload.text.strip():
        raise HTTPException(422, "No text supplied.")
    return await _build(payload.text, "text", 1)
