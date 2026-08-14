"""VITALS & MDPS Unified Server.

Launches the FastAPI backend on port 8000 serving:
- /api/diseases, /api/predict/{slug}, /api/extract, /api/chat, /api/health
- / (landing.html), /app.html, /report.html, /care.html, /fonts, /img

Usage:
    python serve.py [port]
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "api"))

import uvicorn
from app.main import app

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"==================================================")
    print(f"  VITALS & MDPS Unified Server running on:")
    print(f"  http://localhost:{port}/           (Landing page)")
    print(f"  http://localhost:{port}/app.html   (Screening tool)")
    print(f"  http://localhost:{port}/report.html(Report analysis)")
    print(f"  http://localhost:{port}/care.html  (Find care)")
    print(f"  http://localhost:{port}/api/docs   (Interactive API docs)")
    print(f"==================================================")
    uvicorn.run(app, host="0.0.0.0", port=port)
