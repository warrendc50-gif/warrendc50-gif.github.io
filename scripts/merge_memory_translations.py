"""Merge translated fields into the Memory board data files.

usage: python scripts/merge_memory_translations.py <translations.json> <board-key>

<translations.json> maps an item's url to {"headline_en", "summary_en", "headline_ja", "summary_ja"}.
Only those four fields are written, and only onto items whose url matches; nothing else changes.
Prints how many items were updated and which urls had no matching item.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "memory"
FIELDS = ("headline_en", "summary_en", "headline_ja", "summary_ja")


def main(path: str, board: str) -> int:
    tr = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    file = DATA / f"{board}.json"
    data = json.loads(file.read_text(encoding="utf-8"))
    items = data["items"] if isinstance(data, dict) else data
    by_url = {i["url"]: i for i in items}
    updated = 0
    for url, fields in tr.items():
        item = by_url.get(url)
        if item is None:
            print(f"   - no item for {url}")
            continue
        for f in FIELDS:
            if fields.get(f):
                item[f] = fields[f]
        updated += 1
    file.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"[{board}] updated {updated} of {len(items)} items")
    return updated


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
