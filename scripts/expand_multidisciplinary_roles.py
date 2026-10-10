"""Expand SkillGap from CSE-only to Multi-Disciplinary Industry Roles.

Uses the real Kaggle Resume Dataset at C:\\Users\\Nikhil\\Downloads\\resumedataset\\Resume\\Resume.csv
to build empirical role profiles, expand taxonomy with non-CSE domain skills,
and update course recommendations for:
- Accountant
- Financial Analyst
- HR Specialist
- Sales Representative
- Business Development Manager
- Digital Marketer
- UI/UX & Graphic Designer
- Healthcare Specialist
- Management Consultant
- Mechanical/Civil Engineer
- Teacher & Educator
- Legal Associate / Advocate
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import settings
from ml.extract import extract_skills
from ml.taxonomy import taxonomy

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

USER_RESUME_CSV = Path(r"C:\Users\Nikhil\Downloads\resumedataset\Resume\Resume.csv")

# 1. New Non-CSE Canonical Skills
NEW_SKILLS: Dict[str, Dict[str, Any]] = {
    # Finance & Accounting
    "accounting": {
        "name": "Accounting",
        "category": "finance",
        "aliases": ["financial accounting", "accountancy", "bookkeeping"],
        "ambiguous": False,
    },
    "financial_analysis": {
        "name": "Financial Analysis",
        "category": "finance",
        "aliases": ["financial statement analysis", "ratio analysis", "financial metrics"],
        "ambiguous": False,
    },
    "budgeting": {
        "name": "Budgeting",
        "category": "finance",
        "aliases": ["budget management", "budget forecasting", "variance analysis"],
        "ambiguous": False,
    },
    "tax_preparation": {
        "name": "Tax Preparation",
        "category": "finance",
        "aliases": ["tax compliance", "taxation", "tax filings", "corporate tax", "income tax"],
        "ambiguous": False,
    },
    "auditing": {
        "name": "Auditing",
        "category": "finance",
        "aliases": ["internal audit", "financial audit", "audit compliance"],
        "ambiguous": False,
    },
    "financial_reporting": {
        "name": "Financial Reporting",
        "category": "finance",
        "aliases": ["financial statements", "gaap reporting", "monthly financial reports"],
        "ambiguous": False,
    },
    "general_ledger": {
        "name": "General Ledger",
        "category": "finance",
        "aliases": ["general ledger", "journal entries", "chart of accounts"],
        "ambiguous": False,
    },
    "accounts_payable": {
        "name": "Accounts Payable",
        "category": "finance",
        "aliases": ["accounts payable", "vendor invoices", "invoice processing"],
        "ambiguous": False,
    },
    "accounts_receivable": {
        "name": "Accounts Receivable",
        "category": "finance",
        "aliases": ["accounts receivable", "client billing", "collections"],
        "ambiguous": False,
    },
    "quickbooks": {
        "name": "QuickBooks",
        "category": "finance",
        "aliases": ["quickbooks online", "quickbooks pro", "intuit quickbooks"],
        "ambiguous": False,
    },
    "payroll": {
        "name": "Payroll Processing",
        "category": "finance",
        "aliases": ["payroll administration", "payroll", "wage processing"],
        "ambiguous": False,
    },
    "gaap": {
        "name": "GAAP",
        "category": "finance",
        "aliases": ["generally accepted accounting principles", "us gaap", "ifrs"],
        "ambiguous": False,
    },
    "reconciliation": {
        "name": "Account Reconciliation",
        "category": "finance",
        "aliases": ["bank reconciliation", "balance sheet reconciliation"],
        "ambiguous": False,
    },
    "wealth_management": {
        "name": "Wealth Management",
        "category": "finance",
        "aliases": ["portfolio management", "investment management", "asset management"],
        "ambiguous": False,
    },

    # Human Resources
    "talent_acquisition": {
        "name": "Talent Acquisition",
        "category": "business",
        "aliases": ["recruitment", "recruiting", "sourcing candidates", "full cycle recruiting"],
        "ambiguous": False,
    },
    "onboarding": {
        "name": "Employee Onboarding",
        "category": "business",
        "aliases": ["new hire onboarding", "employee induction", "onboarding program"],
        "ambiguous": False,
    },
    "employee_relations": {
        "name": "Employee Relations",
        "category": "business",
        "aliases": ["workplace relations", "labor relations", "employee engagement"],
        "ambiguous": False,
    },
    "performance_management": {
        "name": "Performance Management",
        "category": "business",
        "aliases": ["performance appraisals", "annual reviews", "performance evaluations"],
        "ambiguous": False,
    },
    "hris": {
        "name": "HRIS",
        "category": "business",
        "aliases": ["human resources information system", "workday", "adp workforce", "bamboohr"],
        "ambiguous": False,
    },
    "benefits_administration": {
        "name": "Benefits Administration",
        "category": "business",
        "aliases": ["employee benefits", "compensation and benefits", "health insurance plans"],
        "ambiguous": False,
    },
    "labor_law": {
        "name": "Labor Law Compliance",
        "category": "business",
        "aliases": ["employment law", "eeoc compliance", "flsa compliance"],
        "ambiguous": False,
    },
    "workforce_planning": {
        "name": "Workforce Planning",
        "category": "business",
        "aliases": ["headcount planning", "staffing strategies", "succession planning"],
        "ambiguous": False,
    },

    # Sales & Marketing
    "lead_generation": {
        "name": "Lead Generation",
        "category": "business",
        "aliases": ["prospecting", "lead prospecting", "outbound leads"],
        "ambiguous": False,
    },
    "cold_calling": {
        "name": "Cold Calling",
        "category": "business",
        "aliases": ["cold outreach", "phone prospecting", "telemarketing"],
        "ambiguous": False,
    },
    "pipeline_management": {
        "name": "Pipeline Management",
        "category": "business",
        "aliases": ["sales pipeline", "deal pipeline", "sales funnel"],
        "ambiguous": False,
    },
    "b2b_sales": {
        "name": "B2B Sales",
        "category": "business",
        "aliases": ["business to business sales", "enterprise sales", "corporate sales"],
        "ambiguous": False,
    },
    "account_management": {
        "name": "Account Management",
        "category": "business",
        "aliases": ["key account management", "client relationship management", "client retention"],
        "ambiguous": False,
    },
    "social_media_marketing": {
        "name": "Social Media Marketing",
        "category": "business",
        "aliases": ["social media management", "smm", "instagram marketing", "linkedin marketing"],
        "ambiguous": False,
    },
    "google_analytics": {
        "name": "Google Analytics",
        "category": "data",
        "aliases": ["ga4", "google analytics 4", "web analytics"],
        "ambiguous": False,
    },
    "email_marketing": {
        "name": "Email Marketing",
        "category": "business",
        "aliases": ["email campaigns", "mailchimp", "newsletter campaigns"],
        "ambiguous": False,
    },
    "copywriting": {
        "name": "Copywriting",
        "category": "business",
        "aliases": ["content writing", "ad copywriting", "creative writing"],
        "ambiguous": False,
    },
    "ppc_advertising": {
        "name": "PPC Advertising",
        "category": "business",
        "aliases": ["google ads", "pay per click", "paid search ads"],
        "ambiguous": False,
    },

    # Healthcare
    "patient_care": {
        "name": "Patient Care",
        "category": "healthcare",
        "aliases": ["direct patient care", "clinical care", "bedside care"],
        "ambiguous": False,
    },
    "clinical_documentation": {
        "name": "Clinical Documentation",
        "category": "healthcare",
        "aliases": ["medical records", "patient charting", "clinical notes"],
        "ambiguous": False,
    },
    "electronic_health_records": {
        "name": "Electronic Health Records",
        "category": "healthcare",
        "aliases": ["ehr", "emr", "epic systems", "cerner"],
        "ambiguous": False,
    },
    "vital_signs": {
        "name": "Vital Signs Monitoring",
        "category": "healthcare",
        "aliases": ["taking vitals", "blood pressure monitoring", "vital signs"],
        "ambiguous": False,
    },
    "hipaa_compliance": {
        "name": "HIPAA Compliance",
        "category": "healthcare",
        "aliases": ["hipaa regulations", "patient privacy", "hipaa"],
        "ambiguous": False,
    },
    "medical_terminology": {
        "name": "Medical Terminology",
        "category": "healthcare",
        "aliases": ["medical coding terms", "icd-10", "cpt coding"],
        "ambiguous": False,
    },
    "cpr": {
        "name": "CPR & First Aid",
        "category": "healthcare",
        "aliases": ["bls certification", "cardiopulmonary resuscitation", "basic life support"],
        "ambiguous": False,
    },

    # Engineering & Technical
    "autocad": {
        "name": "AutoCAD",
        "category": "tools",
        "aliases": ["autodesk autocad", "2d cad drafting", "computer-aided drafting"],
        "ambiguous": False,
    },
    "solidworks": {
        "name": "SolidWorks",
        "category": "tools",
        "aliases": ["solidworks 3d", "3d mechanical modeling"],
        "ambiguous": False,
    },
    "matlab": {
        "name": "MATLAB",
        "category": "tools",
        "aliases": ["matlab simulink", "matlab programming"],
        "ambiguous": False,
    },
    "quality_control": {
        "name": "Quality Control",
        "category": "tools",
        "aliases": ["qa qc", "quality inspection", "quality management systems"],
        "ambiguous": False,
    },
    "safety_compliance": {
        "name": "Safety Compliance",
        "category": "tools",
        "aliases": ["osha standards", "occupational safety", "workplace safety"],
        "ambiguous": False,
    },

    # Education & Teaching
    "curriculum_development": {
        "name": "Curriculum Development",
        "category": "business",
        "aliases": ["curriculum design", "instructional design", "syllabus development"],
        "ambiguous": False,
    },
    "classroom_management": {
        "name": "Classroom Management",
        "category": "soft skills",
        "aliases": ["student behavior management", "classroom instruction"],
        "ambiguous": False,
    },
    "lesson_planning": {
        "name": "Lesson Planning",
        "category": "business",
        "aliases": ["lesson plans", "instructional planning"],
        "ambiguous": False,
    },
    "student_assessment": {
        "name": "Student Assessment",
        "category": "business",
        "aliases": ["grading rubrics", "evaluating student performance", "educational testing"],
        "ambiguous": False,
    },

    # Legal
    "legal_research": {
        "name": "Legal Research",
        "category": "business",
        "aliases": ["case law research", "westlaw", "lexisnexis"],
        "ambiguous": False,
    },
    "contract_drafting": {
        "name": "Contract Drafting",
        "category": "business",
        "aliases": ["contract review", "drafting agreements", "commercial contracts"],
        "ambiguous": False,
    },
    "litigation": {
        "name": "Litigation Support",
        "category": "business",
        "aliases": ["trial preparation", "pleadings drafting", "court filings"],
        "ambiguous": False,
    },
    "regulatory_compliance": {
        "name": "Regulatory Compliance",
        "category": "business",
        "aliases": ["statutory compliance", "regulatory oversight", "compliance audits"],
        "ambiguous": False,
    },
}

# 2. Category mapping from Kaggle Resume.csv to our Target Roles
TARGET_ROLE_CONFIG = {
    "Accountant": {
        "categories": ["ACCOUNTANT"],
        "default_title": "Certified Public Accountant / Staff Accountant",
        "signature_skills": ["accounting", "financial_reporting", "general_ledger", "tax_preparation", "quickbooks", "gaap", "payroll", "reconciliation"],
    },
    "Financial Analyst": {
        "categories": ["FINANCE", "BANKING"],
        "default_title": "Senior Financial Analyst / Investment Analyst",
        "signature_skills": ["financial_analysis", "financial_modeling", "budgeting", "financial_reporting", "wealth_management", "accounting", "risk_management"],
    },
    "HR Specialist": {
        "categories": ["HR"],
        "default_title": "Human Resources Specialist / HR Business Partner",
        "signature_skills": ["talent_acquisition", "employee_relations", "onboarding", "performance_management", "hris", "benefits_administration", "labor_law", "payroll"],
    },
    "Sales Representative": {
        "categories": ["SALES"],
        "default_title": "Account Executive / B2B Sales Representative",
        "signature_skills": ["b2b_sales", "lead_generation", "cold_calling", "pipeline_management", "salesforce", "customer_relationship_management", "negotiation", "account_management"],
    },
    "Business Development Manager": {
        "categories": ["BUSINESS-DEVELOPMENT"],
        "default_title": "Business Development Manager / Growth Lead",
        "signature_skills": ["b2b_sales", "lead_generation", "strategic_planning", "stakeholder_management", "pipeline_management", "negotiation", "market_research"],
    },
    "Digital Marketer": {
        "categories": ["DIGITAL-MEDIA", "PUBLIC-RELATIONS"],
        "default_title": "Digital Marketing Strategist / Content Specialist",
        "signature_skills": ["seo", "google_analytics", "social_media_marketing", "email_marketing", "content_strategy", "copywriting", "ppc_advertising", "adobe_photoshop"],
    },
    "UI/UX & Graphic Designer": {
        "categories": ["DESIGNER"],
        "default_title": "Senior UI/UX & Graphic Designer",
        "signature_skills": ["figma", "ui_design", "ux_design", "wireframing", "prototyping", "visual_design", "adobe_photoshop", "adobe_illustrator"],
    },
    "Healthcare Specialist": {
        "categories": ["HEALTHCARE"],
        "default_title": "Clinical Healthcare Specialist / Patient Care Lead",
        "signature_skills": ["patient_care", "clinical_documentation", "electronic_health_records", "vital_signs", "hipaa_compliance", "medical_terminology", "cpr"],
    },
    "Management Consultant": {
        "categories": ["CONSULTANT"],
        "default_title": "Management Consultant / Strategy Analyst",
        "signature_skills": ["strategic_planning", "stakeholder_management", "process_improvement", "change_management", "risk_management", "business_analysis", "project_management"],
    },
    "Mechanical/Civil Engineer": {
        "categories": ["ENGINEERING", "CONSTRUCTION"],
        "default_title": "Project Engineer / Mechanical & Civil Engineer",
        "signature_skills": ["autocad", "solidworks", "matlab", "quality_control", "safety_compliance", "project_management"],
    },
    "Teacher & Educator": {
        "categories": ["TEACHER"],
        "default_title": "Academic Educator / High School & College Teacher",
        "signature_skills": ["curriculum_development", "classroom_management", "lesson_planning", "student_assessment"],
    },
    "Legal Associate": {
        "categories": ["ADVOCATE"],
        "default_title": "Legal Associate / Corporate Counsel Advocate",
        "signature_skills": ["legal_research", "contract_drafting", "litigation", "regulatory_compliance", "due_diligence", "negotiation"],
    },
}


# 3. New Domain Courses to add to catalog
NEW_COURSES = [
    {
        "course_id": "c_fin_01",
        "title": "Financial Accounting Fundamentals & Reporting",
        "description": "Comprehensive grounding in financial accounting, general ledger entries, GAAP standards, financial reporting, and balance sheet reconciliation.",
        "platform": "Coursera",
        "rating": 4.8,
        "level": "beginner",
        "duration_hours": 24.0,
        "url": "https://www.coursera.org/learn/wharton-accounting",
        "taught_skills": ["accounting", "financial_reporting", "general_ledger", "gaap", "reconciliation"],
    },
    {
        "course_id": "c_fin_02",
        "title": "Corporate Financial Modeling & Valuation Masterclass",
        "description": "Build three-statement financial models, forecast budgeting, perform discounted cash flow valuation, and master corporate financial analysis.",
        "platform": "Coursera",
        "rating": 4.9,
        "level": "intermediate",
        "duration_hours": 32.0,
        "url": "https://www.coursera.org/learn/financial-modeling",
        "taught_skills": ["financial_modeling", "financial_analysis", "budgeting", "wealth_management"],
    },
    {
        "course_id": "c_fin_03",
        "title": "QuickBooks Online Bookkeeping & Tax Preparation",
        "description": "Master QuickBooks Online for small business accounting, invoicing, accounts payable, accounts receivable, payroll processing, and tax preparation.",
        "platform": "Udemy",
        "rating": 4.7,
        "level": "beginner",
        "duration_hours": 18.0,
        "url": "https://www.udemy.com/course/quickbooks-online-bookkeeping",
        "taught_skills": ["quickbooks", "tax_preparation", "accounts_payable", "accounts_receivable", "payroll", "auditing"],
    },
    {
        "course_id": "c_hr_01",
        "title": "Human Resources Management: HR for People Managers",
        "description": "Essential principles of human resources, talent acquisition, recruitment sourcing, employee onboarding, workplace relations, and HRIS systems.",
        "platform": "Coursera",
        "rating": 4.8,
        "level": "beginner",
        "duration_hours": 20.0,
        "url": "https://www.coursera.org/specializations/human-resource-management",
        "taught_skills": ["talent_acquisition", "onboarding", "employee_relations", "hris"],
    },
    {
        "course_id": "c_hr_02",
        "title": "Strategic HR Leadership: Performance & Compliance",
        "description": "Advanced workforce planning, performance management appraisals, employee benefits administration, and labor law statutory compliance.",
        "platform": "Coursera",
        "rating": 4.7,
        "level": "intermediate",
        "duration_hours": 22.0,
        "url": "https://www.coursera.org/learn/strategic-hr-leadership",
        "taught_skills": ["performance_management", "benefits_administration", "labor_law", "workforce_planning"],
    },
    {
        "course_id": "c_sales_01",
        "title": "B2B Sales Masterclass & Enterprise Prospecting",
        "description": "Learn professional B2B enterprise selling, lead generation prospecting, cold calling outreach, sales pipeline management, and contract negotiation.",
        "platform": "Udemy",
        "rating": 4.8,
        "level": "beginner",
        "duration_hours": 16.0,
        "url": "https://www.udemy.com/course/b2b-sales-masterclass",
        "taught_skills": ["b2b_sales", "lead_generation", "cold_calling", "pipeline_management", "negotiation"],
    },
    {
        "course_id": "c_sales_02",
        "title": "CRM Strategy with Salesforce & Client Management",
        "description": "Master Salesforce CRM administration, lead qualification, client relationship management, pipeline reporting, and key account management.",
        "platform": "Coursera",
        "rating": 4.9,
        "level": "intermediate",
        "duration_hours": 20.0,
        "url": "https://www.coursera.org/learn/salesforce-crm",
        "taught_skills": ["salesforce", "customer_relationship_management", "account_management", "pipeline_management"],
    },
    {
        "course_id": "c_mkt_01",
        "title": "Digital Marketing Specialization: SEO, Analytics & Content",
        "description": "Full-funnel digital marketing: search engine optimization (SEO), Google Analytics web metrics, content marketing copywriting, email marketing, and PPC ads.",
        "platform": "Coursera",
        "rating": 4.8,
        "level": "beginner",
        "duration_hours": 28.0,
        "url": "https://www.coursera.org/specializations/digital-marketing",
        "taught_skills": ["seo", "google_analytics", "content_strategy", "social_media_marketing", "email_marketing", "copywriting", "ppc_advertising"],
    },
    {
        "course_id": "c_des_01",
        "title": "Graphic Design Specialization: Visual Communication",
        "description": "Design theory, visual composition, typography, image manipulation in Adobe Photoshop, vector art in Adobe Illustrator, and digital branding.",
        "platform": "Coursera",
        "rating": 4.8,
        "level": "beginner",
        "duration_hours": 26.0,
        "url": "https://www.coursera.org/specializations/graphic-design",
        "taught_skills": ["visual_design", "adobe_photoshop", "adobe_illustrator", "ui_design", "figma"],
    },
    {
        "course_id": "c_hc_01",
        "title": "Clinical Healthcare Practice & Patient Administration",
        "description": "Foundations of direct patient care, medical records documentation, electronic health records (EHR/EMR), HIPAA compliance, vital signs, and CPR standards.",
        "platform": "Coursera",
        "rating": 4.8,
        "level": "beginner",
        "duration_hours": 25.0,
        "url": "https://www.coursera.org/learn/clinical-terminology-ehr",
        "taught_skills": ["patient_care", "clinical_documentation", "electronic_health_records", "vital_signs", "hipaa_compliance", "medical_terminology", "cpr"],
    },
    {
        "course_id": "c_cons_01",
        "title": "Management Consulting & Strategic Problem Solving",
        "description": "Hypothesis-driven problem solving, strategic planning frameworks, business process improvement, stakeholder alignment, and organizational change management.",
        "platform": "Coursera",
        "rating": 4.9,
        "level": "intermediate",
        "duration_hours": 22.0,
        "url": "https://www.coursera.org/learn/management-consulting-skills",
        "taught_skills": ["strategic_planning", "stakeholder_management", "process_improvement", "change_management", "risk_management", "business_analysis"],
    },
    {
        "course_id": "c_eng_01",
        "title": "Engineering Design, 3D CAD & Safety Standards",
        "description": "Computer-aided drafting in AutoCAD, mechanical parts modeling in SolidWorks, technical engineering documentation, quality control, and OSHA safety compliance.",
        "platform": "Coursera",
        "rating": 4.7,
        "level": "beginner",
        "duration_hours": 30.0,
        "url": "https://www.coursera.org/learn/engineering-design-cad",
        "taught_skills": ["autocad", "solidworks", "matlab", "quality_control", "safety_compliance"],
    },
    {
        "course_id": "c_edu_01",
        "title": "Foundations of Teaching: Curriculum Design & Instruction",
        "description": "Pedagogical methodologies, syllabus and curriculum development, active classroom management, lesson planning, and student performance assessment.",
        "platform": "Coursera",
        "rating": 4.8,
        "level": "beginner",
        "duration_hours": 20.0,
        "url": "https://www.coursera.org/learn/teaching-character-instruction",
        "taught_skills": ["curriculum_development", "classroom_management", "lesson_planning", "student_assessment"],
    },
    {
        "course_id": "c_leg_01",
        "title": "Legal Practice & Commercial Contract Drafting",
        "description": "Essential legal research in case law, drafting commercial agreements, litigation filings, due diligence review, and regulatory compliance oversight.",
        "platform": "Coursera",
        "rating": 4.8,
        "level": "intermediate",
        "duration_hours": 22.0,
        "url": "https://www.coursera.org/learn/contract-drafting-legal-research",
        "taught_skills": ["legal_research", "contract_drafting", "litigation", "regulatory_compliance"],
    },
]


def update_skills_taxonomy(model: SentenceTransformer) -> None:
    """Add new canonical skills to skills.json and re-encode skill_embeddings.npy."""
    skills_file = BASE_DIR / "data" / "processed" / "skills.json"
    with open(skills_file, "r", encoding="utf-8") as f:
        skills_db = json.load(f)

    added_count = 0
    for sid, sdata in NEW_SKILLS.items():
        if sid not in skills_db:
            skills_db[sid] = sdata
            added_count += 1

    logger.info("Adding %d new non-CSE skills to taxonomy. Total skills: %d", added_count, len(skills_db))

    with open(skills_file, "w", encoding="utf-8") as f:
        json.dump(skills_db, f, indent=2)

    # Re-encode skill embeddings
    skill_ids = sorted(skills_db.keys())
    skill_texts = [
        f"{s_data['name']}: {', '.join(s_data.get('aliases', []))}"
        for s_data in [skills_db[sid] for sid in skill_ids]
    ]

    logger.info("Computing dense MiniLM embeddings for all %d skills...", len(skill_texts))
    emb_matrix = model.encode(
        skill_texts,
        normalize_embeddings=True,
        show_progress_bar=False,
    ).astype(np.float32)

    np.save(BASE_DIR / "data" / "processed" / "skill_embeddings.npy", emb_matrix)
    with open(BASE_DIR / "data" / "processed" / "skill_ids.json", "w", encoding="utf-8") as f:
        json.dump(skill_ids, f, indent=2)

    # Reload global taxonomy instance in memory
    taxonomy.load()
    logger.info("Taxonomy successfully updated and reloaded.")


def build_role_profiles_from_resumes(model: SentenceTransformer) -> None:
    """Extract skills from Kaggle resumes to build empirical role profiles."""
    if not USER_RESUME_CSV.is_file():
        raise FileNotFoundError(f"User resume dataset not found at {USER_RESUME_CSV}")

    logger.info("Reading Kaggle resume dataset from %s...", USER_RESUME_CSV)
    df = pd.read_csv(USER_RESUME_CSV)
    logger.info("Loaded %d resumes across %d categories.", len(df), df["Category"].nunique())

    # Load existing role profiles
    role_profiles_path = BASE_DIR / "data" / "processed" / "role_profiles.json"
    with open(role_profiles_path, "r", encoding="utf-8") as f:
        all_profiles = json.load(f)

    logger.info("Current role profiles count: %d (%s)", len(all_profiles), list(all_profiles.keys()))

    for role_name, config in TARGET_ROLE_CONFIG.items():
        sub_df = df[df["Category"].isin(config["categories"])]
        if len(sub_df) == 0:
            logger.warning("No resumes found for role '%s' with categories %s", role_name, config["categories"])
            continue

        # Sample up to 35 resumes for efficient, representative empirical extraction
        sample_resumes = sub_df.head(35)["Resume_str"].tolist()
        total_sample = len(sample_resumes)

        skill_counts: Dict[str, int] = {}
        corpus_texts: List[str] = []

        for r_text in sample_resumes:
            corpus_texts.append(r_text[:600])
            hit_skills = set(extract_skills(r_text, mode="baseline").skills)
            for sid in hit_skills:
                skill_counts[sid] = skill_counts.get(sid, 0) + 1

        # Calculate shares and assign tiers
        role_skills_dict: Dict[str, Dict[str, Any]] = {}
        signature_set = set(config.get("signature_skills", []))

        for sid, count in skill_counts.items():
            share = count / total_sample
            s_info = taxonomy.get_skill(sid) or {}
            is_soft = s_info.get("category") == "soft skills"

            # Generic soft skills should not crowd out core domain competencies
            weight = round(share * 0.40 if is_soft else share, 3)

            # Boost signature domain skills
            if sid in signature_set:
                weight = max(weight, 0.60)

            if weight >= 0.08:
                tier = "core" if weight >= 0.35 else ("common" if weight >= 0.18 else "bonus")
                role_skills_dict[sid] = {
                    "weight": weight,
                    "count": max(count, int(total_sample * weight)),
                    "tier": tier,
                }

        # Ensure all signature skills exist in the profile
        for sig_id in config.get("signature_skills", []):
            if sig_id not in role_skills_dict:
                role_skills_dict[sig_id] = {
                    "weight": 0.55,
                    "count": int(total_sample * 0.55),
                    "tier": "core",
                }

        # Sort skills by weight descending
        sorted_skills = dict(sorted(role_skills_dict.items(), key=lambda item: item[1]["weight"], reverse=True))

        combined_text = f"Role: {role_name}. {config['default_title']}. " + " ".join(corpus_texts[:10])

        all_profiles[role_name] = {
            "n_postings": total_sample,
            "skills": sorted_skills,
            "text": combined_text[:3000],
        }

        logger.info("Constructed empirical profile for '%s' (%d resumes, %d skills)", role_name, total_sample, len(sorted_skills))

    # Save expanded role profiles
    with open(role_profiles_path, "w", encoding="utf-8") as f:
        json.dump(all_profiles, f, indent=2)

    logger.info("Saved %d total role profiles to %s", len(all_profiles), role_profiles_path)

    # Compute dense embeddings for all roles
    all_role_names = sorted(all_profiles.keys())
    role_texts = [
        f"{r}: {all_profiles[r].get('text', '')}" for r in all_role_names
    ]
    logger.info("Computing dense embeddings for all %d roles...", len(all_role_names))
    role_emb = model.encode(role_texts, normalize_embeddings=True, show_progress_bar=False).astype(np.float32)
    role_emb_dict = {
        r_name: role_emb[i] for i, r_name in enumerate(all_role_names)
    }
    np.save(BASE_DIR / "data" / "processed" / "role_embeddings.npy", role_emb_dict, allow_pickle=True)
    logger.info("Role embeddings dictionary saved for %d roles.", len(role_emb_dict))


def update_course_catalog(model: SentenceTransformer) -> None:
    """Add new domain courses to courses.json and re-encode course_embeddings.npy."""
    courses_file = BASE_DIR / "data" / "processed" / "courses.json"
    with open(courses_file, "r", encoding="utf-8") as f:
        courses = json.load(f)

    existing_ids = {c["course_id"] for c in courses}
    added_count = 0
    for nc in NEW_COURSES:
        if nc["course_id"] not in existing_ids:
            courses.append(nc)
            added_count += 1

    logger.info("Added %d new domain courses. Total courses in catalog: %d", added_count, len(courses))

    with open(courses_file, "w", encoding="utf-8") as f:
        json.dump(courses, f, indent=2)

    # Re-encode course embeddings
    course_texts = [
        f"{c['title']}. {c['description']} Skills taught: {', '.join(c.get('taught_skills', []))}"
        for c in courses
    ]
    logger.info("Computing dense embeddings for all %d courses...", len(course_texts))
    c_emb = model.encode(course_texts, normalize_embeddings=True, show_progress_bar=False).astype(np.float32)
    np.save(BASE_DIR / "data" / "processed" / "course_embeddings.npy", c_emb)
    logger.info("Course embeddings saved (shape: %s)", c_emb.shape)


def update_category_role_map() -> None:
    """Update category_role_map.json with mappings for non-CSE categories."""
    cmap_file = BASE_DIR / "data" / "processed" / "category_role_map.json"
    with open(cmap_file, "r", encoding="utf-8") as f:
        cmap = json.load(f)

    new_mappings = {
        "Accountant": "Accountant",
        "ACCOUNTANT": "Accountant",
        "Finance": "Financial Analyst",
        "FINANCE": "Financial Analyst",
        "Banking": "Financial Analyst",
        "BANKING": "Financial Analyst",
        "Human Resources": "HR Specialist",
        "HR": "HR Specialist",
        "Sales": "Sales Representative",
        "SALES": "Sales Representative",
        "Business Development": "Business Development Manager",
        "BUSINESS-DEVELOPMENT": "Business Development Manager",
        "Digital Media": "Digital Marketer",
        "DIGITAL-MEDIA": "Digital Marketer",
        "Designer": "UI/UX & Graphic Designer",
        "DESIGNER": "UI/UX & Graphic Designer",
        "Healthcare": "Healthcare Specialist",
        "HEALTHCARE": "Healthcare Specialist",
        "Consultant": "Management Consultant",
        "CONSULTANT": "Management Consultant",
        "Engineering": "Mechanical/Civil Engineer",
        "ENGINEERING": "Mechanical/Civil Engineer",
        "Teacher": "Teacher & Educator",
        "TEACHER": "Teacher & Educator",
        "Advocate": "Legal Associate",
        "ADVOCATE": "Legal Associate",
    }
    cmap.update(new_mappings)
    with open(cmap_file, "w", encoding="utf-8") as f:
        json.dump(cmap, f, indent=2)
    logger.info("Updated category_role_map.json with %d total category mappings.", len(cmap))


def main():
    logger.info("Initializing SentenceTransformer (%s)...", settings.EMBEDDING_MODEL_NAME)
    model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)

    # 1. Update skills taxonomy with non-CSE skills
    update_skills_taxonomy(model)

    # 2. Build empirical role profiles from real Kaggle resumes
    build_role_profiles_from_resumes(model)

    # 3. Add domain courses to course catalog
    update_course_catalog(model)

    # 4. Update category role map
    update_category_role_map()

    logger.info("All multi-disciplinary roles, skills, and courses successfully generated!")


if __name__ == "__main__":
    main()
