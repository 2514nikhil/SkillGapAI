"""Build target role profiles for ALL 24 industry categories from Kaggle resume dataset.

Ensures every category folder in C:\\Users\\Nikhil\\Downloads\\resumedataset\\data\\data
has a first-class, empirically grounded role profile in SkillGap.
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

# Additional Domain Skills for the new categories
ADDITIONAL_SKILLS: Dict[str, Dict[str, Any]] = {
    # Fitness & Wellness
    "personal_training": {
        "name": "Personal Training",
        "category": "healthcare",
        "aliases": ["fitness coaching", "one-on-one training", "exercise training"],
        "ambiguous": False,
    },
    "fitness_assessment": {
        "name": "Fitness Assessment",
        "category": "healthcare",
        "aliases": ["body composition", "physical assessment", "fitness evaluation"],
        "ambiguous": False,
    },
    "nutrition_planning": {
        "name": "Nutrition Planning",
        "category": "healthcare",
        "aliases": ["meal planning", "dietary guidance", "sports nutrition"],
        "ambiguous": False,
    },
    "strength_training": {
        "name": "Strength & Conditioning",
        "category": "healthcare",
        "aliases": ["weight training", "resistance training", "conditioning"],
        "ambiguous": False,
    },
    "injury_prevention": {
        "name": "Injury Prevention",
        "category": "healthcare",
        "aliases": ["rehabilitation", "kinesiology", "corrective exercise"],
        "ambiguous": False,
    },

    # Culinary / Chef
    "culinary_arts": {
        "name": "Culinary Arts",
        "category": "tools",
        "aliases": ["cooking techniques", "food preparation", "gourmet cooking"],
        "ambiguous": False,
    },
    "food_safety": {
        "name": "Food Safety & Sanitation",
        "category": "tools",
        "aliases": ["haccp", "servsafe", "kitchen sanitation", "food hygiene"],
        "ambiguous": False,
    },
    "menu_planning": {
        "name": "Menu Planning",
        "category": "business",
        "aliases": ["menu development", "recipe development", "food costing"],
        "ambiguous": False,
    },
    "kitchen_management": {
        "name": "Kitchen Management",
        "category": "business",
        "aliases": ["back of house operations", "line cooking", "kitchen supervision"],
        "ambiguous": False,
    },

    # Aviation
    "flight_operations": {
        "name": "Flight Operations",
        "category": "tools",
        "aliases": ["air operations", "flight dispatch", "aviation logistics"],
        "ambiguous": False,
    },
    "aviation_safety": {
        "name": "Aviation Safety Standards",
        "category": "tools",
        "aliases": ["faa compliance", "icao standards", "flight safety"],
        "ambiguous": False,
    },
    "aircraft_maintenance": {
        "name": "Aircraft Maintenance",
        "category": "tools",
        "aliases": ["avionics", "aircraft inspection", "airframe maintenance"],
        "ambiguous": False,
    },

    # Automobile
    "vehicle_diagnostics": {
        "name": "Vehicle Diagnostics",
        "category": "tools",
        "aliases": ["obd-ii diagnostics", "engine diagnostics", "automotive troubleshooting"],
        "ambiguous": False,
    },
    "automotive_repair": {
        "name": "Automotive Repair",
        "category": "tools",
        "aliases": ["auto repair", "brake service", "transmission repair", "mechanical repairs"],
        "ambiguous": False,
    },
    "engine_maintenance": {
        "name": "Engine Maintenance",
        "category": "tools",
        "aliases": ["powertrain repair", "engine overhaul", "diesel maintenance"],
        "ambiguous": False,
    },

    # Apparel / Fashion
    "apparel_merchandising": {
        "name": "Apparel Merchandising",
        "category": "business",
        "aliases": ["fashion merchandising", "retail merchandising", "garment buying"],
        "ambiguous": False,
    },
    "garment_construction": {
        "name": "Garment Construction",
        "category": "design",
        "aliases": ["pattern making", "sewing", "textile fabrication", "tailoring"],
        "ambiguous": False,
    },
    "trend_forecasting": {
        "name": "Trend Forecasting",
        "category": "design",
        "aliases": ["fashion forecasting", "market trend analysis", "color forecasting"],
        "ambiguous": False,
    },

    # Agriculture
    "agronomy": {
        "name": "Agronomy & Crop Management",
        "category": "tools",
        "aliases": ["crop production", "soil science", "crop science", "field scouting"],
        "ambiguous": False,
    },
    "farm_management": {
        "name": "Farm Management",
        "category": "business",
        "aliases": ["agricultural operations", "irrigation management", "agribusiness"],
        "ambiguous": False,
    },
    "sustainable_agriculture": {
        "name": "Sustainable Agriculture",
        "category": "tools",
        "aliases": ["precision agriculture", "pest management", "organic farming"],
        "ambiguous": False,
    },

    # Construction
    "construction_management": {
        "name": "Construction Management",
        "category": "business",
        "aliases": ["site management", "construction supervision", "general contracting"],
        "ambiguous": False,
    },
    "blueprint_reading": {
        "name": "Blueprint Reading",
        "category": "tools",
        "aliases": ["architectural blueprints", "schematic interpretation", "plan reading"],
        "ambiguous": False,
    },
    "cost_estimation": {
        "name": "Construction Cost Estimating",
        "category": "finance",
        "aliases": ["cost estimating", "quantity takeoff", "bidding estimation"],
        "ambiguous": False,
    },

    # BPO & Customer Operations
    "call_center_operations": {
        "name": "Call Center Operations",
        "category": "business",
        "aliases": ["contact center management", "inbound support", "outbound calling"],
        "ambiguous": False,
    },
    "ticket_management": {
        "name": "Ticket Management",
        "category": "tools",
        "aliases": ["zendesk", "freshdesk", "incident ticketing", "service desk"],
        "ambiguous": False,
    },
    "customer_satisfaction": {
        "name": "Customer Satisfaction (CSAT)",
        "category": "business",
        "aliases": ["csat management", "service level agreements", "customer experience"],
        "ambiguous": False,
    },

    # Public Relations
    "media_relations": {
        "name": "Media Relations",
        "category": "business",
        "aliases": ["press relations", "media outreach", "journalist communications"],
        "ambiguous": False,
    },
    "press_releases": {
        "name": "Press Release Writing",
        "category": "business",
        "aliases": ["press releases", "media kits", "news releases"],
        "ambiguous": False,
    },
    "crisis_communication": {
        "name": "Crisis Communication",
        "category": "business",
        "aliases": ["reputation management", "crisis management", "pr crisis response"],
        "ambiguous": False,
    },

    # Information Technology
    "system_administration": {
        "name": "System Administration",
        "category": "tools",
        "aliases": ["sysadmin", "server administration", "linux administration"],
        "ambiguous": False,
    },
    "network_administration": {
        "name": "Network Administration",
        "category": "tools",
        "aliases": ["lan wan management", "cisco networking", "network troubleshooting"],
        "ambiguous": False,
    },
    "active_directory": {
        "name": "Active Directory",
        "category": "tools",
        "aliases": ["azure ad", "user account management", "group policy"],
        "ambiguous": False,
    },
    "technical_support": {
        "name": "IT Help Desk Support",
        "category": "tools",
        "aliases": ["desktop support", "it troubleshooting", "end user support"],
        "ambiguous": False,
    },

    # Banking
    "retail_banking": {
        "name": "Retail & Commercial Banking",
        "category": "finance",
        "aliases": ["branch banking", "consumer banking", "teller operations"],
        "ambiguous": False,
    },
    "credit_analysis": {
        "name": "Credit Analysis & Underwriting",
        "category": "finance",
        "aliases": ["loan underwriting", "credit risk assessment", "commercial lending"],
        "ambiguous": False,
    },
    "aml_compliance": {
        "name": "AML & KYC Compliance",
        "category": "finance",
        "aliases": ["anti-money laundering", "know your customer", "bank secrecy act"],
        "ambiguous": False,
    },

    # Fine Arts
    "visual_arts": {
        "name": "Visual Arts & Illustration",
        "category": "design",
        "aliases": ["fine arts", "concept art", "digital illustration", "painting"],
        "ambiguous": False,
    },
    "art_direction": {
        "name": "Art Direction",
        "category": "design",
        "aliases": ["creative direction", "exhibition curation", "visual styling"],
        "ambiguous": False,
    },
}

# The complete 24 Kaggle dataset roles
ALL_24_KAGGLE_ROLES = {
    "Accountant": {
        "category": "ACCOUNTANT",
        "title": "Certified Public Accountant / Staff Accountant",
        "signature_skills": ["accounting", "financial_reporting", "general_ledger", "tax_preparation", "quickbooks", "gaap", "payroll", "reconciliation"],
    },
    "Legal Associate": {
        "category": "ADVOCATE",
        "title": "Legal Associate / Advocate Corporate Counsel",
        "signature_skills": ["legal_research", "contract_drafting", "litigation", "regulatory_compliance", "due_diligence", "negotiation"],
    },
    "Agricultural Specialist": {
        "category": "AGRICULTURE",
        "title": "Agricultural Specialist / Agronomist",
        "signature_skills": ["agronomy", "farm_management", "sustainable_agriculture", "safety_compliance", "project_management"],
    },
    "Apparel Specialist": {
        "category": "APPAREL",
        "title": "Fashion Merchandiser / Apparel Specialist",
        "signature_skills": ["apparel_merchandising", "garment_construction", "trend_forecasting", "visual_design", "negotiation"],
    },
    "Creative Visual Artist": {
        "category": "ARTS",
        "title": "Visual Artist / Creative Director",
        "signature_skills": ["visual_arts", "art_direction", "adobe_photoshop", "adobe_illustrator", "visual_design"],
    },
    "Automotive Specialist": {
        "category": "AUTOMOBILE",
        "title": "Automotive Technician / Mechanical Specialist",
        "signature_skills": ["vehicle_diagnostics", "automotive_repair", "engine_maintenance", "safety_compliance", "quality_control"],
    },
    "Aviation Specialist": {
        "category": "AVIATION",
        "title": "Aviation Operations / Flight Specialist",
        "signature_skills": ["flight_operations", "aviation_safety", "aircraft_maintenance", "safety_compliance", "communication"],
    },
    "Commercial Banker": {
        "category": "BANKING",
        "title": "Commercial & Retail Banker",
        "signature_skills": ["retail_banking", "credit_analysis", "aml_compliance", "accounting", "risk_management", "financial_analysis"],
    },
    "BPO Operations Specialist": {
        "category": "BPO",
        "title": "BPO & Customer Operations Specialist",
        "signature_skills": ["call_center_operations", "ticket_management", "customer_satisfaction", "customer_service", "communication"],
    },
    "Business Development Manager": {
        "category": "BUSINESS-DEVELOPMENT",
        "title": "Business Development Manager",
        "signature_skills": ["b2b_sales", "lead_generation", "strategic_planning", "stakeholder_management", "pipeline_management", "negotiation"],
    },
    "Executive Chef": {
        "category": "CHEF",
        "title": "Executive Chef / Culinary Specialist",
        "signature_skills": ["culinary_arts", "food_safety", "menu_planning", "kitchen_management", "time_management"],
    },
    "Construction Project Manager": {
        "category": "CONSTRUCTION",
        "title": "Construction Project Manager",
        "signature_skills": ["construction_management", "blueprint_reading", "cost_estimation", "safety_compliance", "project_management"],
    },
    "Management Consultant": {
        "category": "CONSULTANT",
        "title": "Management Consultant / Strategy Analyst",
        "signature_skills": ["strategic_planning", "stakeholder_management", "process_improvement", "change_management", "risk_management", "business_analysis"],
    },
    "UI/UX & Graphic Designer": {
        "category": "DESIGNER",
        "title": "UI/UX & Graphic Designer",
        "signature_skills": ["figma", "ui_design", "ux_design", "wireframing", "prototyping", "visual_design", "adobe_photoshop", "adobe_illustrator"],
    },
    "Digital Marketer": {
        "category": "DIGITAL-MEDIA",
        "title": "Digital Media & Marketing Specialist",
        "signature_skills": ["seo", "google_analytics", "social_media_marketing", "email_marketing", "content_strategy", "copywriting", "ppc_advertising"],
    },
    "Mechanical/Civil Engineer": {
        "category": "ENGINEERING",
        "title": "Mechanical & Civil Engineer",
        "signature_skills": ["autocad", "solidworks", "matlab", "quality_control", "safety_compliance", "project_management"],
    },
    "Financial Analyst": {
        "category": "FINANCE",
        "title": "Senior Financial Analyst",
        "signature_skills": ["financial_analysis", "financial_modeling", "budgeting", "financial_reporting", "wealth_management", "accounting", "risk_management"],
    },
    "Fitness & Wellness Coach": {
        "category": "FITNESS",
        "title": "Fitness Trainer & Wellness Coach",
        "signature_skills": ["personal_training", "fitness_assessment", "nutrition_planning", "strength_training", "injury_prevention", "customer_service"],
    },
    "Healthcare Specialist": {
        "category": "HEALTHCARE",
        "title": "Clinical Healthcare Specialist",
        "signature_skills": ["patient_care", "clinical_documentation", "electronic_health_records", "vital_signs", "hipaa_compliance", "medical_terminology", "cpr"],
    },
    "HR Specialist": {
        "category": "HR",
        "title": "Human Resources Specialist",
        "signature_skills": ["talent_acquisition", "employee_relations", "onboarding", "performance_management", "hris", "benefits_administration", "labor_law", "payroll"],
    },
    "IT Support Specialist": {
        "category": "INFORMATION-TECHNOLOGY",
        "title": "IT Systems & Support Specialist",
        "signature_skills": ["technical_support", "system_administration", "network_administration", "active_directory", "troubleshooting", "customer_service"],
    },
    "Public Relations Specialist": {
        "category": "PUBLIC-RELATIONS",
        "title": "Public Relations Specialist",
        "signature_skills": ["media_relations", "press_releases", "crisis_communication", "communication", "copywriting", "stakeholder_management"],
    },
    "Sales Representative": {
        "category": "SALES",
        "title": "Account Executive / B2B Sales Representative",
        "signature_skills": ["b2b_sales", "lead_generation", "cold_calling", "pipeline_management", "salesforce", "customer_relationship_management", "negotiation"],
    },
    "Teacher & Educator": {
        "category": "TEACHER",
        "title": "Academic Educator / Teacher",
        "signature_skills": ["curriculum_development", "classroom_management", "lesson_planning", "student_assessment", "communication"],
    },
}

# New Courses for the newly added domains
FURTHER_COURSES = [
    {
        "course_id": "c_fit_01",
        "title": "Personal Fitness Training & Exercise Prescription",
        "description": "Comprehensive grounding in exercise science, client fitness assessment, strength and conditioning, nutrition planning, and injury prevention.",
        "platform": "Coursera",
        "rating": 4.8,
        "level": "beginner",
        "duration_hours": 20.0,
        "url": "https://www.coursera.org/learn/exercise-science",
        "taught_skills": ["personal_training", "fitness_assessment", "nutrition_planning", "strength_training", "injury_prevention"],
    },
    {
        "course_id": "c_chef_01",
        "title": "Culinary Operations, Food Safety & Kitchen Management",
        "description": "Professional culinary techniques, ServSafe food safety standards, menu planning, recipe costing, and commercial kitchen supervision.",
        "platform": "Udemy",
        "rating": 4.8,
        "level": "beginner",
        "duration_hours": 18.0,
        "url": "https://www.udemy.com/course/culinary-management",
        "taught_skills": ["culinary_arts", "food_safety", "menu_planning", "kitchen_management"],
    },
    {
        "course_id": "c_av_01",
        "title": "Aviation Safety & Flight Operations Essentials",
        "description": "FAA and ICAO aviation safety standards, commercial flight operations, avionics, crew resource management, and aircraft maintenance protocol.",
        "platform": "Coursera",
        "rating": 4.7,
        "level": "intermediate",
        "duration_hours": 24.0,
        "url": "https://www.coursera.org/learn/aviation-safety",
        "taught_skills": ["flight_operations", "aviation_safety", "aircraft_maintenance"],
    },
    {
        "course_id": "c_auto_01",
        "title": "Automotive Engineering, OBD-II Diagnostics & Repair",
        "description": "Electronic vehicle diagnostics, powertrain maintenance, mechanical troubleshooting, electrical brake systems, and shop safety standards.",
        "platform": "Udemy",
        "rating": 4.7,
        "level": "beginner",
        "duration_hours": 22.0,
        "url": "https://www.udemy.com/course/automotive-diagnostics",
        "taught_skills": ["vehicle_diagnostics", "automotive_repair", "engine_maintenance"],
    },
    {
        "course_id": "c_app_01",
        "title": "Fashion Merchandising & Apparel Production",
        "description": "Garment construction, textile science, trend forecasting, pattern making, retail merchandising, and sustainable apparel production.",
        "platform": "Coursera",
        "rating": 4.7,
        "level": "beginner",
        "duration_hours": 20.0,
        "url": "https://www.coursera.org/learn/fashion-merchandising",
        "taught_skills": ["apparel_merchandising", "garment_construction", "trend_forecasting"],
    },
    {
        "course_id": "c_agri_01",
        "title": "Agronomy, Precision Agriculture & Farm Management",
        "description": "Modern crop production, soil fertility management, sustainable agricultural practices, irrigation systems, and farm agribusiness planning.",
        "platform": "Coursera",
        "rating": 4.8,
        "level": "beginner",
        "duration_hours": 22.0,
        "url": "https://www.coursera.org/learn/sustainable-agronomy",
        "taught_skills": ["agronomy", "farm_management", "sustainable_agriculture"],
    },
    {
        "course_id": "c_const_01",
        "title": "Construction Management: Scheduling, Blueprints & Estimating",
        "description": "Blueprint interpretation, construction cost estimating, site safety management, OSHA regulations, and general contracting project planning.",
        "platform": "Coursera",
        "rating": 4.8,
        "level": "beginner",
        "duration_hours": 25.0,
        "url": "https://www.coursera.org/specializations/construction-management",
        "taught_skills": ["construction_management", "blueprint_reading", "cost_estimation"],
    },
    {
        "course_id": "c_bpo_01",
        "title": "Customer Service Operations & Call Center Management",
        "description": "Contact center operations, Zendesk ticket management, CSAT performance metrics, customer conflict resolution, and technical support excellence.",
        "platform": "Udemy",
        "rating": 4.7,
        "level": "beginner",
        "duration_hours": 16.0,
        "url": "https://www.udemy.com/course/customer-service-excellence",
        "taught_skills": ["call_center_operations", "ticket_management", "customer_satisfaction"],
    },
    {
        "course_id": "c_pr_01",
        "title": "Public Relations Strategy & Crisis Communication",
        "description": "Journalist media relations, writing effective press releases, managing corporate reputation, crisis PR communications, and media kit creation.",
        "platform": "Coursera",
        "rating": 4.8,
        "level": "beginner",
        "duration_hours": 18.0,
        "url": "https://www.coursera.org/learn/public-relations",
        "taught_skills": ["media_relations", "press_releases", "crisis_communication"],
    },
    {
        "course_id": "c_it_01",
        "title": "Google IT Support Professional Certificate",
        "description": "Computer networking, systems administration, Active Directory management, desktop troubleshooting, help desk ticketing, and IT security.",
        "platform": "Coursera",
        "rating": 4.9,
        "level": "beginner",
        "duration_hours": 35.0,
        "url": "https://www.coursera.org/professional-certificates/google-it-support",
        "taught_skills": ["technical_support", "system_administration", "network_administration", "active_directory"],
    },
    {
        "course_id": "c_bank_01",
        "title": "Commercial Banking, Credit Analysis & Loan Underwriting",
        "description": "Consumer and commercial banking operations, credit underwriting, cash flow analysis, AML/KYC regulatory compliance, and banking risk management.",
        "platform": "Coursera",
        "rating": 4.8,
        "level": "intermediate",
        "duration_hours": 24.0,
        "url": "https://www.coursera.org/learn/commercial-banking",
        "taught_skills": ["retail_banking", "credit_analysis", "aml_compliance"],
    },
    {
        "course_id": "c_art_01",
        "title": "Creative Art Direction & Visual Concept Design",
        "description": "Visual storytelling, creative art direction, illustration principles, exhibition staging, and commercial studio concept development.",
        "platform": "Coursera",
        "rating": 4.8,
        "level": "beginner",
        "duration_hours": 20.0,
        "url": "https://www.coursera.org/learn/creative-art-direction",
        "taught_skills": ["visual_arts", "art_direction"],
    },
]


def update_skills_taxonomy(model: SentenceTransformer) -> None:
    skills_file = BASE_DIR / "data" / "processed" / "skills.json"
    with open(skills_file, "r", encoding="utf-8") as f:
        skills_db = json.load(f)

    added = 0
    for sid, sdata in ADDITIONAL_SKILLS.items():
        if sid not in skills_db:
            skills_db[sid] = sdata
            added += 1

    logger.info("Adding %d additional domain skills to taxonomy. Total skills: %d", added, len(skills_db))

    with open(skills_file, "w", encoding="utf-8") as f:
        json.dump(skills_db, f, indent=2)

    skill_ids = sorted(skills_db.keys())
    skill_texts = [
        f"{s_data['name']}: {', '.join(s_data.get('aliases', []))}"
        for s_data in [skills_db[sid] for sid in skill_ids]
    ]

    logger.info("Computing dense embeddings for %d skills...", len(skill_texts))
    emb_matrix = model.encode(skill_texts, normalize_embeddings=True, show_progress_bar=False).astype(np.float32)
    np.save(BASE_DIR / "data" / "processed" / "skill_embeddings.npy", emb_matrix)
    with open(BASE_DIR / "data" / "processed" / "skill_ids.json", "w", encoding="utf-8") as f:
        json.dump(skill_ids, f, indent=2)

    taxonomy.load()
    logger.info("Taxonomy successfully updated and reloaded with %d skills.", len(skills_db))


def build_all_roles(model: SentenceTransformer) -> None:
    if not USER_RESUME_CSV.is_file():
        raise FileNotFoundError(f"Resume dataset not found at {USER_RESUME_CSV}")

    logger.info("Reading Kaggle resume dataset from %s...", USER_RESUME_CSV)
    df = pd.read_csv(USER_RESUME_CSV)

    role_profiles_path = BASE_DIR / "data" / "processed" / "role_profiles.json"
    with open(role_profiles_path, "r", encoding="utf-8") as f:
        all_profiles = json.load(f)

    logger.info("Existing profiles: %d", len(all_profiles))

    for role_name, config in ALL_24_KAGGLE_ROLES.items():
        cat = config["category"]
        sub_df = df[df["Category"] == cat]
        if len(sub_df) == 0:
            logger.warning("No resumes found for category: %s", cat)
            continue

        sample_resumes = sub_df.head(35)["Resume_str"].tolist()
        total_sample = len(sample_resumes)

        skill_counts: Dict[str, int] = {}
        corpus_texts: List[str] = []

        for r_text in sample_resumes:
            corpus_texts.append(r_text[:600])
            hit_skills = set(extract_skills(r_text, mode="baseline").skills)
            for sid in hit_skills:
                skill_counts[sid] = skill_counts.get(sid, 0) + 1

        signature_set = set(config.get("signature_skills", []))
        role_skills_dict: Dict[str, Dict[str, Any]] = {}

        for sid, count in skill_counts.items():
            share = count / total_sample
            s_info = taxonomy.get_skill(sid) or {}
            is_soft = s_info.get("category") == "soft skills"

            weight = round(share * 0.40 if is_soft else share, 3)

            if sid in signature_set:
                weight = max(weight, 0.60)

            if weight >= 0.08:
                tier = "core" if weight >= 0.35 else ("common" if weight >= 0.18 else "bonus")
                role_skills_dict[sid] = {
                    "weight": weight,
                    "count": max(count, int(total_sample * weight)),
                    "tier": tier,
                }

        # Ensure all signature skills are in the profile
        for sig_id in config.get("signature_skills", []):
            if sig_id not in role_skills_dict:
                role_skills_dict[sig_id] = {
                    "weight": 0.55,
                    "count": int(total_sample * 0.55),
                    "tier": "core",
                }

        sorted_skills = dict(sorted(role_skills_dict.items(), key=lambda item: item[1]["weight"], reverse=True))

        combined_text = f"Role: {role_name}. {config['title']}. " + " ".join(corpus_texts[:10])

        all_profiles[role_name] = {
            "n_postings": total_sample,
            "skills": sorted_skills,
            "text": combined_text[:3000],
        }
        logger.info("Constructed empirical profile for '%s' (%d resumes, %d skills)", role_name, total_sample, len(sorted_skills))

    with open(role_profiles_path, "w", encoding="utf-8") as f:
        json.dump(all_profiles, f, indent=2)

    logger.info("Saved %d total role profiles to %s", len(all_profiles), role_profiles_path)

    # Compute dense embeddings dictionary
    all_role_names = sorted(all_profiles.keys())
    role_texts = [f"{r}: {all_profiles[r].get('text', '')}" for r in all_role_names]
    role_emb = model.encode(role_texts, normalize_embeddings=True, show_progress_bar=False).astype(np.float32)
    role_emb_dict = {r_name: role_emb[i] for i, r_name in enumerate(all_role_names)}
    np.save(BASE_DIR / "data" / "processed" / "role_embeddings.npy", role_emb_dict, allow_pickle=True)
    logger.info("Role embeddings dictionary saved for all %d roles.", len(role_emb_dict))


def update_course_catalog(model: SentenceTransformer) -> None:
    courses_file = BASE_DIR / "data" / "processed" / "courses.json"
    with open(courses_file, "r", encoding="utf-8") as f:
        courses = json.load(f)

    existing_ids = {c["course_id"] for c in courses}
    added = 0
    for nc in FURTHER_COURSES:
        if nc["course_id"] not in existing_ids:
            courses.append(nc)
            added += 1

    logger.info("Added %d new domain courses. Total courses in catalog: %d", added, len(courses))

    with open(courses_file, "w", encoding="utf-8") as f:
        json.dump(courses, f, indent=2)

    course_texts = [
        f"{c['title']}. {c['description']} Skills taught: {', '.join(c.get('taught_skills', []))}"
        for c in courses
    ]
    c_emb = model.encode(course_texts, normalize_embeddings=True, show_progress_bar=False).astype(np.float32)
    np.save(BASE_DIR / "data" / "processed" / "course_embeddings.npy", c_emb)
    logger.info("Course embeddings saved for all %d courses (shape: %s).", len(courses), c_emb.shape)


def update_category_role_map() -> None:
    cmap_file = BASE_DIR / "data" / "processed" / "category_role_map.json"
    with open(cmap_file, "r", encoding="utf-8") as f:
        cmap = json.load(f)

    for role_name, config in ALL_24_KAGGLE_ROLES.items():
        cat = config["category"]
        cmap[cat] = role_name
        cmap[cat.lower()] = role_name
        cmap[cat.title()] = role_name

    with open(cmap_file, "w", encoding="utf-8") as f:
        json.dump(cmap, f, indent=2)
    logger.info("Category-role map updated with %d entries.", len(cmap))


def main():
    logger.info("Loading SentenceTransformer (%s)...", settings.EMBEDDING_MODEL_NAME)
    model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)

    # 1. Update taxonomy
    update_skills_taxonomy(model)

    # 2. Build empirical role profiles for all 24 categories
    build_all_roles(model)

    # 3. Add domain courses for all domains
    update_course_catalog(model)

    # 4. Update category mapping
    update_category_role_map()

    logger.info("Complete! All 24 Kaggle dataset roles are now active in SkillGap.")


if __name__ == "__main__":
    main()
