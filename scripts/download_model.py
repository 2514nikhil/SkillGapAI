"""Download sentence-transformers/all-MiniLM-L6-v2 directly using requests."""

import os
import sys
from pathlib import Path
import requests

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
FILES = [
    "config.json",
    "modules.json",
    "config_sentence_transformers.json",
    "sentence_bert_config.json",
    "model.safetensors",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "vocab.txt",
]

CACHE_DIR = Path.home() / ".cache" / "huggingface" / "hub" / f"models--{MODEL_ID.replace('/', '--')}"
SNAPSHOT_DIR = CACHE_DIR / "snapshots" / "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


def download():
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    base_url = f"https://huggingface.co/{MODEL_ID}/resolve/main"

    for filename in FILES:
        dest_path = SNAPSHOT_DIR / filename
        if dest_path.is_file() and dest_path.stat().st_size > 0:
            print(f"Already cached: {filename} ({dest_path.stat().st_size} bytes)")
            continue

        url = f"{base_url}/{filename}"
        print(f"Downloading {filename} from {url}...")
        resp = requests.get(url, stream=True, timeout=60)
        resp.raise_for_status()

        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = (downloaded / total) * 100
                        print(f"\r  {downloaded}/{total} bytes ({pct:.1f}%)", end="", flush=True)
        print(f"\nSaved {filename} ({dest_path.stat().st_size} bytes)")

    print("\nAll model files downloaded successfully!")


if __name__ == "__main__":
    download()
