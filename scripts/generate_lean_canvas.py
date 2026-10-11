"""Script to generate a pixel-perfect, single-page Lean Canvas PDF for SkillGap."""

import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

def create_lean_canvas():
    output_path = r"C:\Users\Nikhil\Desktop\SkillGap_Lean_Canvas.pdf"
    
    # A4 Landscape: 841.89 x 595.28 pt
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        leftMargin=18,
        rightMargin=18,
        topMargin=12,
        bottomMargin=12,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CanvasTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=15,
        textColor=colors.HexColor("#0F172A"),
    )
    
    meta_style = ParagraphStyle(
        "CanvasMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#475569"),
        alignment=2,
    )

    box_title_style = ParagraphStyle(
        "BoxTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0F172A"),
    )

    box_subtitle_style = ParagraphStyle(
        "BoxSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=6.5,
        leading=8.5,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=3,
    )

    box_bullet_style = ParagraphStyle(
        "BoxBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.5,
        leading=8.6,
        textColor=colors.HexColor("#1E293B"),
        leftIndent=4,
        spaceAfter=2,
    )

    num_badge_style = ParagraphStyle(
        "NumBadge",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=16,
        textColor=colors.HexColor("#3B82F6"),  # Crisp modern blue
        alignment=2,
    )

    def header_cell(title, subtitle, num):
        t_data = [
            [
                Paragraph(f"<b>{title}</b>", box_title_style),
                Paragraph(f"<b>{num}</b>", num_badge_style)
            ],
            [
                Paragraph(subtitle, box_subtitle_style),
                Paragraph("", box_subtitle_style)
            ]
        ]
        t = Table(t_data, colWidths=[120, 28])
        t.setStyle(TableStyle([
            ('SPAN', (0, 1), (1, 1)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        return t

    story = []

    # Canvas Header Bar
    header_data = [
        [
            Paragraph("<b>SKILLGAP - LEAN CANVAS</b>", title_style),
            Paragraph("<b>AICTE Student Internship Project</b> | Author: Nikhil<br/><b>Live App:</b> https://skill-gap-ai-woad.vercel.app", meta_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[400, 405])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 3))

    # Column Width: 805 pt total width / 5 = 161 pt
    col_w = 161.0

    # 1. PROBLEM (1)
    p_content = [
        header_cell("PROBLEM", "Top 3 problems", "1"),
        Paragraph("<b>1. Curriculum-Industry Latency:</b> Engineering syllabi lag 2-4 years behind current technical hiring standards.", box_bullet_style),
        Paragraph("<b>2. Brittle ATS Screening:</b> Exact keyword matchers reject qualified candidates who use equivalent phrasing.", box_bullet_style),
        Paragraph("<b>3. Black-Box AI Hallucinations:</b> Generic LLMs generate ungrounded advice and fabricated match percentages.", box_bullet_style),
        Spacer(1, 3),
        Paragraph("<b>Existing Alternatives:</b>", box_title_style),
        Paragraph("• Generic commercial ATS checkers<br/>• Expensive career coaching<br/>• Unverified ChatGPT prompts", box_bullet_style),
    ]

    # 4. SOLUTION (4)
    sol_content = [
        header_cell("SOLUTION", "Top 3 features", "4"),
        Paragraph("<b>1. Two-Stage Extraction:</b> Fast spaCy PhraseMatcher + SBERT dense vector fallback.", box_bullet_style),
        Paragraph("<b>2. Explainable Scoring:</b> Transparent weighted match separating critical from secondary skills.", box_bullet_style),
        Paragraph("<b>3. What-If Simulator:</b> Instant score recalculation for prospective skills with direct course links.", box_bullet_style),
    ]

    # 8. KEY METRICS (8)
    met_content = [
        header_cell("KEY METRICS", "Key activities you measure", "8"),
        Paragraph("• Daily/Monthly active resume analyses.", box_bullet_style),
        Paragraph("• Gap closure rate (re-test score delta).", box_bullet_style),
        Paragraph("• Sub-second API latency (&lt; 1.5s total).", box_bullet_style),
        Paragraph("• Automated test suite pass rate (77/77).", box_bullet_style),
    ]

    # 3. UNIQUE VALUE PROPOSITION (3)
    uvp_content = [
        header_cell("UNIQUE VALUE PROP.", "Single, clear, compelling message", "3"),
        Paragraph("<b>The first 100% explainable, deterministic skill gap analyzer grounded in empirical market demand - not keyword counting or AI hallucinations.</b>", box_bullet_style),
        Spacer(1, 4),
        Paragraph("<b>High-Level Concept:</b>", box_title_style),
        Paragraph("An instant 'MRI scan' of your resume against real tech roles with a mathematically verified roadmap to placement readiness.", box_bullet_style),
        Spacer(1, 4),
        Paragraph("<b>Privacy Guarantee:</b>", box_title_style),
        Paragraph("Zero-PII retention. Resumes analyzed purely in volatile RAM and immediately discarded.", box_bullet_style),
    ]

    # 5. UNFAIR ADVANTAGE (5)
    adv_content = [
        header_cell("UNFAIR ADVANTAGE", "Can't be easily copied or bought", "5"),
        Paragraph("• Curated 439-skill taxonomy mapped directly to real labor market demand profiles across 17 canonical roles.", box_bullet_style),
        Paragraph("• Strict Zero-PII privacy guarantee with no user resume storage.", box_bullet_style),
        Paragraph("• Ultra-lightweight &lt;150MB CPU runtime requiring zero expensive GPU infrastructure.", box_bullet_style),
    ]

    # 9. CHANNELS (9)
    chan_content = [
        header_cell("CHANNELS", "Path to customers", "9"),
        Paragraph("• <b>Colleges & TPOs:</b> Campus placement pre-training drives.", box_bullet_style),
        Paragraph("• <b>Student Communities:</b> Open-source GitHub repo, hackathons, developer clubs.", box_bullet_style),
        Paragraph("• <b>AICTE & Portals:</b> Standardized student readiness benchmark.", box_bullet_style),
        Paragraph("• <b>Direct Web:</b> Free public edge deployment on Vercel.", box_bullet_style),
    ]

    # 2. CUSTOMER SEGMENTS (2)
    cust_content = [
        header_cell("CUSTOMER SEGMENTS", "Target customers", "2"),
        Paragraph("• <b>Engineering & STEM Students:</b> Preparing for campus placements and internships.", box_bullet_style),
        Paragraph("• <b>Early Career Developers:</b> Planning lateral role transitions (e.g. QA to Backend).", box_bullet_style),
        Paragraph("• <b>Training & Placement Officers:</b> Auditing department-wide curriculum gaps.", box_bullet_style),
        Spacer(1, 3),
        Paragraph("<b>Early Adopters:</b>", box_title_style),
        Paragraph("Tier-2 / Tier-3 engineering colleges needing structured, automated placement prep.", box_bullet_style),
    ]

    # Nested sub-tables for Col 2 and Col 4
    # Available height in top row: 300 pt
    # Upper boxes: 150 pt, Lower boxes: 150 pt
    col2_table = Table([[sol_content], [met_content]], colWidths=[col_w], rowHeights=[150, 150])
    col2_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#0F172A")),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor("#0F172A")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))

    col4_table = Table([[adv_content], [chan_content]], colWidths=[col_w], rowHeights=[150, 150])
    col4_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#0F172A")),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor("#0F172A")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))

    top_grid = [
        [p_content, col2_table, uvp_content, col4_table, cust_content]
    ]

    top_table = Table(top_grid, colWidths=[col_w, col_w, col_w, col_w, col_w], rowHeights=[300])
    top_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor("#0F172A")),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.HexColor("#0F172A")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (1, 0), (1, 0), 0),
        ('BOTTOMPADDING', (1, 0), (1, 0), 0),
        ('LEFTPADDING', (1, 0), (1, 0), 0),
        ('RIGHTPADDING', (1, 0), (1, 0), 0),
        ('TOPPADDING', (3, 0), (3, 0), 0),
        ('BOTTOMPADDING', (3, 0), (3, 0), 0),
        ('LEFTPADDING', (3, 0), (3, 0), 0),
        ('RIGHTPADDING', (3, 0), (3, 0), 0),
    ]))
    story.append(top_table)

    # --- BOTTOM ROW (2 Columns) ---
    # Width: 805 / 2 = 402.5 pt
    bot_w = 402.5

    # 7. COST STRUCTURE (7)
    cost_content = [
        header_cell("COST STRUCTURE", "Customer Acquisition Costs, Hosting, Distribution, People", "7"),
        Paragraph("• <b>Cloud Hosting & Compute:</b> Containerized FastAPI on Render (free tier / $7 micro) + Vercel Edge ($0).", box_bullet_style),
        Paragraph("• <b>Zero LLM API Toll:</b> Pure deterministic NLP + local embeddings eliminates ongoing per-query API costs.", box_bullet_style),
        Paragraph("• <b>Maintenance & Curation:</b> Periodic web-scraping to refresh role profiles, skill taxonomies, and course links.", box_bullet_style),
        Paragraph("• <b>Marketing / Acquisition:</b> Low-cost student-led word of mouth, campus ambassador programs, and GitHub open-source visibility.", box_bullet_style),
    ]

    # 6. REVENUE STREAMS (6)
    rev_content = [
        header_cell("REVENUE STREAMS", "Revenue Model, Lifetime Value, Revenue, Gross Margin", "6"),
        Paragraph("• <b>Freemium B2C:</b> Free individual resume analysis and gap roadmaps for all university students.", box_bullet_style),
        Paragraph("• <b>Institutional B2B SaaS:</b> Annual college subscriptions for batch analytics, placement readiness dashboards, and curriculum gap audits.", box_bullet_style),
        Paragraph("• <b>Affiliate Learning Partners:</b> Referral commissions from certified course providers (Coursera, Udemy, edX).", box_bullet_style),
        Paragraph("• <b>High Gross Margins (~92%+):</b> Ultra-efficient CPU architecture with negligible marginal cost per analysis.", box_bullet_style),
    ]

    bot_grid = [
        [cost_content, rev_content]
    ]

    bot_table = Table(bot_grid, colWidths=[bot_w, bot_w], rowHeights=[195])
    bot_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor("#0F172A")),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.HexColor("#0F172A")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(bot_table)

    doc.build(story)
    print(f"Lean Canvas successfully generated at: {output_path}")

if __name__ == "__main__":
    create_lean_canvas()
