"""Script to generate test fixtures (PDF, DOCX, TXT) for testing."""

from pathlib import Path
import docx

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)


def create_docx_fixture():
    doc = docx.Document()
    doc.add_heading("Jane Smith", level=0)
    doc.add_paragraph("Data Scientist | jane.smith@example.com")

    doc.add_heading("Summary", level=1)
    doc.add_paragraph(
        "Experienced Data Scientist with 4+ years of expertise in machine learning, "
        "natural language processing, and data engineering."
    )

    doc.add_heading("Skills", level=1)
    table = doc.add_table(rows=1, cols=2)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Category"
    hdr_cells[1].text = "Skills"

    skills_data = [
        ("Languages", "Python, R, SQL"),
        ("Machine Learning", "scikit-learn, PyTorch, pandas, numpy"),
        ("NLP", "spaCy, transformers, NLTK, BERT"),
        ("Cloud & Tools", "Docker, Git, AWS, MLflow"),
    ]
    for cat, sk in skills_data:
        row_cells = table.add_row().cells
        row_cells[0].text = cat
        row_cells[1].text = sk

    doc.add_heading("Experience", level=1)
    doc.add_paragraph("Data Scientist - AI Innovations (2021-Present)")
    doc.add_paragraph(
        "- Built NLP pipelines for customer feedback sentiment classification.\n"
        "- Trained gradient boosting models with scikit-learn for churn prediction.\n"
        "- Deployed ML models using FastAPI and Docker."
    )

    docx_path = FIXTURES_DIR / "sample_resume.docx"
    doc.save(docx_path)
    print(f"Generated DOCX fixture: {docx_path}")


def create_pdf_fixture():
    # Construct a valid, minimal single-page PDF with text stream readable by pdfplumber/pdfminer
    content = b"""%PDF-1.4
1 0 obj
<<
  /Type /Catalog
  /Pages 2 0 R
>>
endobj
2 0 obj
<<
  /Type /Pages
  /Kids [3 0 R]
  /Count 1
>>
endobj
3 0 obj
<<
  /Type /Page
  /Parent 2 0 R
  /MediaBox [0 0 612 792]
  /Contents 4 0 R
  /Resources <<
    /Font <<
      /F1 <<
        /Type /Font
        /Subtype /Type1
        /BaseFont /Helvetica
      >>
    >>
  >>
>>
endobj
4 0 obj
<<
  /Length 240
>>
stream
BT
/F1 14 Tf
50 720 Td
(Alice Johnson - Machine Learning Engineer) Tj
/F1 11 Tf
0 -30 Td
(Skills: Python, TensorFlow, PyTorch, Docker, Kubernetes, SQL) Tj
0 -25 Td
(Experience: ML Engineer at TechCorp building deep learning models.) Tj
0 -20 Td
(Education: MS Computer Science) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000280 00000 n 
trailer
<<
  /Size 5
  /Root 1 0 R
>>
startxref
570
%%EOF"""
    pdf_path = FIXTURES_DIR / "sample_resume.pdf"
    pdf_path.write_bytes(content)
    print(f"Generated PDF fixture: {pdf_path}")


if __name__ == "__main__":
    create_pdf_fixture()
    try:
        create_docx_fixture()
    except Exception as e:
        print(f"DOCX generation will run once python-docx is ready: {e}")
