"""Script to generate a structured 2-page Project Concept Note PDF for SkillGap without headers or footers."""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

def create_concept_note():
    output_path = r"C:\Users\Nikhil\Desktop\SkillGap_Concept_Note.pdf"
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Colors
    primary_color = colors.HexColor("#0F2942")     # Deep Navy
    secondary_color = colors.HexColor("#1E5F74")   # Slate Teal
    dark_neutral = colors.HexColor("#1E293B")
    muted_neutral = colors.HexColor("#475569")
    bg_light = colors.HexColor("#F8FAFC")
    border_color = colors.HexColor("#CBD5E1")

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=primary_color,
        spaceAfter=3,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=secondary_color,
        spaceAfter=12,
    )

    meta_style = ParagraphStyle(
        "DocMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=muted_neutral,
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=primary_color,
        spaceBefore=8,
        spaceAfter=3,
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.2,
        textColor=dark_neutral,
        spaceAfter=4,
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.2,
        leading=11.6,
        textColor=dark_neutral,
        leftIndent=10,
        spaceAfter=2.5,
    )

    callout_style = ParagraphStyle(
        "Callout_Text",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#1E3A8A"),
    )

    th_style = ParagraphStyle(
        "THStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
        textColor=colors.white,
    )

    td_style = ParagraphStyle(
        "TDStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.2,
        leading=9.5,
        textColor=dark_neutral,
    )

    story = []

    # ================= PAGE 1 =================
    story.append(Paragraph("SkillGap: Explainable Job-Skill Gap Analyzer & Upskilling Engine", title_style))
    story.append(Paragraph("A Grounded, Deterministic AI System Aligning Engineering Graduates with Market Realities", subtitle_style))
    
    # Metadata Table
    meta_data = [
        [
            Paragraph("<b>Author:</b> Nikhil (AICTE Internship Project)", meta_style),
            Paragraph("<b>Domain:</b> Machine Learning & Natural Language Processing", meta_style),
        ],
        [
            Paragraph("<b>Stack:</b> FastAPI, spaCy, Sentence-Transformers, Next.js", meta_style),
            Paragraph("<b>Live URL:</b> https://skill-gap-ai-woad.vercel.app", meta_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[270, 262])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_light),
        ('BOX', (0, 0), (-1, -1), 0.5, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 6))

    # 1. Executive Summary
    story.append(Paragraph("1. Executive Summary", h1_style))
    story.append(Paragraph(
        "Higher education institutions face an acute <b>employability gap</b>: while thousands of engineering students graduate each year, tech industry recruiters face continuous shortages in production-ready competencies. Traditional recruitment platforms rely on brittle keyword search (penalizing candidates with synonym phrasing) or opaque generative Large Language Models (LLMs) prone to hallucinating scores and prerequisites. <b>SkillGap</b> is a deterministic, explainable AI platform designed to analyze resumes against empirical labor market demand profiles across 17+ canonical technical roles, providing candidates with mathematically verifiable match scores, gap breakdowns, interactive 'What-If' simulations, and grounded course roadmaps.",
        body_style
    ))

    # 2. Problem Statement
    story.append(Paragraph("2. Problem Statement & Industry Friction", h1_style))
    story.append(Paragraph("• <b>Curriculum-Industry Latency:</b> University syllabi update in multi-year cycles, whereas software industry standards shift in months (e.g., containerization, cloud-native architectures, vector databases).", bullet_style))
    story.append(Paragraph("• <b>Brittle ATS Filtering:</b> Commercial Applicant Tracking Systems (ATS) discard qualified candidates due to exact-keyword mismatch without explaining what is missing.", bullet_style))
    story.append(Paragraph("• <b>Generative AI Hallucinations:</b> Asking general-purpose chatbots for resume critique results in unverified advice with arbitrary match percentages detached from real hiring data.", bullet_style))
    story.append(Paragraph("• <b>Data Privacy Concerns:</b> Commercial platforms frequently harvest user resumes and PII for recruitment databases or third-party marketing.", bullet_style))

    # 3. Technical Approach & Innovation
    story.append(Paragraph("3. Technical Approach & Innovation", h1_style))
    story.append(Paragraph(
        "SkillGap eliminates guesswork through an empirical, four-pillar architecture built strictly on open science principles:",
        body_style
    ))
    story.append(Paragraph("• <b>Hybrid Two-Stage Skill Extraction:</b> Stage A uses spaCy's <code>PhraseMatcher</code> over an expertly curated 439-skill taxonomy for sub-millisecond deterministic extraction. Stage B uses <code>all-MiniLM-L6-v2</code> dense vector embeddings (cosine threshold 0.75) to extract emerging tech and variant phrasing.", bullet_style))
    story.append(Paragraph("• <b>Empirical Market Profiles:</b> Role requirements are not fabricated; they are derived from real job posting datasets, separating critical must-haves (e.g., Python, SQL for Backend) from secondary nice-to-haves (e.g., Redis, Kafka).", bullet_style))
    story.append(Paragraph("• <b>Transparent Mathematical Scoring:</b> Scores represent the exact weighted intersection of verified critical skills and secondary skills. Zero black-box bias.", bullet_style))
    story.append(Paragraph("• <b>Interactive 'What-If' Simulator:</b> A dynamic modeling interface that recalculates match scores instantly when a candidate plans to acquire prospective skills.", bullet_style))
    story.append(Paragraph("• <b>Multi-Role Competency Comparison:</b> Evaluates candidate skills simultaneously across 17 canonical roles to identify natural adjacent career paths.", bullet_style))

    # Callout Box
    callout_data = [[Paragraph("<b>Core Differentiator:</b> SkillGap guarantees 100% explainability. If a candidate receives a 68% match score, the system explicitly lists the exact critical and secondary skills missing, why they matter to recruiters, and which courses bridge the gap.", callout_style)]]
    callout_table = Table(callout_data, colWidths=[532])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#93C5FD")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(Spacer(1, 4))
    story.append(callout_table)

    # ================= PAGE 2 =================
    story.append(PageBreak())

    # 4. Feature Comparison Table
    story.append(Paragraph("4. Architectural Comparison: SkillGap vs Alternatives", h1_style))
    
    comp_data = [
        [
            Paragraph("<b>Dimension</b>", th_style),
            Paragraph("<b>Traditional ATS</b>", th_style),
            Paragraph("<b>Generic LLMs (ChatGPT)</b>", th_style),
            Paragraph("<b>SkillGap (Our Approach)</b>", th_style),
        ],
        [
            Paragraph("<b>Skill Extraction</b>", td_style),
            Paragraph("Exact string matching only", td_style),
            Paragraph("Unconstrained generative text", td_style),
            Paragraph("Two-stage: spaCy regex + SBERT dense vectors", td_style),
        ],
        [
            Paragraph("<b>Scoring Reliability</b>", td_style),
            Paragraph("Opaque keyword count", td_style),
            Paragraph("Hallucinated / arbitrary %", td_style),
            Paragraph("Deterministic weighted intersection", td_style),
        ],
        [
            Paragraph("<b>Market Grounding</b>", td_style),
            Paragraph("Single job description text", td_style),
            Paragraph("General pre-training web scrape", td_style),
            Paragraph("Empirical labor market demand profiles", td_style),
        ],
        [
            Paragraph("<b>Course Roadmap</b>", td_style),
            Paragraph("None (Pass / Fail only)", td_style),
            Paragraph("Fabricated / broken links", td_style),
            Paragraph("Vector-similarity mapped course index", td_style),
        ],
        [
            Paragraph("<b>What-If Modeling</b>", td_style),
            Paragraph("Not available", td_style),
            Paragraph("Manual re-prompting required", td_style),
            Paragraph("Real-time interactive slider calculation", td_style),
        ],
        [
            Paragraph("<b>Data Privacy</b>", td_style),
            Paragraph("Resumes stored in database", td_style),
            Paragraph("Data used to train public models", td_style),
            Paragraph("Strict Zero-PII volatile memory only", td_style),
        ],
    ]
    comp_table = Table(comp_data, colWidths=[100, 130, 140, 162])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('BOX', (0, 0), (-1, -1), 0.5, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, bg_light]),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 6))

    # 5. System Engineering & Privacy
    story.append(Paragraph("5. System Engineering & Privacy-by-Design", h1_style))
    story.append(Paragraph("• <b>Zero-PII Volatile Processing:</b> Resumes are processed in volatile memory buffers and immediately garbage collected. No user resume or personal contact details are stored in databases or logged to disk.", bullet_style))
    story.append(Paragraph("• <b>Sub-Second Latency:</b> Precomputed offline embeddings (<code>.npy</code>) and CPU thread constraints allow full resume parsing, extraction, and gap analysis in &lt; 1.5 seconds.", bullet_style))
    story.append(Paragraph("• <b>Micro-Container Optimization:</b> Optimized for constrained micro-container environments (&lt; 150MB active RAM footprint), deployed on Render (Docker backend) and Vercel (Next.js frontend).", bullet_style))
    story.append(Paragraph("• <b>Rigorous Automated Verification:</b> Backed by 77 automated integration tests with 100% pass rate covering payload validation, latency limits, and role scoring.", bullet_style))

    # 6. Target Beneficiaries & Impact
    story.append(Paragraph("6. Target Beneficiaries & Educational Impact", h1_style))
    story.append(Paragraph("• <b>Engineering Students & Freshers:</b> Gain objective, actionable insight into employer expectations and targeted learning roadmaps prior to campus placement drives.", bullet_style))
    story.append(Paragraph("• <b>Academic Institutions & Training Cells (TPOs):</b> Can analyze cohort trends to identify department-wide skill gaps and align laboratory training with industry demands.", bullet_style))
    story.append(Paragraph("• <b>Early Career Professionals:</b> Self-diagnose capability gaps when transitioning between adjacent disciplines (e.g. Frontend to Full-Stack).", bullet_style))

    # 7. Future Roadmap
    story.append(Paragraph("7. Future Development Roadmap", h1_style))
    story.append(Paragraph("• <b>AI Resume Builder:</b> Automated drafting module that incorporates verified acquired skills into a clean, recruiter-ready resume.", bullet_style))
    story.append(Paragraph("• <b>University Curriculum Alignment:</b> API integration enabling universities to map course syllabi directly to empirical role skill requirements.", bullet_style))
    story.append(Paragraph("• <b>Localized Edge SLM Inference:</b> Offline quantized Small Language Model (Qwen 2.5) for qualitative bullet-point rewrite suggestions.", bullet_style))

    doc.build(story)
    print(f"Clean Concept Note successfully generated at: {output_path}")

if __name__ == "__main__":
    create_concept_note()
