"""Unified build and orchestration script for SkillGap.

Runs data verification, taxonomy generation, role profiling, and course indexing
with step resumption (--force to override) and optional evaluation suite (--with-eval).
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("skillgap.build_all")


def run_cmd(cmd: list[str], description: str) -> None:
    """Execute a command as a subprocess, checking for errors."""
    logger.info(f"==> {description}...")
    result = subprocess.run(cmd, cwd=str(BASE_DIR))
    if result.returncode != 0:
        logger.error(f"Command failed with exit code {result.returncode}: {' '.join(cmd)}")
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description="SkillGap Unified Build and Evaluation Pipeline")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Recompute all steps and overwrite existing processed artifacts",
    )
    parser.add_argument(
        "--with-eval",
        action="store_true",
        help="Run evaluation scripts and generate summary tables in eval/results/ after building",
    )
    args = parser.parse_args()

    python_bin = sys.executable

    logger.info("=" * 80)
    logger.info("SKILLGAP UNIFIED BUILD PIPELINE")
    logger.info(f"Working Directory: {BASE_DIR}")
    logger.info(f"Force Recompute: {args.force}")
    logger.info(f"Run Evaluations: {args.with_eval}")
    logger.info("=" * 80)

    # 1. Step 1: Raw Data Check
    logger.info("\n--- [Step 1/4] Checking Raw Datasets ---")
    data_check_script = BASE_DIR / "scripts" / "check_data.py"
    data_ready = subprocess.run([python_bin, str(data_check_script)], cwd=str(BASE_DIR)).returncode == 0
    if not data_ready:
        logger.warning(
            "Some raw data files are missing. If running for development or testing, "
            "make sure data/raw/ or tests/fixtures are configured."
        )

    # 2. Step 2: Taxonomy & Skill Embeddings
    skills_json = settings.PROCESSED_DATA_DIR / "skills.json"
    skill_emb = settings.PROCESSED_DATA_DIR / "skill_embeddings.npy"
    skill_ids = settings.PROCESSED_DATA_DIR / "skill_ids.json"

    logger.info("\n--- [Step 2/4] Skills Taxonomy & Dense Embeddings ---")
    if not args.force and skills_json.exists() and skill_emb.exists() and skill_ids.exists():
        logger.info(f"[SKIP] Taxonomy artifacts already exist at {skills_json}. Use --force to rebuild.")
    else:
        build_tax_script = BASE_DIR / "scripts" / "build_taxonomy.py"
        run_cmd([python_bin, str(build_tax_script)], "Building skills taxonomy and embeddings")

    # 3. Step 3: Role Profiles & Embeddings
    profiles_json = settings.PROCESSED_DATA_DIR / "role_profiles.json"
    role_emb = settings.PROCESSED_DATA_DIR / "role_embeddings.npy"

    logger.info("\n--- [Step 3/4] Role Demand Profiles & Role Embeddings ---")
    if not args.force and profiles_json.exists() and role_emb.exists():
        logger.info(f"[SKIP] Role profiles already exist at {profiles_json}. Use --force to rebuild.")
    else:
        build_prof_script = BASE_DIR / "scripts" / "build_all_24_kaggle_roles.py"
        if not build_prof_script.exists():
            build_prof_script = BASE_DIR / "scripts" / "build_profiles.py"
        run_cmd([python_bin, str(build_prof_script)], "Extracting demand profiles from postings/resumes")

    # 4. Step 4: Course Recommendation Index
    courses_json = settings.PROCESSED_DATA_DIR / "courses.json"
    course_emb = settings.PROCESSED_DATA_DIR / "course_embeddings.npy"

    logger.info("\n--- [Step 4/4] Course Recommendation Catalog & Index ---")
    if not args.force and courses_json.exists() and course_emb.exists():
        logger.info(f"[SKIP] Course index already exists at {courses_json}. Use --force to rebuild.")
    else:
        build_course_script = BASE_DIR / "scripts" / "build_course_index.py"
        run_cmd([python_bin, str(build_course_script)], "Building course recommendation index and embeddings")

    # 5. Optional Step 5: Evaluations
    if args.with_eval:
        logger.info("\n--- [Step 5/5] Running Model Evaluation Suite ---")
        eval_scripts = [
            ("eval/extract_eval.py", "Skill Extraction Benchmark"),
            ("eval/match_eval.py", "Role Matching Ablation Study"),
            ("eval/rec_eval.py", "Course Recommendation Evaluation"),
            ("eval/sensitivity_eval.py", "Hyperparameter Sensitivity Sweeps"),
            ("eval/robustness_eval.py", "Format & Section Robustness Checks"),
            ("scripts/make_report_tables.py", "Compiling Markdown & CSV Report Tables"),
        ]
        for rel_path, desc in eval_scripts:
            script_file = BASE_DIR / rel_path
            if script_file.exists():
                run_cmd([python_bin, str(script_file)], desc)
            else:
                logger.warning(f"Evaluation script not found: {script_file}")

        logger.info("\nEvaluation tables successfully written to eval/results/")

    logger.info("\n" + "=" * 80)
    logger.info("SkillGap build completed successfully!")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
