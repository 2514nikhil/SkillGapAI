"""Verification checks script for Phase 12A."""

import json
import random
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml.socials import build_url, extract_value

# Check 1: Entry counts per category and 20 random entries
with open('data/processed/tech_catalog.json', 'r', encoding='utf-8') as f:
    cat_data = json.load(f)

print('=' * 75)
print('CHECK 1: Tech Catalog Entry Counts per Category')
print('=' * 75)
all_skills = []
for c in cat_data['categories']:
    skills = c['skills']
    all_skills.extend([(c['name'], s) for s in skills])
    print(f"  {c['id']:<25} ({c['name']}): {len(skills):>3} entries")

print(f"\nTotal Catalog Entries: {len(all_skills)}")

print('\n' + '=' * 75)
print('CHECK 1 (cont): 20 Random Catalog Entries')
print('=' * 75)
random.seed(42)
sample_20 = random.sample(all_skills, 20)
for idx, (cat_name, s) in enumerate(sample_20, 1):
    alias_str = f" (aliases: {s['aliases']})" if s['aliases'] else ""
    print(f"{idx:>2}. [{cat_name}] {s['name']:<28} (id: {s['id']:<20} tax_id: {s['taxonomy_id']}){alias_str}")

# Check 2: build_url and extract_value results for 5 platforms
print('\n' + '=' * 75)
print('CHECK 2: Social Platform URL Build & Value Extraction (5 Platforms)')
print('=' * 75)
test_cases = [
    ('linkedin', 'johndoe', 'https://www.linkedin.com/in/johndoe?trk=public_profile'),
    ('github', '@octocat', 'https://github.com/octocat/'),
    ('leetcode', 'topcoder25', 'https://leetcode.com/u/topcoder25/'),
    ('x', '@techlead', 'https://x.com/techlead?s=20'),
    ('email', 'engineer@example.com', 'mailto:engineer@example.com?subject=Inquiry'),
]

for pid, username_in, full_url_in in test_cases:
    ext_from_user = extract_value(pid, username_in)
    url_from_user = build_url(pid, username_in)
    ext_from_url = extract_value(pid, full_url_in)
    url_from_url = build_url(pid, full_url_in)
    print(f"Platform: {pid}")
    print(f"  [From username \"{username_in}\"]:  extracted=\"{ext_from_user}\" -> built_url=\"{url_from_user}\"")
    print(f"  [From full URL \"{full_url_in}\"]: extracted=\"{ext_from_url}\" -> built_url=\"{url_from_url}\"")
    print('-' * 75)
