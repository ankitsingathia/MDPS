"""Clinical risk scoring.

The prototype's `clinical_risk_score` was a 110-line if/elif chain that mixed
weights, thresholds, and prose into one function per disease. The weights are
the interesting part, so they are lifted here into data — a tuple of
:class:`Rule` per disease — and one interpreter walks them.

That buys three things the chain could not give: the per-factor contributions
can be returned to the client (which is what the result chart draws), a rule
can be unit-tested without invoking a disease, and adding a condition is a data
edit rather than a new branch.

Weights are unchanged from the prototype. They are heuristics drawn from
published reference ranges, not fitted parameters, and are documented as such.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Band(StrEnum):
    """Risk bands. These map 1:1 onto the `risk-*` colour tokens in the client."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


def band_for(score: int) -> Band:
    if score < 25:
        return Band.LOW
    if score < 50:
        return Band.MODERATE
    if score < 75:
        return Band.HIGH
    return Band.CRITICAL


@dataclass(frozen=True, slots=True)
class Rule:
    """One weighted clinical factor.

    `normal` is where the factor starts contributing and `danger` is where it
    saturates at full weight. When `danger < normal` the factor is inverted —
    haemoglobin and HNR are risky when *low* — so direction is inferred from
    the two bounds rather than carried in a separate `inverse` flag that could
    disagree with them.
    """

    field: str
    label: str
    weight: float
    normal: float
    danger: float
    # Emitted when the factor contributes more than `flag_at` percent of its
    # own range, so the reason list reflects what actually drove the score.
    reason: str | None = None
    flag_at: int = 50

    @property
    def inverted(self) -> bool:
        return self.danger < self.normal

    def contribution(self, value: float | None) -> tuple[float, bool]:
        """Return (weighted points, whether this factor should be flagged)."""
        if value is None:
            return 0.0, False
        span = abs(self.normal - self.danger)
        if span < 1e-9:
            return 0.0, False

        ratio = (self.normal - value) / span if self.inverted else (value - self.normal) / span
        pct = max(0.0, min(1.0, ratio)) * 100

        return pct * self.weight, pct >= self.flag_at and self.reason is not None


@dataclass(frozen=True, slots=True)
class Flag:
    """A categorical factor: fixed points when the field equals `when`."""

    field: str
    label: str
    points: float
    when: int
    reason: str


# Each disease's factors. Weights within a disease are the prototype's, so the
# scores this produces match the Streamlit app's for the same inputs.
RULES: dict[str, tuple[Rule | Flag, ...]] = {
    "diabetes": (
        Rule("Glucose", "Glucose", 0.45, 125, 220, "Glucose is in a diabetic range."),
        Rule("BMI", "BMI", 0.25, 30, 45, "BMI is in the obesity range."),
        Rule("Age", "Age", 0.15, 45, 75),
        Rule("BloodPressure", "Blood pressure", 0.10, 130, 180, "Blood pressure is elevated."),
        Rule("Insulin", "Insulin", 0.05, 180, 500),
    ),
    "heart-disease": (
        Rule("chol", "Cholesterol", 0.22, 200, 320, "Cholesterol is high."),
        Rule("trestbps", "Resting BP", 0.18, 130, 190, "Resting blood pressure is high."),
        Rule("age", "Age", 0.15, 50, 80),
        Rule("thalach", "Max heart rate", 0.15, 140, 90, "Maximum heart rate is low."),
        Rule("oldpeak", "ST depression", 0.12, 1.0, 4.0, "ST depression is clinically notable."),
        Flag("cp", "Chest pain type", 25, 2, "Chest pain type suggests reduced perfusion."),
        Flag("exang", "Exercise angina", 20, 1, "Exercise-induced angina is present."),
        Flag("ca", "Major vessels", 15, 1, "One or more major vessels are affected."),
    ),
    "parkinsons": (
        Rule("MDVP:Jitter(%)", "Jitter", 0.22, 0.006, 0.02, "Voice jitter is elevated."),
        Rule("MDVP:Shimmer", "Shimmer", 0.18, 0.03, 0.10, "Voice shimmer is elevated."),
        Rule("NHR", "Noise-to-harmonics", 0.18, 0.03, 0.25, "Noise-to-harmonics ratio is high."),
        Rule("HNR", "Harmonics-to-noise", 0.18, 20, 10, "Harmonics-to-noise ratio is low."),
        Rule("PPE", "Pitch period entropy", 0.14, 0.2, 0.6, "Pitch period entropy is elevated."),
        Rule("D2", "Correlation dimension", 0.10, 2.5, 4.5),
    ),
    "liver-disease": (
        Rule("Total_Bilirubin", "Total bilirubin", 0.25, 1.2, 5.0, "Bilirubin is elevated."),
        Rule("Direct_Bilirubin", "Direct bilirubin", 0.15, 0.3, 2.0),
        Rule("Alkaline_Phosphotase", "Alkaline phosphatase", 0.15, 150, 500,
             "Alkaline phosphatase is elevated."),
        Rule("Alamine_Aminotransferase", "ALT", 0.15, 45, 300, "ALT is elevated."),
        Rule("Aspartate_Aminotransferase", "AST", 0.15, 40, 300, "AST is elevated."),
        Rule("Albumin", "Albumin", 0.15, 3.5, 2.2, "Albumin is low."),
    ),
    "hepatitis": (
        Rule("bilirubin", "Bilirubin", 0.25, 1.2, 5.0, "Bilirubin is elevated."),
        Rule("albumin", "Albumin", 0.20, 3.5, 2.2, "Albumin is low."),
        Flag("fatigue", "Fatigue", 15, 2, "Fatigue is reported."),
        Flag("malaise", "Malaise", 10, 2, "Malaise is reported."),
        Flag("anorexia", "Anorexia", 10, 2, "Anorexia is reported."),
        Flag("liver_big", "Enlarged liver", 15, 2, "The liver is enlarged."),
        Flag("liver_firm", "Firm liver", 15, 2, "The liver is firm."),
    ),
    "lung-cancer": (
        Rule("AGE", "Age", 0.15, 55, 85),
        Flag("SMOKING", "Smoking", 18, 2, "Smoking history is present."),
        Flag("YELLOW_FINGERS", "Yellow fingers", 8, 2, "Yellow fingers are reported."),
        Flag("CHRONIC_DISEASE", "Chronic disease", 8, 2, "Chronic disease history is present."),
        Flag("FATIGUE", "Fatigue", 8, 2, "Fatigue is reported."),
        Flag("WHEEZING", "Wheezing", 8, 2, "Wheezing is reported."),
        Flag("COUGHING", "Coughing", 10, 2, "Coughing is reported."),
        Flag("SHORTNESS_OF_BREATH", "Shortness of breath", 12, 2,
             "Shortness of breath is reported."),
        Flag("SWALLOWING_DIFFICULTY", "Swallowing difficulty", 8, 2,
             "Swallowing difficulty is reported."),
        Flag("CHEST_PAIN", "Chest pain", 12, 2, "Chest pain is reported."),
    ),
    "kidney-disease": (
        Rule("sc", "Serum creatinine", 0.20, 1.3, 5.0, "Serum creatinine is elevated."),
        Rule("hemo", "Haemoglobin", 0.14, 12, 7, "Haemoglobin is low."),
        Rule("bp", "Blood pressure", 0.12, 130, 190, "Blood pressure is high."),
        Rule("al", "Urine albumin", 0.12, 0, 4, "Urine albumin is elevated."),
        Rule("bu", "Blood urea", 0.12, 45, 150, "Blood urea is elevated."),
        Rule("bgr", "Blood glucose", 0.10, 140, 300),
        Flag("htn", "Hypertension", 12, 1, "Hypertension is present."),
        Flag("dm", "Diabetes mellitus", 10, 1, "Diabetes mellitus is present."),
        Flag("pe", "Pedal oedema", 8, 1, "Pedal oedema is present."),
    ),
    "breast-cancer": (
        Rule("worst_concave_points", "Worst concave points", 0.25, 0.15, 0.28,
             "Worst concave points are elevated."),
        Rule("mean_concave_points", "Mean concave points", 0.18, 0.08, 0.18,
             "Mean concave points are elevated."),
        Rule("worst_radius", "Worst radius", 0.16, 18, 32, "Worst radius is elevated."),
        Rule("worst_perimeter", "Worst perimeter", 0.16, 115, 220),
        Rule("mean_concavity", "Mean concavity", 0.13, 0.12, 0.35),
        Rule("worst_texture", "Worst texture", 0.12, 30, 45),
    ),
    "jaundice": (
        Rule("Total_Bilirubin", "Total bilirubin", 0.35, 1.2, 5.0,
             "Total bilirubin is elevated."),
        Rule("Direct_Bilirubin", "Direct bilirubin", 0.20, 0.3, 2.0,
             "Direct bilirubin is elevated."),
        Rule("Alkaline_Phosphotase", "Alkaline phosphatase", 0.12, 150, 500),
        Rule("Alamine_Aminotransferase", "ALT", 0.12, 45, 300),
        Rule("Aspartate_Aminotransferase", "AST", 0.11, 40, 300),
        Flag("dark_urine", "Dark urine", 15, 1, "Dark urine is reported."),
        Flag("yellow_eyes", "Yellow eyes or skin", 20, 1, "Yellow eyes or skin are reported."),
    ),
}


@dataclass(frozen=True, slots=True)
class Factor:
    """A single factor's contribution, for the breakdown chart."""

    label: str
    points: float
    max_points: float


@dataclass(frozen=True, slots=True)
class RuleScore:
    score: int
    reasons: tuple[str, ...]
    factors: tuple[Factor, ...]


def clinical_score(slug: str, values: dict[str, float]) -> RuleScore:
    """Score `values` against the published thresholds for `slug`.

    Returns the clamped 0-100 score, the reasons that fired, and every factor's
    contribution — including the ones that scored zero, because a chart that
    omits them hides the fact that they were checked and found normal.
    """
    rules = RULES.get(slug, ())
    total = 0.0
    reasons: list[str] = []
    factors: list[Factor] = []

    for rule in rules:
        if isinstance(rule, Flag):
            hit = values.get(rule.field) == rule.when
            points = rule.points if hit else 0.0
            if hit:
                reasons.append(rule.reason)
            factors.append(Factor(rule.label, points, rule.points))
        else:
            points, flagged = rule.contribution(values.get(rule.field))
            if flagged and rule.reason:
                reasons.append(rule.reason)
            factors.append(Factor(rule.label, round(points, 1), round(100 * rule.weight, 1)))
        total += points

    score = int(min(100, max(0, total)))
    if not reasons:
        reasons.append("No clinical threshold was crossed by these values.")

    # Largest contributor first — the chart reads top-down as "what drove this".
    factors.sort(key=lambda f: f.points, reverse=True)
    return RuleScore(score=score, reasons=tuple(reasons), factors=tuple(factors))


# How much the model's own opinion moves the final number. The prototype used
# 70/30 in favour of the clinical rules, and that split is kept: the rules are
# traceable to published reference ranges, while several of these estimators
# were trained on a few hundred rows.
RULE_WEIGHT = 0.70
MODEL_WEIGHT = 0.30


def blend(rule_score: int, model_probability: float | None) -> tuple[int, str]:
    """Combine the rule score with the model's probability, if it has one.

    Returns the blended score and a human-readable description of what went
    into it. When the model cannot produce a calibrated probability, the score
    is the rule score alone — **not** the prototype's substituted constants of
    65 and 20, which invented precision that did not exist (ADR-007).
    """
    if model_probability is None:
        return rule_score, "clinical thresholds"
    model_score = model_probability * 100
    blended = int((rule_score * RULE_WEIGHT) + (model_score * MODEL_WEIGHT))
    return blended, "clinical thresholds blended with model probability"
