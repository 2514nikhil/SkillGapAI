"""Check runner script for Phase 12B.

Renders both fixture resumes into all 3 templates (classic, compact, technical)
as PDF, reports page counts, outputs lint results, and prints extracted text
from one rendered PDF to demonstrate ATS readability.
"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import pdfplumber

from ml.resume_lint import lint
from ml.resume_render import render_pdf

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
R1_PATH = FIXTURES_DIR / "resume_example_1.json"
R2_PATH = FIXTURES_DIR / "resume_example_2.json"

TEMPLATES = ["classic", "compact", "technical"]


def main():
    print("=" * 70)
    print("SKILLGAP PHASE 12B: DETERMINISTIC RESUME ENGINE VERIFICATION")
    print("=" * 70)

    # 1. Load Fixtures
    with open(R1_PATH, "r", encoding="utf-8") as f:
        r1 = json.load(f)
    with open(R2_PATH, "r", encoding="utf-8") as f:
        r2 = json.load(f)

    # 2. Lint Reports
    print("\n--- LINT RESULTS ---")
    for name, data in [("Fixture 1 (Backend Engineer - Nikhil)", r1), ("Fixture 2 (Frontend/Fullstack - Priya)", r2)]:
        issues = lint(data)
        errors = [i for i in issues if i["level"] == "error"]
        warnings = [i for i in issues if i["level"] == "warning"]
        tips = [i for i in issues if i["level"] == "tip"]
        print(f"\n{name}:")
        print(f"  Total findings: {len(issues)} (Errors: {len(errors)}, Warnings: {len(warnings)}, Tips: {len(tips)})")
        for i in issues:
            print(f"    [{i['level'].upper()}] ({i['section']}) {i['message']} (at {i['path']})")

    # 3. PDF Rendering to Temp Directory
    out_dir = Path(tempfile.gettempdir()) / "skillgap_phase12b_pdfs"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n--- PDF RENDERING (Destination: {out_dir}) ---")

    render_outputs = []
    for res_name, res_data in [("resume_1", r1), ("resume_2", r2)]:
        for tmpl in TEMPLATES:
            pdf_bytes = render_pdf(res_data, template_name=tmpl, page_size="A4")
            filename = f"{res_name}_{tmpl}.pdf"
            file_path = out_dir / filename
            file_path.write_bytes(pdf_bytes)

            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                page_count = len(pdf.pages)

            render_outputs.append((filename, len(pdf_bytes), page_count, file_path))
            print(f"  {filename:<24} | Size: {len(pdf_bytes):>6} bytes | Pages: {page_count}")

    # 4. Print extracted text from one rendered PDF (e.g. resume_1_classic.pdf)
    sample_pdf_path = render_outputs[0][3]
    print(f"\n--- ATS READABILITY: PDFPLUMBER TEXT EXTRACTION ({render_outputs[0][0]}) ---")
    print("-" * 70)
    with pdfplumber.open(sample_pdf_path) as pdf:
        for idx, page in enumerate(pdf.pages):
            print(f"--- PAGE {idx + 1} ---")
            print(page.extract_text())
    print("-" * 70)
    print("\nPhase 12B checks completed successfully.")


if __name__ == "__main__":
    main()
