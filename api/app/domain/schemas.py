"""The disease registry — the single source of truth for every screening form.

The prototype kept this as a dict of tuples in `mdps-streamlit/code/predictors.py`
and paid for it: the ``"Parkinson's"`` key is defined twice there (a 13-field
version at line 69 and a 22-field version at line 86), and Python silently keeps
the second. The app worked by luck. Tuples also carry no names, so
``field[3]`` meaning "default" was knowledge that lived only in a comment.

Here each field is a frozen dataclass, each disease appears exactly once
(enforced at import by :func:`_validate_registry`), and the whole registry is
serialisable to the client so the React form renders itself from this file
rather than duplicating 130 field definitions in TypeScript.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

FieldKind = Literal["int", "float", "bool", "choice"]


@dataclass(frozen=True, slots=True)
class Choice:
    """One option of a `choice` field."""

    value: int
    label: str


@dataclass(frozen=True, slots=True)
class Field:
    """One input on a screening form.

    `name` is the key the model was trained on and is passed through verbatim —
    including the awkward ones like ``MDVP:Jitter(%)``. `label` is what a human
    reads. The two are deliberately separate; the prototype showed raw feature
    names to users.
    """

    name: str
    label: str
    kind: FieldKind
    default: float
    minimum: float
    maximum: float
    unit: str | None = None
    help: str | None = None
    choices: tuple[Choice, ...] = ()
    group: str = "General"

    @property
    def step(self) -> float:
        """Sensible input step, derived from the range rather than hardcoded.

        A float spanning 0-0.05 (jitter) needs a far finer step than one
        spanning 0-2500 (mean area), and `step="any"` — what the prototype used
        — gives the browser no guidance for arrow keys or validation.
        """
        if self.kind in ("int", "bool", "choice"):
            return 1
        span = self.maximum - self.minimum
        if span <= 0.1:
            return 0.0001
        if span <= 2:
            return 0.01
        if span <= 100:
            return 0.1
        return 1


# Binary yes/no encodings differ per dataset and are a genuine source of bugs:
# the UCI hepatitis and lung-cancer sets use 1=No/2=Yes, while kidney and
# jaundice use 0=No/1=Yes. Naming them stops that from being retyped per field.
NO_YES_12 = (Choice(1, "No"), Choice(2, "Yes"))
NO_YES_01 = (Choice(0, "No"), Choice(1, "Yes"))
SEX_10 = (Choice(0, "Female"), Choice(1, "Male"))


def _flag12(name: str, label: str, group: str = "Symptoms") -> Field:
    """A 1=No / 2=Yes symptom flag."""
    return Field(name, label, "choice", 1, 1, 2, choices=NO_YES_12, group=group)


def _flag01(name: str, label: str, group: str = "History") -> Field:
    """A 0=No / 1=Yes clinical flag."""
    return Field(name, label, "choice", 0, 0, 1, choices=NO_YES_01, group=group)


@dataclass(frozen=True, slots=True)
class Disease:
    """A screenable condition and everything needed to render and score it."""

    slug: str
    name: str
    blurb: str
    model: str | None
    fields: tuple[Field, ...]
    threshold: int
    positive_class: int = 1
    # Set where the underlying dataset's positive rate or provenance means the
    # result deserves an extra caveat beyond the global disclaimer.
    caveat: str | None = None

    @property
    def field_count(self) -> int:
        return len(self.fields)


REGISTRY: tuple[Disease, ...] = (
    Disease(
        slug="diabetes",
        name="Diabetes",
        blurb="Pima Indians Diabetes dataset. Eight metabolic and demographic measures.",
        model="diabetes",
        threshold=40,
        caveat=(
            "This model is an SVC trained without probability=True, so it can report a "
            "class but not a calibrated probability. The score shown is rule-based."
        ),
        fields=(
            Field("Pregnancies", "Pregnancies", "int", 1, 0, 20, group="Demographics"),
            Field("Glucose", "Glucose", "float", 100, 0, 300, unit="mg/dL", group="Bloodwork",
                  help="Plasma glucose 2 hours into an oral tolerance test. 126+ is diabetic."),
            Field("BloodPressure", "Diastolic BP", "float", 72, 0, 200, unit="mm Hg",
                  group="Vitals"),
            Field("SkinThickness", "Triceps skin fold", "float", 20, 0, 100, unit="mm",
                  group="Body"),
            Field("Insulin", "Serum insulin", "float", 80, 0, 900, unit="µU/mL",
                  group="Bloodwork"),
            Field("BMI", "BMI", "float", 24.0, 0.0, 70.0, unit="kg/m²", group="Body",
                  help="30 and above is the obesity range."),
            Field("DiabetesPedigreeFunction", "Pedigree function", "float", 0.5, 0.0, 3.0,
                  group="Demographics", help="Family-history likelihood score."),
            Field("Age", "Age", "int", 35, 1, 120, unit="years", group="Demographics"),
        ),
    ),
    Disease(
        slug="heart-disease",
        name="Heart Disease",
        blurb="Cleveland heart disease dataset. Thirteen cardiac and exercise measures.",
        model="heart",
        threshold=45,
        # `heart.sav` was trained with 1 meaning *absence* of disease, the
        # opposite of the usual Cleveland convention. Feeding it a 71-year-old
        # with cholesterol 310, exercise angina, and three affected vessels
        # returns P(class 1) = 0.01; a healthy 29-year-old returns 0.98. The
        # coefficient signs agree — `ca` and `exang` both push away from class
        # 1. Assuming the convention instead of measuring it would have
        # inverted the model's contribution to every cardiac screening.
        positive_class=0,
        caveat=(
            "The shipped heart model encodes its classes inverted relative to the usual "
            "Cleveland convention. This is handled, but it means the model was trained by "
            "someone who may not have verified their label mapping."
        ),
        fields=(
            Field("age", "Age", "int", 45, 1, 120, unit="years", group="Demographics"),
            Field("sex", "Sex", "choice", 1, 0, 1, choices=SEX_10, group="Demographics"),
            Field("cp", "Chest pain type", "choice", 0, 0, 3, group="Symptoms",
                  choices=(Choice(0, "Typical angina"), Choice(1, "Atypical angina"),
                           Choice(2, "Non-anginal pain"), Choice(3, "Asymptomatic"))),
            Field("trestbps", "Resting BP", "int", 120, 50, 250, unit="mm Hg", group="Vitals"),
            Field("chol", "Cholesterol", "int", 180, 50, 600, unit="mg/dL", group="Bloodwork",
                  help="Above 240 is considered high."),
            Field("fbs", "Fasting sugar > 120 mg/dL", "choice", 0, 0, 1, choices=NO_YES_01,
                  group="Bloodwork"),
            Field("restecg", "Resting ECG", "choice", 0, 0, 2, group="Cardiac",
                  choices=(Choice(0, "Normal"), Choice(1, "ST-T abnormality"),
                           Choice(2, "Left ventricular hypertrophy"))),
            Field("thalach", "Max heart rate", "int", 150, 50, 220, unit="bpm", group="Cardiac"),
            Field("exang", "Exercise-induced angina", "choice", 0, 0, 1, choices=NO_YES_01,
                  group="Cardiac"),
            Field("oldpeak", "ST depression", "float", 0.0, 0.0, 10.0, group="Cardiac",
                  help="Induced by exercise relative to rest. 2 and above is notable."),
            Field("slope", "Peak ST segment slope", "choice", 1, 0, 2, group="Cardiac",
                  choices=(Choice(0, "Upsloping"), Choice(1, "Flat"), Choice(2, "Downsloping"))),
            Field("ca", "Major vessels coloured", "int", 0, 0, 3, group="Cardiac",
                  help="Count of major vessels visible under fluoroscopy, 0-3."),
            Field("thal", "Thalassemia", "choice", 2, 0, 3, group="Bloodwork",
                  choices=(Choice(0, "Unknown"), Choice(1, "Normal"),
                           Choice(2, "Fixed defect"), Choice(3, "Reversible defect"))),
        ),
    ),
    # 22 fields, not 13. `predictors.py` defines this disease twice and the
    # 22-field definition is the one Python keeps — which is also the one
    # `parkinsons.sav` was trained on (n_features_in_ == 22). Stated once here,
    # and asserted against the model file in tests/test_schemas.py.
    Disease(
        slug="parkinsons",
        name="Parkinson's",
        blurb="Oxford voice dataset. Twenty-two acoustic measures from sustained phonation.",
        model="parkinsons",
        threshold=45,
        caveat=(
            "This model is an SVC trained without probability=True, so it can report a "
            "class but not a calibrated probability. The score shown is rule-based."
        ),
        fields=(
            Field("MDVP:Fo(Hz)", "Average vocal frequency", "float", 154.0, 80.0, 300.0,
                  unit="Hz", group="Frequency"),
            Field("MDVP:Fhi(Hz)", "Maximum vocal frequency", "float", 197.0, 100.0, 600.0,
                  unit="Hz", group="Frequency"),
            Field("MDVP:Flo(Hz)", "Minimum vocal frequency", "float", 116.0, 60.0, 240.0,
                  unit="Hz", group="Frequency"),
            Field("MDVP:Jitter(%)", "Jitter", "float", 0.006, 0.0, 0.05, unit="%",
                  group="Jitter", help="Cycle-to-cycle frequency variation. Elevated above 1%."),
            Field("MDVP:Jitter(Abs)", "Jitter (absolute)", "float", 0.00004, 0.0, 0.001,
                  unit="s", group="Jitter"),
            Field("MDVP:RAP", "Relative amplitude perturbation", "float", 0.003, 0.0, 0.03,
                  group="Jitter"),
            Field("MDVP:PPQ", "Five-point period perturbation", "float", 0.003, 0.0, 0.03,
                  group="Jitter"),
            Field("Jitter:DDP", "Jitter DDP", "float", 0.009, 0.0, 0.09, group="Jitter"),
            Field("MDVP:Shimmer", "Shimmer", "float", 0.03, 0.0, 0.2, group="Shimmer",
                  help="Cycle-to-cycle amplitude variation."),
            Field("MDVP:Shimmer(dB)", "Shimmer (dB)", "float", 0.28, 0.0, 2.0, unit="dB",
                  group="Shimmer"),
            Field("Shimmer:APQ3", "Three-point amplitude perturbation", "float", 0.015, 0.0, 0.1,
                  group="Shimmer"),
            Field("Shimmer:APQ5", "Five-point amplitude perturbation", "float", 0.018, 0.0, 0.1,
                  group="Shimmer"),
            Field("MDVP:APQ", "Amplitude perturbation quotient", "float", 0.024, 0.0, 0.15,
                  group="Shimmer"),
            Field("Shimmer:DDA", "Shimmer DDA", "float", 0.045, 0.0, 0.3, group="Shimmer"),
            Field("NHR", "Noise-to-harmonics ratio", "float", 0.02, 0.0, 1.0, group="Noise"),
            Field("HNR", "Harmonics-to-noise ratio", "float", 21.0, 5.0, 35.0, unit="dB",
                  group="Noise", help="Lower is worse. Below 18 is a concern."),
            Field("RPDE", "Recurrence period density entropy", "float", 0.5, 0.0, 1.0,
                  group="Nonlinear"),
            Field("DFA", "Detrended fluctuation analysis", "float", 0.7, 0.0, 1.0,
                  group="Nonlinear"),
            Field("spread1", "Frequency spread 1", "float", -5.0, -10.0, 0.0, group="Nonlinear"),
            Field("spread2", "Frequency spread 2", "float", 0.2, 0.0, 1.0, group="Nonlinear"),
            Field("D2", "Correlation dimension", "float", 2.3, 0.0, 5.0, group="Nonlinear"),
            Field("PPE", "Pitch period entropy", "float", 0.2, 0.0, 1.0, group="Nonlinear"),
        ),
    ),
    Disease(
        slug="liver-disease",
        name="Liver Disease",
        blurb="Indian Liver Patient Dataset. Ten liver-function and demographic measures.",
        model="liver",
        threshold=40,
        # Per the ILPD convention the classes are [1, 2], not [0, 1], and 1 is
        # the disease label. Assuming 1 == positive happens to be right here,
        # but only because the field is explicit rather than defaulted.
        positive_class=1,
        fields=(
            Field("Age", "Age", "int", 45, 1, 100, unit="years", group="Demographics"),
            Field("Gender", "Sex", "choice", 1, 0, 1, choices=SEX_10, group="Demographics"),
            Field("Total_Bilirubin", "Total bilirubin", "float", 1.0, 0.0, 80.0, unit="mg/dL",
                  group="Bilirubin", help="Above 1.2 is elevated."),
            Field("Direct_Bilirubin", "Direct bilirubin", "float", 0.3, 0.0, 30.0, unit="mg/dL",
                  group="Bilirubin"),
            Field("Alkaline_Phosphotase", "Alkaline phosphatase", "int", 120, 50, 2000,
                  unit="IU/L", group="Enzymes"),
            Field("Alamine_Aminotransferase", "ALT", "int", 35, 1, 2000, unit="IU/L",
                  group="Enzymes", help="Alanine aminotransferase. Above 45 is elevated."),
            Field("Aspartate_Aminotransferase", "AST", "int", 40, 1, 2000, unit="IU/L",
                  group="Enzymes", help="Aspartate aminotransferase."),
            Field("Total_Protiens", "Total proteins", "float", 7.0, 0.0, 10.0, unit="g/dL",
                  group="Proteins"),
            Field("Albumin", "Albumin", "float", 4.0, 0.0, 6.0, unit="g/dL", group="Proteins",
                  help="Lower is worse. Below 3.5 is low."),
            Field("Albumin_and_Globulin_Ratio", "A/G ratio", "float", 1.5, 0.0, 3.0,
                  group="Proteins"),
        ),
    ),
    Disease(
        slug="hepatitis",
        name="Hepatitis",
        blurb="UCI hepatitis dataset. Twelve symptom and liver-function measures.",
        model="hepatitis",
        threshold=40,
        fields=(
            Field("age", "Age", "int", 35, 1, 100, unit="years", group="Demographics"),
            Field("sex", "Sex", "choice", 1, 0, 1, choices=SEX_10, group="Demographics"),
            _flag12("steroid", "On steroids", group="Treatment"),
            _flag12("antivirals", "On antivirals", group="Treatment"),
            _flag12("fatigue", "Fatigue"),
            _flag12("malaise", "Malaise"),
            _flag12("anorexia", "Anorexia"),
            _flag12("liver_big", "Enlarged liver", group="Examination"),
            _flag12("liver_firm", "Firm liver", group="Examination"),
            _flag12("spleen_palpable", "Palpable spleen", group="Examination"),
            Field("bilirubin", "Bilirubin", "float", 0.8, 0.0, 8.0, unit="mg/dL",
                  group="Bloodwork", help="Above 1.2 is elevated."),
            Field("albumin", "Albumin", "float", 4.0, 0.0, 6.0, unit="g/dL", group="Bloodwork",
                  help="Lower is worse. Below 3.5 is low."),
        ),
    ),
    Disease(
        slug="lung-cancer",
        name="Lung Cancer",
        blurb="Survey-based lung cancer dataset. Fifteen risk factors and symptoms.",
        model="lung_cancer",
        threshold=45,
        caveat=(
            "This dataset is a symptom survey, not imaging or histology. It reflects "
            "self-reported risk factors and cannot detect a tumour."
        ),
        fields=(
            Field("GENDER", "Sex", "choice", 1, 0, 1, choices=SEX_10, group="Demographics"),
            Field("AGE", "Age", "int", 45, 1, 100, unit="years", group="Demographics"),
            _flag12("SMOKING", "Smoking history", group="Risk factors"),
            _flag12("ALCOHOL", "Alcohol consumption", group="Risk factors"),
            _flag12("PEER_PRESSURE", "Peer pressure", group="Risk factors"),
            _flag12("ANXIETY", "Anxiety", group="Risk factors"),
            _flag12("CHRONIC_DISEASE", "Chronic disease", group="Risk factors"),
            _flag12("ALLERGY", "Allergy", group="Risk factors"),
            _flag12("YELLOW_FINGERS", "Yellow fingers"),
            _flag12("FATIGUE", "Fatigue"),
            _flag12("WHEEZING", "Wheezing"),
            _flag12("COUGHING", "Coughing"),
            _flag12("SHORTNESS_OF_BREATH", "Shortness of breath"),
            _flag12("SWALLOWING_DIFFICULTY", "Swallowing difficulty"),
            _flag12("CHEST_PAIN", "Chest pain"),
        ),
    ),
    Disease(
        slug="kidney-disease",
        name="Chronic Kidney Disease",
        blurb="UCI CKD dataset. Twenty-four urine, blood, and comorbidity measures.",
        model="kidney",
        threshold=35,
        # Inverted for the same reason as heart disease: class 1 is the healthy
        # class in this pickle. Confirmed by probing, not assumed.
        positive_class=0,
        caveat=(
            "The shipped kidney model encodes its classes inverted relative to the UCI "
            "dataset's convention. This is handled, but the model file's provenance is "
            "worth treating with caution."
        ),
        fields=(
            Field("age", "Age", "int", 45, 1, 100, unit="years", group="Demographics"),
            Field("bp", "Blood pressure", "int", 80, 40, 200, unit="mm Hg", group="Vitals"),
            Field("sg", "Specific gravity", "float", 1.02, 1.0, 1.05, group="Urine"),
            Field("al", "Albumin", "int", 0, 0, 5, group="Urine", help="Graded 0-5."),
            Field("su", "Sugar", "int", 0, 0, 5, group="Urine", help="Graded 0-5."),
            Field("rbc", "Red blood cells", "choice", 0, 0, 1, group="Urine",
                  choices=(Choice(0, "Normal"), Choice(1, "Abnormal"))),
            Field("pc", "Pus cells", "choice", 0, 0, 1, group="Urine",
                  choices=(Choice(0, "Normal"), Choice(1, "Abnormal"))),
            Field("pcc", "Pus cell clumps", "choice", 0, 0, 1, group="Urine",
                  choices=(Choice(0, "Not present"), Choice(1, "Present"))),
            Field("ba", "Bacteria", "choice", 0, 0, 1, group="Urine",
                  choices=(Choice(0, "Not present"), Choice(1, "Present"))),
            Field("bgr", "Random blood glucose", "int", 100, 40, 500, unit="mg/dL",
                  group="Bloodwork"),
            Field("bu", "Blood urea", "int", 30, 1, 400, unit="mg/dL", group="Bloodwork"),
            Field("sc", "Serum creatinine", "float", 1.0, 0.0, 20.0, unit="mg/dL",
                  group="Bloodwork", help="Above 1.3 is elevated."),
            Field("sod", "Sodium", "int", 138, 100, 200, unit="mEq/L", group="Electrolytes"),
            Field("pot", "Potassium", "float", 4.5, 1.0, 10.0, unit="mEq/L",
                  group="Electrolytes"),
            Field("hemo", "Haemoglobin", "float", 14.0, 3.0, 20.0, unit="g/dL",
                  group="Blood count", help="Lower is worse. Below 12 is low."),
            Field("pcv", "Packed cell volume", "int", 44, 10, 60, unit="%", group="Blood count"),
            Field("wc", "White blood cell count", "int", 7800, 2200, 26400, unit="cells/µL",
                  group="Blood count"),
            Field("rc", "Red blood cell count", "float", 5.2, 2.0, 8.0, unit="M/µL",
                  group="Blood count"),
            _flag01("htn", "Hypertension", group="Comorbidities"),
            _flag01("dm", "Diabetes mellitus", group="Comorbidities"),
            _flag01("cad", "Coronary artery disease", group="Comorbidities"),
            Field("appet", "Appetite", "choice", 0, 0, 1, group="Symptoms",
                  choices=(Choice(0, "Good"), Choice(1, "Poor"))),
            _flag01("pe", "Pedal oedema", group="Symptoms"),
            _flag01("ane", "Anaemia", group="Symptoms"),
        ),
    ),
    Disease(
        slug="breast-cancer",
        name="Breast Cancer",
        blurb="Wisconsin diagnostic dataset. Thirty cell-nucleus measures from a needle aspirate.",
        model="breast_cancer",
        threshold=45,
        caveat=(
            "The shipped breast_cancer.sav is corrupt and fails to unpickle. The loader "
            "falls back to breast_cancer.joblib, and if that is also unavailable it trains "
            "a RandomForest on sklearn's bundled Wisconsin data at startup."
        ),
        fields=(
            Field("mean_radius", "Mean radius", "float", 14.0, 5.0, 30.0, group="Mean"),
            Field("mean_texture", "Mean texture", "float", 19.0, 5.0, 40.0, group="Mean"),
            Field("mean_perimeter", "Mean perimeter", "float", 92.0, 40.0, 200.0, group="Mean"),
            Field("mean_area", "Mean area", "float", 655.0, 100.0, 2500.0, group="Mean"),
            Field("mean_smoothness", "Mean smoothness", "float", 0.1, 0.05, 0.2, group="Mean"),
            Field("mean_compactness", "Mean compactness", "float", 0.1, 0.0, 0.35, group="Mean"),
            Field("mean_concavity", "Mean concavity", "float", 0.09, 0.0, 0.5, group="Mean"),
            Field("mean_concave_points", "Mean concave points", "float", 0.05, 0.0, 0.2,
                  group="Mean", help="One of the strongest single predictors in this dataset."),
            Field("mean_symmetry", "Mean symmetry", "float", 0.18, 0.1, 0.35, group="Mean"),
            Field("mean_fractal_dimension", "Mean fractal dimension", "float", 0.06, 0.04, 0.1,
                  group="Mean"),
            Field("radius_error", "Radius error", "float", 0.4, 0.1, 2.5, group="Error"),
            Field("texture_error", "Texture error", "float", 1.2, 0.3, 4.0, group="Error"),
            Field("perimeter_error", "Perimeter error", "float", 2.9, 0.5, 20.0, group="Error"),
            Field("area_error", "Area error", "float", 40.0, 5.0, 250.0, group="Error"),
            Field("smoothness_error", "Smoothness error", "float", 0.007, 0.001, 0.03,
                  group="Error"),
            Field("compactness_error", "Compactness error", "float", 0.025, 0.002, 0.14,
                  group="Error"),
            Field("concavity_error", "Concavity error", "float", 0.03, 0.0, 0.4, group="Error"),
            Field("concave_points_error", "Concave points error", "float", 0.012, 0.0, 0.05,
                  group="Error"),
            Field("symmetry_error", "Symmetry error", "float", 0.02, 0.007, 0.08, group="Error"),
            Field("fractal_dimension_error", "Fractal dimension error", "float", 0.004, 0.0008,
                  0.03, group="Error"),
            Field("worst_radius", "Worst radius", "float", 16.0, 7.0, 40.0, group="Worst",
                  help="Above 18 is elevated."),
            Field("worst_texture", "Worst texture", "float", 25.0, 10.0, 50.0, group="Worst"),
            Field("worst_perimeter", "Worst perimeter", "float", 107.0, 50.0, 260.0,
                  group="Worst"),
            Field("worst_area", "Worst area", "float", 880.0, 150.0, 4300.0, group="Worst"),
            Field("worst_smoothness", "Worst smoothness", "float", 0.13, 0.07, 0.25,
                  group="Worst"),
            Field("worst_compactness", "Worst compactness", "float", 0.25, 0.02, 1.1,
                  group="Worst"),
            Field("worst_concavity", "Worst concavity", "float", 0.27, 0.0, 1.3, group="Worst"),
            Field("worst_concave_points", "Worst concave points", "float", 0.11, 0.0, 0.3,
                  group="Worst", help="Above 0.15 is elevated."),
            Field("worst_symmetry", "Worst symmetry", "float", 0.29, 0.15, 0.7, group="Worst"),
            Field("worst_fractal_dimension", "Worst fractal dimension", "float", 0.08, 0.05,
                  0.25, group="Worst"),
        ),
    ),
    # No model file ships for jaundice. The prototype set `"model": None` and
    # scored it purely from clinical thresholds; that is kept, and the API
    # reports `model_available: false` so the UI can say so rather than
    # implying an estimator ran.
    Disease(
        slug="jaundice",
        name="Jaundice",
        blurb="Rule-based bilirubin screening. No trained model ships for this condition.",
        model=None,
        threshold=35,
        caveat=(
            "No trained model exists for jaundice in this repository. This score comes "
            "entirely from published clinical thresholds."
        ),
        fields=(
            Field("Age", "Age", "int", 35, 1, 100, unit="years", group="Demographics"),
            Field("Total_Bilirubin", "Total bilirubin", "float", 1.0, 0.0, 30.0, unit="mg/dL",
                  group="Bilirubin", help="Above 1.2 is elevated."),
            Field("Direct_Bilirubin", "Direct bilirubin", "float", 0.3, 0.0, 20.0, unit="mg/dL",
                  group="Bilirubin", help="Above 0.3 is elevated."),
            Field("Alkaline_Phosphotase", "Alkaline phosphatase", "int", 120, 20, 2000,
                  unit="IU/L", group="Enzymes"),
            Field("Alamine_Aminotransferase", "ALT", "int", 35, 1, 2000, unit="IU/L",
                  group="Enzymes"),
            Field("Aspartate_Aminotransferase", "AST", "int", 35, 1, 2000, unit="IU/L",
                  group="Enzymes"),
            _flag01("dark_urine", "Dark urine", group="Symptoms"),
            _flag01("yellow_eyes", "Yellow eyes or skin", group="Symptoms"),
        ),
    ),
)


def _validate_registry(registry: tuple[Disease, ...]) -> None:
    """Catch at import time the class of bug that shipped in the prototype.

    A duplicate slug there was invisible — the dict literal simply dropped the
    first definition. Here it raises before the app can serve a request.
    """
    seen_slugs: set[str] = set()
    for disease in registry:
        if disease.slug in seen_slugs:
            raise ValueError(f"Duplicate disease slug: {disease.slug!r}")
        seen_slugs.add(disease.slug)

        seen_fields: set[str] = set()
        for f in disease.fields:
            if f.name in seen_fields:
                raise ValueError(f"Duplicate field {f.name!r} in {disease.slug!r}")
            seen_fields.add(f.name)
            if not f.minimum <= f.default <= f.maximum:
                raise ValueError(
                    f"{disease.slug}.{f.name}: default {f.default} outside "
                    f"[{f.minimum}, {f.maximum}]"
                )
            if f.kind == "choice" and not f.choices:
                raise ValueError(f"{disease.slug}.{f.name}: choice field has no choices")


_validate_registry(REGISTRY)

BY_SLUG: dict[str, Disease] = {d.slug: d for d in REGISTRY}


def get_disease(slug: str) -> Disease | None:
    return BY_SLUG.get(slug)
