"""Phase 1 — Download every attachment listed in inventory.csv.

For each attachment_block_id, GET /v1/blocks/{id} → fresh signed URL (1h TTL).
Saves to _migration/raw/{page_id}__{slug}.{ext}
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

NOTION_VERSION = "2022-06-28"
ROOT = Path(__file__).resolve().parent.parent
CSV_IN = ROOT / "inventory.csv"
RAW_DIR = ROOT / "raw"


def _load_dotenv():
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()



def _api_get(path: str) -> dict:
    token = os.environ["NOTION_TOKEN"]
    req = urllib.request.Request(f"https://api.notion.com/v1{path}", method="GET")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Notion-Version", NOTION_VERSION)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def slugify(s: str) -> str:
    s = re.sub(r"[^\w가-힣\-]+", "_", s.strip())
    return s[:60].strip("_") or "untitled"


def download(url: str, dest: Path):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=120) as r, dest.open("wb") as f:
        while chunk := r.read(1 << 16):
            f.write(chunk)


def main():
    if "NOTION_TOKEN" not in os.environ:
        print("ERROR: NOTION_TOKEN env var not set", file=sys.stderr)
        sys.exit(2)

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    with CSV_IN.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    total = sum(int(r["attachment_count"]) for r in rows)
    print(f"Downloading {total} files across {len(rows)} pages…")

    done, skipped, failed = 0, 0, 0
    for r in rows:
        if not r["attachment_block_ids"]:
            continue
        page_id_clean = r["page_id"].replace("-", "")
        block_ids = r["attachment_block_ids"].split("|")
        names = r["attachment_filenames"].split("|")
        for idx, (bid, raw_name) in enumerate(zip(block_ids, names)):
            ext = raw_name.rsplit(".", 1)[-1].lower() if "." in raw_name else "pdf"
            slug = slugify(r["title"]) or page_id_clean[:8]
            suffix = f"__{idx}" if len(block_ids) > 1 else ""
            dest = RAW_DIR / f"{page_id_clean}_{slug}{suffix}.{ext}"
            if dest.exists() and dest.stat().st_size > 0:
                skipped += 1
                continue
            try:
                blk = _api_get(f"/blocks/{bid}")
                t = blk.get("type")
                payload = blk.get(t, {})
                file_obj = payload.get("file") or payload.get("external") or {}
                signed = file_obj.get("url")
                if not signed:
                    print(f"  ! no URL for block {bid} ({raw_name})")
                    failed += 1
                    continue
                download(signed, dest)
                size = dest.stat().st_size
                print(f"  ✓ {dest.name}  ({size/1024:.0f} KB)")
                done += 1
            except Exception as e:
                print(f"  ✗ {raw_name}: {e}")
                failed += 1

    print(f"\nDone: {done} downloaded, {skipped} cached, {failed} failed")


if __name__ == "__main__":
    main()
