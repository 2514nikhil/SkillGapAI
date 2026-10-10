"""Demonstration script showing skill extraction on 3 sample resumes with highlighted skills."""

import sys
from pathlib import Path

# Add parent directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml.extract import extract_skills
from ml.taxonomy import taxonomy

SAMPLE_RESUMES = [
    {
        "candidate": "Alex Rivera",
        "role": "Senior Backend Engineer",
        "text": (
            "Alex Rivera | alex.rivera@example.com\n\n"
            "TECHNICAL SKILLS\n"
            "Languages: Python, Go, SQL, Bash\n"
            "Frameworks: FastAPI, Django, Flask\n"
            "Databases: PostgreSQL, Redis, MongoDB\n"
            "DevOps: Docker, Kubernetes, CI/CD, Git, Linux\n\n"
            "PROFESSIONAL EXPERIENCE\n"
            "Senior Backend Developer | CloudScale Systems (2021 - Present)\n"
            "- Designed and implemented scalable asynchronous microservices using Python and FastAPI.\n"
            "- Improved database latency by 45% through PostgreSQL query optimization and Redis caching.\n"
            "- Led migration of legacy monolithic workloads to Docker containers managed on Kubernetes.\n"
            "- Established automated CI/CD deployment pipelines using GitHub Actions.\n\n"
            "EDUCATION\n"
            "B.S. in Computer Science | State University"
        ),
    },
    {
        "candidate": "Priya Sharma",
        "role": "Machine Learning Engineer",
        "text": (
            "Priya Sharma | priya.sharma@example.com\n\n"
            "SUMMARY\n"
            "Machine Learning Engineer with 4 years of experience delivering end-to-end AI applications.\n\n"
            "CORE COMPETENCIES\n"
            "Machine Learning, Deep Learning, Natural Language Processing, Computer Vision\n"
            "Frameworks: PyTorch, TensorFlow, scikit-learn, Hugging Face, spaCy\n"
            "Data & Tools: Pandas, NumPy, SQL, Docker, MLOps, MLflow, AWS\n\n"
            "WORK EXPERIENCE\n"
            "AI Engineer | Insight AI Labs (2020 - Present)\n"
            "- Trained Transformer architectures with PyTorch and Hugging Face for automated document classification.\n"
            "- Built tabular prediction pipelines using scikit-learn and XGBoost for churn forecasting.\n"
            "- Packaged model inference servers using FastAPI and deployed with Docker on AWS.\n"
            "- Monitored experiment metrics and model versioning utilizing MLflow.\n\n"
            "EDUCATION\n"
            "M.S. in Artificial Intelligence | Tech Institute"
        ),
    },
    {
        "candidate": "Marcus Chen",
        "role": "Full Stack React & Node Developer",
        "text": (
            "Marcus Chen | marcus.chen@example.com\n\n"
            "TECHNICAL PROFICIENCIES\n"
            "Frontend: React, Next.js, TypeScript, JavaScript, HTML5, CSS3, Tailwind CSS, Redux\n"
            "Backend: Node.js, Express.js, REST API, GraphQL\n"
            "Tools: Git, Figma, Webpack, Postman\n\n"
            "EXPERIENCE\n"
            "Full Stack Developer | NextGen Apps (2021 - Present)\n"
            "- Developed responsive web applications using React and TypeScript styled with Tailwind CSS.\n"
            "- Implemented server-side rendering and static page generation using Next.js.\n"
            "- Architected backend REST APIs and GraphQL endpoints using Node.js and Express.js.\n"
            "- Collaborated closely with product designers using Figma prototypes.\n\n"
            "EDUCATION\n"
            "B.S. in Software Engineering | City College"
        ),
    },
]


def highlight_skills_in_text(text: str, hits: list) -> str:
    """Insert visual highlights around extracted skill spans."""
    # Sort hits in reverse order of start position to prevent index drift
    sorted_hits = sorted(hits, key=lambda h: h.start, reverse=True)
    highlighted = text

    for h in sorted_hits:
        start, end = h.start, h.end
        target_span = highlighted[start:end]
        replacement = f"**[{h.skill_id.upper()}: {target_span}]**"
        highlighted = highlighted[:start] + replacement + highlighted[end:]

    return highlighted


def main():
    taxonomy.load()
    print("\n" + "=" * 80)
    print("PHASE 3 EXTRACTION DEMONSTRATION ON 3 SAMPLE RESUMES")
    print("=" * 80)

    for i, sample in enumerate(SAMPLE_RESUMES, 1):
        print(f"\n--- RESUME {i}: {sample['candidate']} ({sample['role']}) ---")
        res = extract_skills(sample["text"], mode="hybrid")

        print(f"Extracted {len(res.skills)} Unique Skills:")
        print("  " + ", ".join(res.skills))

        print("\nDocument with Highlighted Skills:")
        print("-" * 60)
        highlighted = highlight_skills_in_text(sample["text"], res.hits)
        print(highlighted)
        print("-" * 60)

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
