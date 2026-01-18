"""\
Create a scrape selection list from a JSONL wiki catalogue.

This is a helper for the workflow:
1) Run catalogue_fallout76_api.py (writes metadata/wiki_catalogue_*.jsonl)
2) Inspect/sort catalogue
3) Build a selection list (titles or urls) for scrape_fallout76.py --selection

By default this script outputs *titles* (one per line) which is the most stable.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Create a scrape selection file from a wiki catalogue JSONL")
    ap.add_argument("--catalogue", type=Path, required=True, help="Path to wiki_catalogue_*.jsonl")
    ap.add_argument("--out", type=Path, required=True, help="Output selection file (one title per line)")
    ap.add_argument("--field", type=str, default="title", help="Field to write: title or fullurl (default: title)")
    args = ap.parse_args()

    field = args.field
    if field not in {"title", "fullurl"}:
        raise SystemExit("--field must be 'title' or 'fullurl'")

    lines: list[str] = []
    seen: set[str] = set()

    for raw in args.catalogue.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            obj = json.loads(raw)
        except Exception:
            continue
        value = obj.get(field)
        if not isinstance(value, str) or not value.strip():
            continue
        value = value.strip()
        if value in seen:
            continue
        seen.add(value)
        lines.append(value)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(lines)} lines to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
