import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml.taxonomy import normalize_skill_name

skills_file = BASE_DIR / "data" / "processed" / "skills.json"
with open(skills_file, "r", encoding="utf-8") as f:
    skills = json.load(f)

canonical_names = {normalize_skill_name(s["name"]): sid for sid, s in skills.items()}

removed = 0
for sid, data in list(skills.items()):
    clean_aliases = []
    for a in data.get("aliases", []):
        norm_a = normalize_skill_name(a)
        if norm_a in canonical_names and canonical_names[norm_a] != sid:
            print(f"Removing colliding alias '{a}' from '{sid}' (collides with {canonical_names[norm_a]})")
            removed += 1
        else:
            clean_aliases.append(a)
    skills[sid]["aliases"] = clean_aliases

with open(skills_file, "w", encoding="utf-8") as f:
    json.dump(skills, f, indent=2)

print(f"Removed {removed} colliding aliases from skills.json.")
