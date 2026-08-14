"""
Run this script once from your mdps folder to retrain the lung cancer model.
    python train_lung_cancer.py
"""
import pandas as pd
import pickle
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder

# ── Paths ───────────────────────────────────────────────
BASE = Path(__file__).parent
DATA = BASE / "datasets" / "lung_cancer.csv"
OUT  = BASE / "models" / "lung_cancer.sav"

# ── Load ────────────────────────────────────────────────
df = pd.read_csv(DATA)
print(f"Loaded {len(df)} rows, columns: {list(df.columns)}")

# ── Encode GENDER M/F → 1/0 ─────────────────────────────
df["GENDER"] = df["GENDER"].map({"M": 1, "F": 0})

# ── Rename columns to match predictors.py schema ────────
df = df.rename(columns={
    "CHRONICDISEASE":     "CHRONIC_DISEASE",
    "ALCOHOLCONSUMING":   "ALCOHOL",
    "SHORTNESSOFBREATH":  "SHORTNESS_OF_BREATH",
    "SWALLOWINGDIFFICULTY": "SWALLOWING_DIFFICULTY",
    "CHESTPAIN":          "CHEST_PAIN",
})

# ── Target ──────────────────────────────────────────────
df["LUNG_CANCER"] = df["LUNG_CANCER"].map({"YES": 1, "NO": 0})

FEATURES = [
    "GENDER", "AGE", "SMOKING", "YELLOW_FINGERS", "ANXIETY",
    "PEER_PRESSURE", "CHRONIC_DISEASE", "FATIGUE", "ALLERGY",
    "WHEEZING", "ALCOHOL", "COUGHING", "SHORTNESS_OF_BREATH",
    "SWALLOWING_DIFFICULTY", "CHEST_PAIN"
]

X = df[FEATURES]
y = df["LUNG_CANCER"]

# ── Train ────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = RandomForestClassifier(
    n_estimators=100,
    class_weight="balanced",   # handles 270 YES vs 39 NO imbalance
    random_state=42
)
model.fit(X_train, y_train)

acc = accuracy_score(y_test, model.predict(X_test))
print(f"✅ Accuracy: {acc*100:.1f}%")

# ── Save ─────────────────────────────────────────────────
with open(OUT, "wb") as f:
    pickle.dump(model, f)
print(f"✅ Model saved to {OUT}")