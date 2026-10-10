"""Interactive Terminal Annotation Helper for Skill Extraction Ground Truth.

Displays document text, runs Stage A baseline extraction to pre-populate candidate
skills, allows the user to accept, remove, or add canonical skill IDs, and writes
the ground-truth annotations to eval/labeled/benchmark.json.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

# Add parent directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import settings
from ml.extract import extract_baseline
from ml.taxonomy import taxonomy

BENCHMARK_FILE = BASE_DIR / "eval" / "labeled" / "benchmark.json"


def load_benchmark() -> List[Dict[str, Any]]:
    if BENCHMARK_FILE.is_file():
        with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_benchmark(data: List[Dict[str, Any]]) -> None:
    BENCHMARK_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BENCHMARK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(data)} labeled documents to {BENCHMARK_FILE}")


def annotate_document(doc_id: str, doc_type: str, title: str, text: str) -> Optional[List[str]]:
    print("\n" + "=" * 80)
    print(f"DOC ID: {doc_id} | TYPE: {doc_type} | TITLE: {title}")
    print("=" * 80)
    print(text.strip())
    print("-" * 80)

    # Pre-populate using Stage A
    baseline_hits = extract_baseline(text)
    prefilled_skills: Set[str] = {h.skill_id for h in baseline_hits}

    current_skills: Set[str] = set(prefilled_skills)

    while True:
        print("\nCurrent Skills:")
        if not current_skills:
            print("  (None)")
        else:
            for s in sorted(current_skills):
                info = taxonomy.get_skill(s)
                name = info["name"] if info else s
                print(f"  + {name} (id: {s})")

        print("\nCommands:")
        print("  [Enter] or 'ok'   : Save current skills and proceed")
        print("  '+ <skill>'       : Add a skill by name or ID (e.g., '+ docker')")
        print("  '- <skill>'       : Remove a skill by name or ID (e.g., '- bash')")
        print("  's'               : Skip document without saving")
        print("  'q'               : Quit annotation")

        choice = input("\nAction > ").strip()

        if choice.lower() in ("", "ok", "a"):
            return sorted(current_skills)
        elif choice.lower() == "s":
            print("Skipped.")
            return None
        elif choice.lower() == "q":
            print("Quitting.")
            sys.exit(0)
        elif choice.startswith("+"):
            term = choice[1:].strip()
            sid = taxonomy.find_skill_id(term)
            if sid:
                current_skills.add(sid)
                print(f"Added '{sid}'")
            else:
                print(f"Could not find skill '{term}' in taxonomy. Try a different alias.")
        elif choice.startswith("-"):
            term = choice[1:].strip()
            sid = taxonomy.find_skill_id(term) or term.lower().replace(" ", "_")
            if sid in current_skills:
                current_skills.remove(sid)
                print(f"Removed '{sid}'")
            else:
                print(f"Skill '{term}' is not in current list.")
        else:
            print(f"Unrecognized command: '{choice}'")


def main() -> None:
    taxonomy.load()
    benchmark_data = load_benchmark()
    existing_ids = {d["doc_id"] for d in benchmark_data}

    print(f"Loaded existing benchmark dataset ({len(benchmark_data)} documents).")

    # If user provided a raw text file or path as argument
    if len(sys.argv) > 1:
        target_path = Path(sys.argv[1])
        if target_path.is_file():
            text = target_path.read_text(encoding="utf-8")
            doc_id = target_path.stem
            skills = annotate_document(doc_id, "resume", target_path.name, text)
            if skills is not None:
                record = {
                    "doc_id": doc_id,
                    "doc_type": "resume",
                    "title": target_path.name,
                    "text": text,
                    "ground_truth_skills": skills,
                }
                benchmark_data = [d for d in benchmark_data if d["doc_id"] != doc_id] + [record]
                save_benchmark(benchmark_data)
            return

    print("To annotate a custom document, run: python scripts/annotate.py <path_to_resume_or_jd>")
    print("Example: python scripts/annotate.py tests/fixtures/sample_resume.txt")


if __name__ == "__main__":
    main()
