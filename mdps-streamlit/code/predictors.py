"""Numerical disease predictor wrappers around .sav / .joblib model files.

Each predictor describes its input fields so the UI can render forms
generically. If a model file is missing, the predictor reports unavailable.
"""
from pathlib import Path
import warnings
import joblib
import pickle
import numpy as np

MODELS = Path(__file__).resolve().parent.parent / "models"


def _load(name: str):
    if not name:
        return None
    for ext in (".joblib", ".sav", ".pkl"):
        p = MODELS / f"{name}{ext}"
        if p.exists():
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    return joblib.load(p)
            except Exception:
                try:
                    with open(p, "rb") as f:
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            return pickle.load(f)
                except Exception:
                    return None
    return None


# Each entry: model filename stem, ordered list of (field, label, type, default, min, max)
SCHEMAS = {
    "Diabetes": {
        "model": "diabetes",
        "fields": [
            ("Pregnancies", "Pregnancies", "int", 1, 0, 20),
            ("Glucose", "Glucose", "float", 100, 0, 300),
            ("BloodPressure", "Blood Pressure", "float", 72, 0, 200),
            ("SkinThickness", "Skin Thickness", "float", 20, 0, 100),
            ("Insulin", "Insulin", "float", 80, 0, 900),
            ("BMI", "BMI", "float", 24.0, 0.0, 70.0),
            ("DiabetesPedigreeFunction", "Diabetes Pedigree Function", "float", 0.5, 0.0, 3.0),
            ("Age", "Age", "int", 35, 1, 120),
        ],
    },
    "Heart Disease": {
        "model": "heart",
        "fields": [
            ("age", "Age", "int", 45, 1, 120),
            ("sex", "Sex (1=M, 0=F)", "int", 1, 0, 1),
            ("cp", "Chest Pain Type (0-3)", "int", 0, 0, 3),
            ("trestbps", "Resting BP", "int", 120, 50, 250),
            ("chol", "Cholesterol", "int", 180, 50, 600),
            ("fbs", "Fasting Sugar >120 (1/0)", "int", 0, 0, 1),
            ("restecg", "Rest ECG (0-2)", "int", 0, 0, 2),
            ("thalach", "Max Heart Rate", "int", 150, 50, 220),
            ("exang", "Exercise Angina (1/0)", "int", 0, 0, 1),
            ("oldpeak", "ST Depression", "float", 0.0, 0.0, 10.0),
            ("slope", "Slope (0-2)", "int", 1, 0, 2),
            ("ca", "Major Vessels (0-3)", "int", 0, 0, 3),
            ("thal", "Thal (0-3)", "int", 2, 0, 3),
        ],
    },
    "Parkinson's": {
        "model": "parkinsons",
        "fields": [
            ("MDVP:Fo(Hz)", "MDVP Fo(Hz)", "float", 154.0, 80.0, 300.0),
            ("MDVP:Fhi(Hz)", "MDVP Fhi(Hz)", "float", 197.0, 100.0, 600.0),
            ("MDVP:Flo(Hz)", "MDVP Flo(Hz)", "float", 116.0, 60.0, 240.0),
            ("MDVP:Jitter(%)", "Jitter %", "float", 0.006, 0.0, 0.05),
            ("MDVP:Shimmer", "Shimmer", "float", 0.03, 0.0, 0.2),
            ("NHR", "NHR", "float", 0.02, 0.0, 1.0),
            ("HNR", "HNR", "float", 21.0, 5.0, 35.0),
            ("RPDE", "RPDE", "float", 0.5, 0.0, 1.0),
            ("DFA", "DFA", "float", 0.7, 0.0, 1.0),
            ("spread1", "spread1", "float", -5.0, -10.0, 0.0),
            ("spread2", "spread2", "float", 0.2, 0.0, 1.0),
            ("D2", "D2", "float", 2.3, 0.0, 5.0),
            ("PPE", "PPE", "float", 0.2, 0.0, 1.0),
        ],
    },"Parkinson's": {
    "model": "parkinsons",
    "fields": [
        ("MDVP:Fo(Hz)", "MDVP Fo(Hz)", "float", 154.0, 80.0, 300.0),
        ("MDVP:Fhi(Hz)", "MDVP Fhi(Hz)", "float", 197.0, 100.0, 600.0),
        ("MDVP:Flo(Hz)", "MDVP Flo(Hz)", "float", 116.0, 60.0, 240.0),
        ("MDVP:Jitter(%)", "Jitter %", "float", 0.006, 0.0, 0.05),
        ("MDVP:Jitter(Abs)", "Jitter Abs", "float", 0.00004, 0.0, 0.001),
        ("MDVP:RAP", "RAP", "float", 0.003, 0.0, 0.03),
        ("MDVP:PPQ", "PPQ", "float", 0.003, 0.0, 0.03),
        ("Jitter:DDP", "Jitter DDP", "float", 0.009, 0.0, 0.09),
        ("MDVP:Shimmer", "Shimmer", "float", 0.03, 0.0, 0.2),
        ("MDVP:Shimmer(dB)", "Shimmer dB", "float", 0.28, 0.0, 2.0),
        ("Shimmer:APQ3", "Shimmer APQ3", "float", 0.015, 0.0, 0.1),
        ("Shimmer:APQ5", "Shimmer APQ5", "float", 0.018, 0.0, 0.1),
        ("MDVP:APQ", "MDVP APQ", "float", 0.024, 0.0, 0.15),
        ("Shimmer:DDA", "Shimmer DDA", "float", 0.045, 0.0, 0.3),
        ("NHR", "NHR", "float", 0.02, 0.0, 1.0),
        ("HNR", "HNR", "float", 21.0, 5.0, 35.0),
        ("RPDE", "RPDE", "float", 0.5, 0.0, 1.0),
        ("DFA", "DFA", "float", 0.7, 0.0, 1.0),
        ("spread1", "spread1", "float", -5.0, -10.0, 0.0),
        ("spread2", "spread2", "float", 0.2, 0.0, 1.0),
        ("D2", "D2", "float", 2.3, 0.0, 5.0),
        ("PPE", "PPE", "float", 0.2, 0.0, 1.0),
    ],
},
    "Liver Disease": {
        "model": "liver",
        "fields": [
            ("Age", "Age", "int", 45, 1, 100),
            ("Gender", "Gender (1=M, 0=F)", "int", 1, 0, 1),
            ("Total_Bilirubin", "Total Bilirubin", "float", 1.0, 0.0, 80.0),
            ("Direct_Bilirubin", "Direct Bilirubin", "float", 0.3, 0.0, 30.0),
            ("Alkaline_Phosphotase", "Alk Phosphatase", "int", 120, 50, 2000),
            ("Alamine_Aminotransferase", "ALT", "int", 35, 1, 2000),
            ("Aspartate_Aminotransferase", "AST", "int", 40, 1, 2000),
            ("Total_Protiens", "Total Proteins", "float", 7.0, 0.0, 10.0),
            ("Albumin", "Albumin", "float", 4.0, 0.0, 6.0),
            ("Albumin_and_Globulin_Ratio", "A/G Ratio", "float", 1.5, 0.0, 3.0),
        ],
    },
    "Hepatitis": {
    "model": "hepatitis",
    "fields": [
        ("age", "Age", "int", 35, 1, 100),
        ("sex", "Sex (1=M, 0=F)", "int", 1, 0, 1),
        ("steroid", "Steroid (1=No, 2=Yes)", "int", 1, 1, 2),
        ("antivirals", "Antivirals (1=No, 2=Yes)", "int", 1, 1, 2),
        ("fatigue", "Fatigue (1=No, 2=Yes)", "int", 1, 1, 2),
        ("malaise", "Malaise (1=No, 2=Yes)", "int", 1, 1, 2),
        ("anorexia", "Anorexia (1=No, 2=Yes)", "int", 1, 1, 2),
        ("liver_big", "Liver Big (1=No, 2=Yes)", "int", 1, 1, 2),
        ("liver_firm", "Liver Firm (1=No, 2=Yes)", "int", 1, 1, 2),
        ("spleen_palpable", "Spleen Palpable (1=No, 2=Yes)", "int", 1, 1, 2),
        ("bilirubin", "Bilirubin", "float", 0.8, 0.0, 8.0),
        ("albumin", "Albumin", "float", 4.0, 0.0, 6.0),
    ],
},
    "Lung Cancer": {
        "model": "lung_cancer",
        "fields": [
            ("GENDER", "Gender (1=M, 0=F)", "int", 1, 0, 1),
            ("AGE", "Age", "int", 45, 1, 100),
            ("SMOKING", "Smoking (1=No, 2=Yes)", "int", 1, 1, 2),
            ("YELLOW_FINGERS", "Yellow Fingers", "int", 1, 1, 2),
            ("ANXIETY", "Anxiety", "int", 1, 1, 2),
            ("PEER_PRESSURE", "Peer Pressure", "int", 1, 1, 2),
            ("CHRONIC_DISEASE", "Chronic Disease", "int", 1, 1, 2),
            ("FATIGUE", "Fatigue", "int", 1, 1, 2),
            ("ALLERGY", "Allergy", "int", 1, 1, 2),
            ("WHEEZING", "Wheezing", "int", 1, 1, 2),
            ("ALCOHOL", "Alcohol", "int", 1, 1, 2),
            ("COUGHING", "Coughing", "int", 1, 1, 2),
            ("SHORTNESS_OF_BREATH", "Shortness of Breath", "int", 1, 1, 2),
            ("SWALLOWING_DIFFICULTY", "Swallowing Difficulty", "int", 1, 1, 2),
            ("CHEST_PAIN", "Chest Pain", "int", 1, 1, 2),
        ],
    },
    "Chronic Kidney Disease": {
    "model": "kidney",
    "fields": [
        ("age", "Age", "int", 45, 1, 100),
        ("bp", "Blood Pressure", "int", 80, 40, 200),
        ("sg", "Specific Gravity", "float", 1.02, 1.0, 1.05),
        ("al", "Albumin (0-5)", "int", 0, 0, 5),
        ("su", "Sugar (0-5)", "int", 0, 0, 5),
        ("rbc", "Red Blood Cells (0=normal,1=abnormal)", "int", 0, 0, 1),
        ("pc", "Pus Cell (0=normal,1=abnormal)", "int", 0, 0, 1),
        ("pcc", "Pus Cell Clumps (0=notpresent,1=present)", "int", 0, 0, 1),
        ("ba", "Bacteria (0=notpresent,1=present)", "int", 0, 0, 1),
        ("bgr", "Blood Glucose Random", "int", 100, 40, 500),
        ("bu", "Blood Urea", "int", 30, 1, 400),
        ("sc", "Serum Creatinine", "float", 1.0, 0.0, 20.0),
        ("sod", "Sodium", "int", 138, 100, 200),
        ("pot", "Potassium", "float", 4.5, 1.0, 10.0),
        ("hemo", "Hemoglobin", "float", 14.0, 3.0, 20.0),
        ("pcv", "Packed Cell Volume", "int", 44, 10, 60),
        ("wc", "White Blood Cell Count", "int", 7800, 2200, 26400),
        ("rc", "Red Blood Cell Count", "float", 5.2, 2.0, 8.0),
        ("htn", "Hypertension (0=no,1=yes)", "int", 0, 0, 1),
        ("dm", "Diabetes Mellitus (0=no,1=yes)", "int", 0, 0, 1),
        ("cad", "Coronary Artery Disease (0=no,1=yes)", "int", 0, 0, 1),
        ("appet", "Appetite (0=good,1=poor)", "int", 0, 0, 1),
        ("pe", "Pedal Edema (0=no,1=yes)", "int", 0, 0, 1),
        ("ane", "Anemia (0=no,1=yes)", "int", 0, 0, 1),
    ],
},
    "Jaundice": {
    "model": None,
    "fields": [
        ("Age", "Age", "int", 35, 1, 100),
        ("Total_Bilirubin", "Total Bilirubin", "float", 1.0, 0.0, 30.0),
        ("Direct_Bilirubin", "Direct Bilirubin", "float", 0.3, 0.0, 20.0),
        ("Alkaline_Phosphotase", "Alk Phosphatase", "int", 120, 20, 2000),
        ("Alamine_Aminotransferase", "ALT", "int", 35, 1, 2000),
        ("Aspartate_Aminotransferase", "AST", "int", 35, 1, 2000),
        ("dark_urine", "Dark Urine (0=no,1=yes)", "int", 0, 0, 1),
        ("yellow_eyes", "Yellow Eyes/Skin (0=no,1=yes)", "int", 0, 0, 1),
    ],
},
    "Breast Cancer": {
    "model": "breast_cancer",
    "fields": [
        ("mean_radius", "Mean Radius", "float", 14.0, 5.0, 30.0),
        ("mean_texture", "Mean Texture", "float", 19.0, 5.0, 40.0),
        ("mean_perimeter", "Mean Perimeter", "float", 92.0, 40.0, 200.0),
        ("mean_area", "Mean Area", "float", 655.0, 100.0, 2500.0),
        ("mean_smoothness", "Mean Smoothness", "float", 0.1, 0.05, 0.2),
        ("mean_compactness", "Mean Compactness", "float", 0.1, 0.0, 0.35),
        ("mean_concavity", "Mean Concavity", "float", 0.09, 0.0, 0.5),
        ("mean_concave_points", "Mean Concave Points", "float", 0.05, 0.0, 0.2),
        ("mean_symmetry", "Mean Symmetry", "float", 0.18, 0.1, 0.35),
        ("mean_fractal_dimension", "Mean Fractal Dimension", "float", 0.06, 0.04, 0.1),
        ("radius_error", "Radius Error", "float", 0.4, 0.1, 2.5),
        ("texture_error", "Texture Error", "float", 1.2, 0.3, 4.0),
        ("perimeter_error", "Perimeter Error", "float", 2.9, 0.5, 20.0),
        ("area_error", "Area Error", "float", 40.0, 5.0, 250.0),
        ("smoothness_error", "Smoothness Error", "float", 0.007, 0.001, 0.03),
        ("compactness_error", "Compactness Error", "float", 0.025, 0.002, 0.14),
        ("concavity_error", "Concavity Error", "float", 0.03, 0.0, 0.4),
        ("concave_points_error", "Concave Points Error", "float", 0.012, 0.0, 0.05),
        ("symmetry_error", "Symmetry Error", "float", 0.02, 0.007, 0.08),
        ("fractal_dimension_error", "Fractal Dimension Error", "float", 0.004, 0.0008, 0.03),
        ("worst_radius", "Worst Radius", "float", 16.0, 7.0, 40.0),
        ("worst_texture", "Worst Texture", "float", 25.0, 10.0, 50.0),
        ("worst_perimeter", "Worst Perimeter", "float", 107.0, 50.0, 260.0),
        ("worst_area", "Worst Area", "float", 880.0, 150.0, 4300.0),
        ("worst_smoothness", "Worst Smoothness", "float", 0.13, 0.07, 0.25),
        ("worst_compactness", "Worst Compactness", "float", 0.25, 0.02, 1.1),
        ("worst_concavity", "Worst Concavity", "float", 0.27, 0.0, 1.3),
        ("worst_concave_points", "Worst Concave Points", "float", 0.11, 0.0, 0.3),
        ("worst_symmetry", "Worst Symmetry", "float", 0.29, 0.15, 0.7),
        ("worst_fractal_dimension", "Worst Fractal Dimension", "float", 0.08, 0.05, 0.25),
    ],
},
}


POSITIVE_CLASSES = {
    "Liver Disease": 1,
}

RISK_THRESHOLDS = {
    "Diabetes": 40,
    "Heart Disease": 45,
    "Parkinson's": 45,
    "Liver Disease": 40,
    "Hepatitis": 40,
    "Lung Cancer": 45,
    "Chronic Kidney Disease": 35,
    "Breast Cancer": 45,
    "Jaundice": 35,
}


def _build_breast_cancer_model():
    try:
        from sklearn.datasets import load_breast_cancer
        from sklearn.ensemble import RandomForestClassifier
    except Exception:
        return None

    data = load_breast_cancer()
    y = (data.target == 0).astype(int)
    model = RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        random_state=42,
    )
    model.fit(data.data, y)
    return model


def _bounded(value, normal, danger, inverse=False):
    try:
        value = float(value)
    except Exception:
        return 0
    if inverse:
        if value >= normal:
            return 0
        if value <= danger:
            return 100
        return int((normal - value) / max(normal - danger, 1e-6) * 100)
    if value <= normal:
        return 0
    if value >= danger:
        return 100
    return int((value - normal) / max(danger - normal, 1e-6) * 100)


def _flag(value, condition, points, reason, reasons):
    try:
        if condition(float(value)):
            reasons.append(reason)
            return points
    except Exception:
        pass
    return 0


def clinical_risk_score(disease: str, params: dict):
    reasons = []
    p = params
    score = 0

    if disease == "Diabetes":
        score += _bounded(p.get("Glucose"), 125, 220) * 0.45
        score += _bounded(p.get("BMI"), 30, 45) * 0.25
        score += _bounded(p.get("Age"), 45, 75) * 0.15
        score += _bounded(p.get("BloodPressure"), 130, 180) * 0.10
        score += _bounded(p.get("Insulin"), 180, 500) * 0.05
        _flag(p.get("Glucose"), lambda x: x >= 126, 1, "Glucose is in a diabetic/high-risk range.", reasons)
        _flag(p.get("BMI"), lambda x: x >= 30, 1, "BMI is in the obesity range.", reasons)
        _flag(p.get("BloodPressure"), lambda x: x >= 140, 1, "Blood pressure is elevated.", reasons)

    elif disease == "Heart Disease":
        score += _bounded(p.get("chol"), 200, 320) * 0.22
        score += _bounded(p.get("trestbps"), 130, 190) * 0.18
        score += _bounded(p.get("age"), 50, 80) * 0.15
        score += _bounded(p.get("thalach"), 140, 90, inverse=True) * 0.15
        score += _bounded(p.get("oldpeak"), 1.0, 4.0) * 0.12
        score += (25 if p.get("cp", 0) >= 2 else 0)
        score += (20 if p.get("exang", 0) == 1 else 0)
        score += (15 if p.get("ca", 0) >= 1 else 0)
        _flag(p.get("chol"), lambda x: x > 240, 1, "Cholesterol is high.", reasons)
        _flag(p.get("trestbps"), lambda x: x >= 140, 1, "Resting blood pressure is high.", reasons)
        _flag(p.get("oldpeak"), lambda x: x >= 2, 1, "ST depression is clinically notable.", reasons)

    elif disease == "Parkinson's":
        score += _bounded(p.get("MDVP:Jitter(%)"), 0.006, 0.02) * 0.22
        score += _bounded(p.get("MDVP:Shimmer"), 0.03, 0.10) * 0.18
        score += _bounded(p.get("NHR"), 0.03, 0.25) * 0.18
        score += _bounded(p.get("HNR"), 20, 10, inverse=True) * 0.18
        score += _bounded(p.get("PPE"), 0.2, 0.6) * 0.14
        score += _bounded(p.get("D2"), 2.5, 4.5) * 0.10
        _flag(p.get("MDVP:Jitter(%)"), lambda x: x > 0.01, 1, "Voice jitter is elevated.", reasons)
        _flag(p.get("HNR"), lambda x: x < 18, 1, "Harmonics-to-noise ratio is low.", reasons)

    elif disease == "Liver Disease":
        score += _bounded(p.get("Total_Bilirubin"), 1.2, 5.0) * 0.25
        score += _bounded(p.get("Direct_Bilirubin"), 0.3, 2.0) * 0.15
        score += _bounded(p.get("Alkaline_Phosphotase"), 150, 500) * 0.15
        score += _bounded(p.get("Alamine_Aminotransferase"), 45, 300) * 0.15
        score += _bounded(p.get("Aspartate_Aminotransferase"), 40, 300) * 0.15
        score += _bounded(p.get("Albumin"), 3.5, 2.2, inverse=True) * 0.15
        _flag(p.get("Total_Bilirubin"), lambda x: x > 1.2, 1, "Bilirubin is elevated.", reasons)
        _flag(p.get("Alamine_Aminotransferase"), lambda x: x > 45, 1, "ALT is elevated.", reasons)
        _flag(p.get("Albumin"), lambda x: x < 3.5, 1, "Albumin is low.", reasons)

    elif disease == "Hepatitis":
        score += _bounded(p.get("bilirubin"), 1.2, 5.0) * 0.25
        score += _bounded(p.get("albumin"), 3.5, 2.2, inverse=True) * 0.20
        score += (15 if p.get("fatigue") == 2 else 0)
        score += (10 if p.get("malaise") == 2 else 0)
        score += (10 if p.get("anorexia") == 2 else 0)
        score += (15 if p.get("liver_big") == 2 or p.get("liver_firm") == 2 else 0)
        _flag(p.get("bilirubin"), lambda x: x > 1.2, 1, "Bilirubin is elevated.", reasons)
        _flag(p.get("albumin"), lambda x: x < 3.5, 1, "Albumin is low.", reasons)

    elif disease == "Lung Cancer":
        score += _bounded(p.get("AGE"), 55, 85) * 0.15
        for key, weight, reason in [
            ("SMOKING", 18, "Smoking history is present."),
            ("YELLOW_FINGERS", 8, "Yellow fingers are reported."),
            ("CHRONIC_DISEASE", 8, "Chronic disease history is present."),
            ("FATIGUE", 8, "Fatigue is reported."),
            ("WHEEZING", 8, "Wheezing is reported."),
            ("COUGHING", 10, "Coughing is reported."),
            ("SHORTNESS_OF_BREATH", 12, "Shortness of breath is reported."),
            ("SWALLOWING_DIFFICULTY", 8, "Swallowing difficulty is reported."),
            ("CHEST_PAIN", 12, "Chest pain is reported."),
        ]:
            if p.get(key) == 2:
                score += weight
                reasons.append(reason)

    elif disease == "Chronic Kidney Disease":
        score += _bounded(p.get("bp"), 130, 190) * 0.12
        score += _bounded(p.get("al"), 0, 4) * 0.12
        score += _bounded(p.get("bgr"), 140, 300) * 0.10
        score += _bounded(p.get("bu"), 45, 150) * 0.12
        score += _bounded(p.get("sc"), 1.3, 5.0) * 0.20
        score += _bounded(p.get("hemo"), 12, 7, inverse=True) * 0.14
        score += (12 if p.get("htn") == 1 else 0)
        score += (10 if p.get("dm") == 1 else 0)
        score += (8 if p.get("pe") == 1 else 0)
        _flag(p.get("sc"), lambda x: x > 1.3, 1, "Serum creatinine is elevated.", reasons)
        _flag(p.get("hemo"), lambda x: x < 12, 1, "Hemoglobin is low.", reasons)

    elif disease == "Breast Cancer":
        score += _bounded(p.get("worst_concave_points"), 0.15, 0.28) * 0.25
        score += _bounded(p.get("mean_concave_points"), 0.08, 0.18) * 0.18
        score += _bounded(p.get("worst_radius"), 18, 32) * 0.16
        score += _bounded(p.get("worst_perimeter"), 115, 220) * 0.16
        score += _bounded(p.get("mean_concavity"), 0.12, 0.35) * 0.13
        score += _bounded(p.get("worst_texture"), 30, 45) * 0.12
        _flag(p.get("worst_concave_points"), lambda x: x > 0.15, 1, "Worst concave points are elevated.", reasons)
        _flag(p.get("worst_radius"), lambda x: x > 18, 1, "Worst radius is elevated.", reasons)

    elif disease == "Jaundice":
        score += _bounded(p.get("Total_Bilirubin"), 1.2, 5.0) * 0.35
        score += _bounded(p.get("Direct_Bilirubin"), 0.3, 2.0) * 0.20
        score += _bounded(p.get("Alkaline_Phosphotase"), 150, 500) * 0.12
        score += _bounded(p.get("Alamine_Aminotransferase"), 45, 300) * 0.12
        score += _bounded(p.get("Aspartate_Aminotransferase"), 40, 300) * 0.11
        score += (15 if p.get("dark_urine") == 1 else 0)
        score += (20 if p.get("yellow_eyes") == 1 else 0)
        _flag(p.get("Total_Bilirubin"), lambda x: x > 1.2, 1, "Total bilirubin is elevated.", reasons)
        _flag(p.get("Direct_Bilirubin"), lambda x: x > 0.3, 1, "Direct bilirubin is elevated.", reasons)
        if p.get("yellow_eyes") == 1:
            reasons.append("Yellow eyes or skin are reported.")

    score = int(min(100, max(0, score)))
    if not reasons:
        reasons.append("No strong abnormal clinical threshold was triggered.")
    return score, reasons


def _positive_probability(model, arr, disease):
    if not hasattr(model, "predict_proba"):
        return None
    try:
        proba = model.predict_proba(arr)[0]
        positive_class = POSITIVE_CLASSES.get(disease, 1)
        classes = list(getattr(model, "classes_", []))
        if positive_class in classes:
            return float(proba[classes.index(positive_class)])
    except Exception:
        return None
    return None


def _is_positive_prediction(disease, pred):
    return pred == POSITIVE_CLASSES.get(disease, 1)


def get_predictor(disease: str):
    schema = SCHEMAS[disease]
    model = _load(schema["model"])
    if model is None and disease == "Breast Cancer":
        model = _build_breast_cancer_model()
    return model, schema["fields"]


def run_prediction(model, values: list[float]):
    arr = np.array(values, dtype=float).reshape(1, -1)
    pred = model.predict(arr)[0]
    conf = None
    if hasattr(model, "predict_proba"):
        try:
            proba = model.predict_proba(arr)[0]
            conf = float(np.max(proba))
        except Exception:
            conf = None
    return int(pred) if not isinstance(pred, str) else pred, conf


def run_screening_prediction(disease: str, model, values: list[float], params: dict):
    arr = np.array(values, dtype=float).reshape(1, -1)
    rule_score, reasons = clinical_risk_score(disease, params)
    model_score = None

    if model is not None:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                pred = model.predict(arr)[0]
                positive_prob = _positive_probability(model, arr, disease)
            if positive_prob is not None:
                model_score = positive_prob * 100
            else:
                model_score = 65 if _is_positive_prediction(disease, pred) else 20
        except Exception:
            model_score = None

    if model_score is None:
        score = rule_score
        source = "clinical thresholds"
    else:
        score = int((rule_score * 0.70) + (model_score * 0.30))
        source = "hybrid clinical thresholds + model"

    threshold = RISK_THRESHOLDS.get(disease, 45)
    pred = 1 if score >= threshold else 0
    confidence = max(score, 100 - score) / 100
    return pred, confidence, {
        "risk_score": int(score),
        "threshold": threshold,
        "reasons": reasons,
        "source": source,
        "model_score": None if model_score is None else int(model_score),
        "rule_score": int(rule_score),
    }
