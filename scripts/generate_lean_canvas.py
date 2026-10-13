"""Script to generate a clean, human-made single-page Lean Canvas PDF without headers, footers, or number badges."""

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
        leftMargin=20,
        rightMargin=20,
        topMargin=15,
        bottomMargin=15,
    )

    styles = getSampleStyleSheet()

    box_title_style = ParagraphStyle(
        "BoxTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=1,
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
        leading=8.8,
        textColor=colors.HexColor("#1E293B"),
        leftIndent=4,
        spaceAfter=2,
    )

    def header_cell(title, subtitle):
        return [
            Paragraph(f"<b>{title}</b>", box_title_style),
            Paragraph(subtitle, box_subtitle_style),
        ]

    story = []

    # Column Width: 801.89 pt / 5 = 160.37 pt
    col_w = 801.89 / 5.0

    # 1. PROBLEM
    p_content = header_cell("PROBLEM", "Top 3 problems") + [
        Paragraph("• <b>Curriculum-Industry Latency:</b> Engineering syllabi lag 2-4 years behind current technical hiring standards.", box_bullet_style),
        Paragraph("• <b>Brittle ATS Screening:</b> Exact keyword matchers reject qualified candidates who use equivalent phrasing.", box_bullet_style),
        Paragraph("• <b>Black-Box AI Hallucinations:</b> Generic LLMs generate ungrounded advice and fabricated match percentages.", box_bullet_style),
        Spacer(1, 3),
        Paragraph("<b>Existing Alternatives:</b>", box_title_style),
        Paragraph("• Generic commercial ATS checkers<br/>• Expensive career coaching<br/>• Unverified ChatGPT prompts", box_bullet_style),
    ]

    # 4. SOLUTION
    sol_content = header_cell("SOLUTION", "Top 3 features") + [
        Paragraph("• <b>Two-Stage Extraction:</b> Fast spaCy PhraseMatcher + SBERT dense vector fallback.", box_bullet_style),
        Paragraph("• <b>Explainable Scoring:</b> Transparent weighted match separating critical from secondary skills.", box_bullet_style),
        Paragraph("• <b>What-If Simulator:</b> Instant score recalculation for prospective skills with direct course links.", box_bullet_style),
    ]

    # 8. KEY METRICS
    met_content = header_cell("KEY METRICS", "Key activities you measure") + [
        Paragraph("• Daily/Monthly active resume analyses.", box_bullet_style),
        Paragraph("• Gap closure rate (re-test score delta).", box_bullet_style),
        Paragraph("• Sub-second API latency (&lt; 1.5s total).", box_bullet_style),
        Paragraph("• Automated test suite pass rate (77/77).", box_bullet_style),
    ]

    # 3. UNIQUE VALUE PROPOSITION
    uvp_content = header_cell("UNIQUE VALUE PROPOSITION", "Single, clear, compelling message") + [
        Paragraph("<b>The first 100% explainable, deterministic skill gap analyzer grounded in empirical market demand - not keyword counting or AI hallucinations.</b>", box_bullet_style),
        Spacer(1, 4),
        Paragraph("<b>High-Level Concept:</b>", box_title_style),
        Paragraph("An instant 'MRI scan' of your resume against real tech roles with a mathematically verified roadmap to placement readiness.", box_bullet_style),
        Spacer(1, 4),
        Paragraph("<b>Privacy Guarantee:</b>", box_title_style),
        Paragraph("Zero-PII retention. Resumes analyzed purely in volatile RAM and immediately discarded.", box_bullet_style),
    ]

    # 5. UNFAIR ADVANTAGE
    adv_content = header_cell("UNFAIR ADVANTAGE", "Can't be easily copied or bought") + [
        Paragraph("• Curated 439-skill taxonomy mapped directly to real labor market demand profiles across 17 canonical roles.", box_bullet_style),
        Paragraph("• Strict Zero-PII privacy guarantee with no user resume storage.", box_bullet_style),
        Paragraph("• Ultra-lightweight &lt;150MB CPU runtime requiring zero expensive GPU infrastructure.", box_bullet_style),
    ]

    # 9. CHANNELS
    chan_content = header_cell("CHANNELS", "Path to customers") + [
        Paragraph("• <b>Colleges & TPOs:</b> Campus placement pre-training drives.", box_bullet_style),
        Paragraph("• <b>Student Communities:</b> Open-source GitHub repo, hackathons, developer clubs.", box_bullet_style),
        Paragraph("• <b>AICTE & Portals:</b> Standardized student readiness benchmark.", box_bullet_style),
        Paragraph("• <b>Direct Web:</b> Free public edge deployment on Vercel.", box_bullet_style),
    ]

    # 2. CUSTOMER SEGMENTS
    cust_content = header_cell("CUSTOMER SEGMENTS", "Target customers") + [
        Paragraph("• <b>Engineering & STEM Students:</b> Preparing for campus placements and internships.", box_bullet_style),
        Paragraph("• <b>Early Career Developers:</b> Planning lateral role transitions (e.g. QA to Backend).", box_bullet_style),
        Paragraph("• <b>Training & Placement Officers:</b> Auditing department-wide curriculum gaps.", box_bullet_style),
        Spacer(1, 3),
        Paragraph("<b>Early Adopters:</b>", box_title_style),
        Paragraph("Tier-2 / Tier-3 engineering colleges needing structured, automated placement prep.", box_bullet_style),
    ]

    # Nested sub-tables for Col 2 and Col 4
    # Available height in top row: 310 pt
    col2_table = Table([[sol_content], [met_content]], colWidths=[col_w], rowHeights=[155, 155])
    col2_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#0F172A")),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor("#0F172A")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))

    col4_table = Table([[adv_content], [chan_content]], colWidths=[col_w], rowHeights=[155, 155])
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

    top_table = Table(top_grid, colWidths=[col_w, col_w, col_w, col_w, col_w], rowHeights=[310])
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
    bot_w = 801.89 / 2.0

    # 7. COST STRUCTURE
    cost_content = header_cell("COST STRUCTURE", "Customer Acquisition Costs, Hosting, Distribution, People") + [
        Paragraph("• <b>Cloud Hosting & Compute:</b> Containerized FastAPI on Render (free tier / $7 micro) + Vercel Edge ($0).", box_bullet_style),
        Paragraph("• <b>Zero LLM API Toll:</b> Pure deterministic NLP + local embeddings eliminates ongoing per-query API costs.", box_bullet_style),
        Paragraph("• <b>Maintenance & Curation:</b> Periodic web-scraping to refresh role profiles, skill taxonomies, and course links.", box_bullet_style),
        Paragraph("• <b>Marketing / Acquisition:</b> Low-cost student-led word of mouth, campus ambassador programs, and GitHub open-source visibility.", box_bullet_style),
    ]

    # 6. REVENUE STREAMS
    rev_content = header_cell("REVENUE STREAMS", "Revenue Model, Lifetime Value, Revenue, Gross Margin") + [
        Paragraph("• <b>Freemium B2C:</b> Free individual resume analysis and gap roadmaps for all university students.", box_bullet_style),
        Paragraph("• <b>Institutional B2B SaaS:</b> Annual college subscriptions for batch analytics, placement readiness dashboards, and curriculum gap audits.", box_bullet_style),
        Paragraph("• <b>Affiliate Learning Partners:</b> Referral commissions from certified course providers (Coursera, Udemy, edX).", box_bullet_style),
        Paragraph("• <b>High Gross Margins (~92%+):</b> Ultra-efficient CPU architecture with negligible marginal cost per analysis.", box_bullet_style),
    ]

    bot_grid = [
        [cost_content, rev_content]
    ]

    bot_table = Table(bot_grid, colWidths=[bot_w, bot_w], rowHeights=[200])
    bot_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor("#0F172A")),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.HexColor("#0F172A")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(bot_table)

    doc.build(story)
    print(f"Clean Lean Canvas successfully generated at: {output_path}")

if __name__ == "__main__":
    create_lean_canvas()
