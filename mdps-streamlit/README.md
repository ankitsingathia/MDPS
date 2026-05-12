# Multiple Disease Prediction System (MDPS)

AI-powered healthcare web app built with **Python + Streamlit**.

## Features
- 🔐 User signup/login (SQLite + bcrypt)
- 🧪 9 numerical disease modules: Diabetes, Heart, Parkinson's, Liver, Hepatitis, Lung Cancer, CKD, Breast Cancer, Jaundice
- 🤒 Symptom-based prediction (Decision Tree, auto-trained from `Training.csv`)
- 🔍 Explainable AI (rule-based highlights of risk-driving inputs)
- 📁 Personal report history (SQLite `reports` table)
- 📄 Professional PDF reports (fpdf2)
- 📊 Plotly analytics dashboard
- 🚨 Doctor / emergency recommendations
- 🌐 Multi-language scaffold, dark/light theme, search

## Project structure
```
Frontend/
├── app.py              # Streamlit entry point
├── auth.py             # SQLite + bcrypt auth & report storage
├── data.db             # auto-created on first run
├── requirements.txt
├── code/
│   ├── DiseaseModel.py # Symptom-based model loader/trainer
│   ├── predictors.py   # Numerical model wrappers + UI schemas
│   └── helper.py       # PDF generation + explainability
├── models/             # Drop your .sav / .joblib files here
├── datasets/           # Training.csv, symptom_severity.csv, ...
├── images/
└── reports/            # (used by app at runtime)
```

## Setup
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Adding ML models
Place pre-trained model files in `models/` using these filenames:

| Module                 | Filename                  |
|------------------------|---------------------------|
| Diabetes               | `diabetes.joblib`         |
| Heart Disease          | `heart.joblib`            |
| Parkinson's            | `parkinsons.joblib`       |
| Liver Disease          | `liver.joblib`            |
| Hepatitis              | `hepatitis.joblib`        |
| Lung Cancer            | `lung_cancer.joblib`      |
| Chronic Kidney Disease | `kidney.joblib`           |
| Breast Cancer          | `breast_cancer.joblib`    |
| Jaundice               | `jaundice.joblib`         |

`.sav` and `.pkl` extensions are also auto-detected. Field order in `code/predictors.py` must match the model's training feature order.

## Symptom-based datasets
Place these in `datasets/`:
- `Training.csv` — symptom columns + `prognosis` target
- `symptom_severity.csv` — symptom, weight
- `disease_description.csv` — disease, description
- `disease_precaution.csv` — disease, p1, p2, p3, p4

The Decision Tree is auto-trained on first launch and cached to `models/symptom_dt.joblib`.

## Deployment
- **Streamlit Community Cloud**: push to GitHub, point to `app.py`.
- **Render / Railway**: start command `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`.
- **Heroku**: add a `Procfile` with the same command.

## Disclaimer
For educational/research use only. Not a substitute for professional medical advice.
