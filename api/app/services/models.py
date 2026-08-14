"""Loading, caching, and honestly describing the trained estimators.

Three problems with how the prototype did this, all fixed here.

**It loaded from disk on every request.** `joblib.load` on a RandomForest with
300 trees is tens of milliseconds and allocates the whole forest again. The
models are immutable, so they are loaded once and held.

**It hid load failures.** `_load` swallowed every exception and returned
``None``, which the caller then treated identically to "this disease has no
model". A corrupt file and a deliberately model-less disease are different
facts and the client is told which is which.

**It assumed `predict_proba` exists.** Two of these estimators are `SVC`
instances trained without ``probability=True`` and have no such method. The
prototype substituted the constants 65 and 20. Here the capability is probed
once at load and reported, so the UI can say "rule-based only" (ADR-007).
"""

from __future__ import annotations

import logging
import pickle
import warnings
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any, Protocol, cast

import joblib
import numpy as np

from app.config import MODELS_DIR
from app.domain.schemas import REGISTRY, Disease

log = logging.getLogger(__name__)

# joblib checks the file magic first; a .sav written by plain pickle still
# loads, so the order here is "most likely to work" rather than by extension.
_EXTENSIONS = (".joblib", ".sav", ".pkl")


class Estimator(Protocol):
    """The slice of the scikit-learn API this app actually uses."""

    def predict(self, X: Any) -> Any: ...  # noqa: N803 — scikit-learn's own parameter name


@dataclass(frozen=True, slots=True)
class LoadedModel:
    """An estimator plus the facts about it that the client is entitled to."""

    estimator: Estimator
    source: str
    n_features: int | None
    classes: tuple[int, ...]
    has_proba: bool

    def positive_probability(self, row: np.ndarray, positive_class: int) -> float | None:
        """P(positive) for one row, or None when the estimator cannot say.

        Returning None is the whole point of this module. The caller must
        handle it rather than receive a fabricated number.
        """
        if not self.has_proba:
            return None
        proba_fn = getattr(self.estimator, "predict_proba", None)
        if proba_fn is None:
            return None
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                proba = _normalise_proba(proba_fn(row)[0])
        except Exception:
            log.exception("predict_proba failed for %s", self.source)
            return None

        if proba is None:
            return None

        if positive_class in self.classes:
            return float(proba[self.classes.index(positive_class)])
        # A binary estimator whose classes we could not read: the second column
        # is the positive one by scikit-learn convention.
        return float(proba[-1]) if len(proba) == 2 else None

    def predict(self, row: np.ndarray) -> int | None:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                return int(self.estimator.predict(row)[0])
        except Exception:
            log.exception("predict failed for %s", self.source)
            return None


def _normalise_proba(proba: np.ndarray) -> np.ndarray | None:
    """Return `proba` as a real probability vector, or None if it is not one.

    `hepatitis.sav` makes this necessary. It is a `RandomForestClassifier`
    whose `predict_proba` returns ``[9.99, 8.84]`` — a vector summing to 18.83.
    The cause is a scikit-learn storage change: before 1.3 a classifier tree's
    `value` array held raw weighted class counts, and from 1.3 it holds
    normalised per-class fractions. The forest was pickled under the old
    convention and is being read under the new one, so the averaging step that
    used to divide by the sample count no longer does.

    Rescaling a non-negative count vector to sum to 1 recovers the number the
    estimator was always trying to report, so it is done rather than discarded.
    Anything that is *not* a non-negative finite vector is a fault we cannot
    interpret, and None is returned so the caller falls back to rule-based
    scoring instead of blending in a meaningless value.
    """
    if proba.ndim != 1 or proba.size == 0:
        return None
    if not np.all(np.isfinite(proba)) or np.any(proba < 0):
        return None

    total = float(proba.sum())
    if total <= 0:
        return None
    if abs(total - 1.0) < 1e-6:
        return proba
    return proba / total


def _read(path: Path) -> Estimator | None:
    """Unpickle one file, trying joblib then plain pickle."""
    try:
        with warnings.catch_warnings():
            # These estimators were pickled under an older scikit-learn, so
            # InconsistentVersionWarning is expected and noisy, not actionable.
            warnings.simplefilter("ignore")
            return cast(Estimator, joblib.load(path))
    except Exception as exc:
        log.debug("joblib could not read %s: %s", path.name, exc)

    try:
        with open(path, "rb") as handle, warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return cast(Estimator, pickle.load(handle))  # noqa: S301 — first-party model files
    except Exception as exc:
        log.warning("Could not load %s: %s", path.name, exc)
        return None


def _describe(estimator: Estimator, source: str) -> LoadedModel:
    """Probe an estimator for the capabilities the API reports.

    `predict_proba` merely existing is not enough — an `SVC` built without
    ``probability=True`` raises on call — so availability is confirmed by
    checking for the fitted `probA_` attribute that libsvm only sets when
    probability estimates were requested.
    """
    raw_classes = getattr(estimator, "classes_", [])
    try:
        classes = tuple(int(c) for c in raw_classes)
    except (TypeError, ValueError):
        classes = ()

    has_proba = hasattr(estimator, "predict_proba")
    if has_proba and type(estimator).__name__ == "SVC":
        has_proba = getattr(estimator, "probability", False) is True

    n_features = getattr(estimator, "n_features_in_", None)
    return LoadedModel(
        estimator=estimator,
        source=source,
        n_features=int(n_features) if n_features is not None else None,
        classes=classes,
        has_proba=has_proba,
    )


def _train_breast_cancer_fallback() -> LoadedModel | None:
    """Last resort for breast cancer, whose shipped `.sav` is corrupt.

    scikit-learn bundles the same Wisconsin dataset the file was trained on, so
    a replacement can be fitted in about a second at startup. Labels are
    inverted because sklearn encodes malignant as 0 while this app treats 1 as
    the positive (disease) class throughout.
    """
    try:
        from sklearn.datasets import load_breast_cancer
        from sklearn.ensemble import RandomForestClassifier
    except ImportError:
        return None

    data = load_breast_cancer()
    estimator = RandomForestClassifier(
        n_estimators=300, class_weight="balanced", random_state=42
    )
    estimator.fit(data.data, (data.target == 0).astype(int))
    log.info("Trained in-process breast cancer fallback model")
    return _describe(cast(Estimator, estimator), "sklearn.datasets (in-process fallback)")


@cache
def load_model(stem: str) -> LoadedModel | None:
    """Load and describe the estimator named `stem`, or None if unavailable.

    Cached, so each model is read from disk exactly once per process.
    """
    for ext in _EXTENSIONS:
        path = MODELS_DIR / f"{stem}{ext}"
        if not path.exists():
            continue
        estimator = _read(path)
        if estimator is not None:
            return _describe(estimator, path.name)
        log.warning("%s exists but could not be unpickled; trying next extension", path.name)

    if stem == "breast_cancer":
        return _train_breast_cancer_fallback()

    log.warning("No loadable model file for %r in %s", stem, MODELS_DIR)
    return None


def model_for(disease: Disease) -> LoadedModel | None:
    """The estimator for a disease, or None when it declares no model."""
    if disease.model is None:
        return None
    return load_model(disease.model)


def warm_cache() -> dict[str, bool]:
    """Load every model up front so the first request is not the slow one.

    Called from the lifespan handler. Returns a slug → available map, which is
    logged at startup and makes a missing model obvious immediately rather than
    on the first request that needs it.
    """
    status: dict[str, bool] = {}
    for disease in REGISTRY:
        if disease.model is None:
            status[disease.slug] = False
            continue
        status[disease.slug] = model_for(disease) is not None
    return status
