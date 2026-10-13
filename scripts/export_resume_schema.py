"""Export JSON Schema and generate validated example resume fixtures."""

import json
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml.resume_schema import Resume, export_json_schema

SCHEMA_FILE = BASE_DIR / "docs" / "resume.schema.json"
FIXTURE_1 = BASE_DIR / "tests" / "fixtures" / "resume_example_1.json"
FIXTURE_2 = BASE_DIR / "tests" / "fixtures" / "resume_example_2.json"

example_1 = {
    "meta": {
        "template": "modern",
        "target_role": "Backend Developer"
    },
    "basics": {
        "name": "Nikhil Maghodiya",
        "headline": "Backend & Cloud Systems Engineer",
        "email": "nikhil@example.com",
        "phone": "+91 9876543210",
        "location": {
            "city": "Bengaluru",
            "region_country": "India"
        },
        "links": [
            {"platform_id": "github", "value": "2514nikhil"},
            {"platform_id": "linkedin", "value": "nikhil-maghodiya"},
            {"platform_id": "portfolio", "value": "https://nikhil.dev"},
            {"platform_id": "leetcode", "value": "nikhil_25"}
        ]
    },
    "summary": "Full-stack backend software engineer with 3+ years building high-throughput microservices using Python, FastAPI, Docker, and PostgreSQL. Experienced in distributed caching, deterministic ML pipelines, and edge deployments.",
    "skills": [
        {"category_id": "languages", "name": "Python", "taxonomy_id": "python", "custom": False, "pinned": True, "level": "strong"},
        {"category_id": "languages", "name": "TypeScript", "taxonomy_id": "typescript", "custom": False, "pinned": True, "level": "comfortable"},
        {"category_id": "languages", "name": "SQL", "taxonomy_id": "sql", "custom": False, "pinned": True, "level": "strong"},
        {"category_id": "frameworks_libraries", "name": "FastAPI", "taxonomy_id": "fastapi", "custom": False, "pinned": True, "level": "strong"},
        {"category_id": "frameworks_libraries", "name": "Next.js", "taxonomy_id": "nextjs", "custom": False, "pinned": True, "level": "comfortable"},
        {"category_id": "databases_orm", "name": "PostgreSQL", "taxonomy_id": "postgresql", "custom": False, "pinned": True, "level": "strong"},
        {"category_id": "databases_orm", "name": "Redis", "taxonomy_id": "redis", "custom": False, "pinned": False, "level": "comfortable"},
        {"category_id": "cicd_vcs", "name": "Docker", "taxonomy_id": "docker", "custom": False, "pinned": True, "level": "strong"},
        {"category_id": "cicd_vcs", "name": "GitHub Actions", "taxonomy_id": "github_actions", "custom": False, "pinned": False, "level": "comfortable"},
        {"category_id": "hosting_cloud", "name": "AWS", "taxonomy_id": "aws", "custom": False, "pinned": False, "level": "comfortable"},
        {"category_id": "testing", "name": "Pytest", "taxonomy_id": "pytest", "custom": False, "pinned": False, "level": "strong"},
        {"category_id": "soft_skills", "name": "Problem Solving", "taxonomy_id": "problem_solving", "custom": False, "pinned": False, "level": "strong"}
    ],
    "experience": [
        {
            "company": "Apex Cloud Systems",
            "title": "Backend Software Engineer",
            "location": "Bengaluru, India",
            "start": "2023-01",
            "end": "Present",
            "current": True,
            "bullets": [
                "Architected asynchronous REST microservices processing 12M monthly requests using FastAPI and PostgreSQL.",
                "Engineered Redis write-through caching layer reducing p99 API latencies from 380ms down to 42ms.",
                "Designed Dockerized CI/CD deployment pipelines on GitHub Actions reducing release build cycles by 40%."
            ]
        },
        {
            "company": "NextGen Infotech",
            "title": "Software Engineering Intern",
            "location": "Pune, India",
            "start": "2022-06",
            "end": "2022-12",
            "current": False,
            "bullets": [
                "Built data ingestion pipelines using Python and Celery workers to parse unstructured CSV and JSON logs.",
                "Authored 60+ automated integration tests with Pytest achieving 92% service test coverage."
            ]
        }
    ],
    "projects": [
        {
            "name": "SkillGap AI",
            "link": "https://skill-gap-ai-woad.vercel.app",
            "tech": ["Python", "FastAPI", "Next.js", "Docker", "PostgreSQL"],
            "bullets": [
                "Developed open-source, deterministic career skill gap analyzer with sub-second analysis latency.",
                "Implemented two-stage NLP extraction combining spaCy phrase matching and dense vector embeddings."
            ]
        },
        {
            "name": "MicroCache Engine",
            "link": "https://github.com/2514nikhil/microcache",
            "tech": ["Python", "Redis", "Cython"],
            "bullets": [
                "Built high-concurrency LRU in-memory store supporting TTL expirations and thread-safe read snapshots."
            ]
        }
    ],
    "education": [
        {
            "school": "National Institute of Technology",
            "degree": "B.Tech",
            "field": "Computer Science and Engineering",
            "start": "2019-08",
            "end": "2023-05",
            "score": "8.8 CGPA",
            "details": [
                "Coursework: Distributed Systems, Database Management, Algorithms, Computer Networks.",
                "Lead Organizer of Annual Technical Hackathon 2022."
            ]
        }
    ],
    "certifications": [
        {
            "name": "AWS Certified Solutions Architect - Associate",
            "issuer": "Amazon Web Services",
            "date": "2023-09"
        }
    ],
    "achievements": [
        "First Prize Winner - Smart India Hackathon 2022 for AI-based document verification.",
        "Authored open-source library with over 500+ GitHub stars."
    ],
    "publications": [
        {
            "title": "Deterministic Evaluation of Skill Taxonomies in Candidate Resumes",
            "venue": "IEEE Conference on Applied NLP",
            "year": "2024",
            "link": "https://doi.org/10.1109/example.2024"
        }
    ],
    "custom_sections": [
        {
            "title": "Open Source Contributions",
            "bullets": [
                "Contributed bug fixes and documentation to FastAPI and Pydantic v2 codebases."
            ]
        }
    ]
}

example_2 = {
    "meta": {
        "template": "classic",
        "target_role": "Data Scientist"
    },
    "basics": {
        "name": "Jane Doe",
        "headline": "Machine Learning Engineer & Data Scientist",
        "email": "jane.doe@example.com",
        "phone": "+1 415 555 0199",
        "location": {
            "city": "San Francisco",
            "region_country": "United States"
        },
        "links": [
            {"platform_id": "github", "value": "janedoe-ai"},
            {"platform_id": "linkedin", "value": "jane-doe-ml"},
            {"platform_id": "kaggle", "value": "janedoe"},
            {"platform_id": "huggingface", "value": "janedoe"}
        ]
    },
    "summary": "Machine Learning Engineer specializing in computer vision and natural language processing. Experienced in training PyTorch models from scratch, fine-tuning large vision-language models, and deploying low-latency ONNX models to production.",
    "skills": [
        {"category_id": "languages", "name": "Python", "taxonomy_id": "python", "custom": False, "pinned": True, "level": "strong"},
        {"category_id": "languages", "name": "R", "taxonomy_id": "r", "custom": False, "pinned": False, "level": "comfortable"},
        {"category_id": "ml_dl_data", "name": "PyTorch", "taxonomy_id": "pytorch", "custom": False, "pinned": True, "level": "strong"},
        {"category_id": "ml_dl_data", "name": "TensorFlow", "taxonomy_id": "tensorflow", "custom": False, "pinned": False, "level": "comfortable"},
        {"category_id": "ml_dl_data", "name": "scikit-learn", "taxonomy_id": "scikit_learn", "custom": False, "pinned": True, "level": "strong"},
        {"category_id": "ml_dl_data", "name": "pandas", "taxonomy_id": "pandas", "custom": False, "pinned": True, "level": "strong"},
        {"category_id": "ml_dl_data", "name": "NumPy", "taxonomy_id": "numpy", "custom": False, "pinned": True, "level": "strong"},
        {"category_id": "ml_dl_data", "name": "Hugging Face Transformers", "taxonomy_id": "huggingface_transformers", "custom": False, "pinned": True, "level": "strong"},
        {"category_id": "data_bi_analytics", "name": "Apache Spark", "taxonomy_id": "apache_spark", "custom": False, "pinned": False, "level": "comfortable"},
        {"category_id": "cicd_vcs", "name": "Docker", "taxonomy_id": "docker", "custom": False, "pinned": False, "level": "comfortable"}
    ],
    "experience": [
        {
            "company": "NeuralMetrics AI",
            "title": "Senior Data Scientist",
            "location": "San Francisco, CA",
            "start": "2021-03",
            "end": "Present",
            "current": True,
            "bullets": [
                "Spearheaded multimodal classification pipeline improving document fraud detection accuracy by 14.2%.",
                "Optimized PyTorch inference latency by 3.5x through quantization and ONNX runtime integration.",
                "Mentored a cohort of 4 junior data analysts in statistical inference and PySpark pipelines."
            ]
        }
    ],
    "projects": [
        {
            "name": "VisionOCR Toolkit",
            "link": "https://github.com/janedoe-ai/visionocr",
            "tech": ["PyTorch", "OpenCV", "ONNX"],
            "bullets": [
                "Built lightweight end-to-end receipt OCR engine processing 40 frames/sec on CPU hardware."
            ]
        }
    ],
    "education": [
        {
            "school": "University of California, Berkeley",
            "degree": "M.S.",
            "field": "Electrical Engineering & Computer Sciences",
            "start": "2018",
            "end": "2020",
            "score": "3.92 GPA",
            "details": ["Thesis: Sparse Transformers in Dense Object Detection."]
        }
    ],
    "certifications": [
        {
            "name": "TensorFlow Developer Certificate",
            "issuer": "Google Developers",
            "date": "2020-11"
        }
    ],
    "achievements": [
        "Kaggle Competitions Grandmaster (Top 0.1% worldwide)."
    ],
    "publications": [
        {
            "title": "Efficient Quantization of Vision Transformers on Edge Hardware",
            "venue": "NeurIPS Workshop on Efficient Deep Learning",
            "year": "2022",
            "link": "https://arxiv.org/abs/2201.00000"
        }
    ],
    "custom_sections": []
}

def main():
    print("Exporting JSON Schema to docs/resume.schema.json...")
    export_json_schema(SCHEMA_FILE)

    print("Validating Example 1...")
    r1 = Resume.model_validate(example_1)
    FIXTURE_1.parent.mkdir(parents=True, exist_ok=True)
    with open(FIXTURE_1, "w", encoding="utf-8") as f:
        json.dump(r1.model_dump(), f, indent=2)

    print("Validating Example 2...")
    r2 = Resume.model_validate(example_2)
    FIXTURE_2.parent.mkdir(parents=True, exist_ok=True)
    with open(FIXTURE_2, "w", encoding="utf-8") as f:
        json.dump(r2.model_dump(), f, indent=2)

    print("Successfully exported JSON schema and verified 2 resume fixtures.")

if __name__ == "__main__":
    main()
