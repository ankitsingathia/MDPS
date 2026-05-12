"""
Run this script once from your mdps folder to fix Training.csv.
    python fix_training_csv.py
"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).parent
DATA = BASE / "datasets" / "dataset.csv"
OUT  = BASE / "datasets" / "Training.csv"

# ── Load raw dataset ─────────────────────────────────────
df = pd.read_csv(DATA)
print(f"Loaded {len(df)} rows")

# ── Strip whitespace from disease and symptom values ─────
df["Disease"] = df["Disease"].str.strip()
symptom_cols = [c for c in df.columns if c.startswith("Symptom_")]
for col in symptom_cols:
    df[col] = df[col].str.strip()

# ── Collect all unique symptoms ──────────────────────────
all_symptoms = set()
for col in symptom_cols:
    all_symptoms.update(df[col].dropna().unique())
all_symptoms = sorted(all_symptoms)
print(f"Total unique symptoms: {len(all_symptoms)}")

# ── Build one-hot encoded Training.csv ──────────────────
rows = []
for _, row in df.iterrows():
    disease = row["Disease"]
    present = set(row[symptom_cols].dropna().values)
    encoded = {s: 1 if s in present else 0 for s in all_symptoms}
    encoded["prognosis"] = disease
    rows.append(encoded)

training_df = pd.DataFrame(rows)

# Move prognosis to last column
cols = [c for c in training_df.columns if c != "prognosis"] + ["prognosis"]
training_df = training_df[cols]

training_df.to_csv(OUT, index=False)
print(f"✅ Training.csv saved with {len(training_df)} rows and {len(all_symptoms)} symptom columns")
print(f"Sample symptoms: {all_symptoms[:10]}")
print(f"Diseases: {sorted(training_df['prognosis'].unique())}")