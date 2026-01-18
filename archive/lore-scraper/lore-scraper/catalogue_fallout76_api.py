"""\
Fallout 76 catalogue pull (API-first, polite crawling).

Builds a catalogue of Fallout 76-related pages by traversing category trees
using the Independent Fallout Wiki (MediaWiki) API.

Outputs are written under: <output>/metadata/
- wiki_catalogue_YYYYMMDD.jsonl  (one JSON per page)
- wiki_catalogue_run.json        (run settings, counters, resume state)
- catalogue.log                  (detailed log)

This script is intentionally API-based (not HTML scraping) to be respectful
and efficient.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import requests
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

API_BASE = "https://fallout.wiki/api.php"


DEFAULT_SEED_CATEGORIES = [
    "Fallout 76 quests",
    "Fallout 76 locations",
    "Fallout 76 characters",
    "Fallout 76 factions",
    "Fallout 76 creatures",
    "Fallout 76 events",
    "Fallout 76 holotapes",
    "Fallout 76 notes",
]


@dataclass
class CrawlStats:
    seeds_total: int = 0
    seeds_resolved: int = 0
    seeds_missing: int = 0
    categories_visited: int = 0
    pages_seen: int = 0
    pages_written: int = 0
    duplicates_skipped: int = 0
    requests: int = 0
    retries: int = 0
    throttles_429: int = 0
    maxlag_hits: int = 0


def _setup_logging(log_file: Path, level: str) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


class ApiClient:
    def __init__(
        self,
        user_agent: str,
        min_delay_seconds: float,
        timeout_seconds: float,
        maxlag: int,
    ) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": user_agent,
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
            }
        )
        self.min_delay_seconds = float(min_delay_seconds)
        self.timeout_seconds = float(timeout_seconds)
        self.maxlag = int(maxlag)
        self._last_request_time = 0.0

    def _sleep_if_needed(self) -> None:
        elapsed = time.time() - self._last_request_time
        if elapsed < self.min_delay_seconds:
            time.sleep(self.min_delay_seconds - elapsed)

    def get_json(self, params: Dict[str, Any], stats: CrawlStats) -> Dict[str, Any]:
        """GET API json with polite rate limiting and backoff."""
        params = dict(params)
        params.setdefault("format", "json")
        params.setdefault("formatversion", 2)
        params.setdefault("maxlag", str(self.maxlag))

        attempt = 0
        while True:
            attempt += 1
            self._sleep_if_needed()
            t0 = time.time()
            try:
                resp = self.session.get(API_BASE, params=params, timeout=self.timeout_seconds)
                stats.requests += 1
                self._last_request_time = time.time()

                if resp.status_code == 429:
                    stats.throttles_429 += 1
                    retry_after = resp.headers.get("Retry-After")
                    sleep_for = float(retry_after) if retry_after and retry_after.isdigit() else min(300.0, 10.0 * (2 ** (attempt - 1)))
                    sleep_for += random.uniform(0.0, 1.0)
                    logging.warning("429 rate limited; sleeping %.1fs (attempt %d)", sleep_for, attempt)
                    stats.retries += 1
                    time.sleep(sleep_for)
                    continue

                # MediaWiki maxlag can come back as 503 with a helpful body.
                if resp.status_code in {502, 503, 504}:
                    body = resp.text[:300]
                    if "maxlag" in body.lower():
                        stats.maxlag_hits += 1
                    sleep_for = min(300.0, 5.0 * (2 ** (attempt - 1))) + random.uniform(0.0, 1.0)
                    logging.warning("%s from API; sleeping %.1fs (attempt %d)", resp.status_code, sleep_for, attempt)
                    stats.retries += 1
                    time.sleep(sleep_for)
                    continue

                resp.raise_for_status()
                dt_ms = int((time.time() - t0) * 1000)
                logging.debug("API ok %dms: %s", dt_ms, params.get("action"))
                return resp.json()
            except requests.RequestException as e:
                if attempt >= 6:
                    raise
                sleep_for = min(300.0, 5.0 * (2 ** (attempt - 1))) + random.uniform(0.0, 1.0)
                logging.warning("Request error %s; sleeping %.1fs (attempt %d)", e, sleep_for, attempt)
                stats.retries += 1
                time.sleep(sleep_for)


def _title_variants(seed: str) -> list[str]:
    """Try a few likely variants before skipping."""
    normalized = seed.strip().replace("_", " ")
    variants = [normalized]

    # Common plural/singular toggles
    if normalized.endswith("s"):
        variants.append(normalized[:-1])
    else:
        variants.append(normalized + "s")

    # Underscore variant
    variants.append(normalized.replace(" ", "_"))

    # Category: prefix variants (callers add Category:)
    return list(dict.fromkeys(v for v in variants if v))


def resolve_category_title(client: ApiClient, seed: str, stats: CrawlStats) -> Optional[str]:
    """Resolve a category title (with fallbacks); return canonical category title or None."""
    for attempt_title in _title_variants(seed):
        title = f"Category:{attempt_title}"
        data = client.get_json(
            {
                "action": "query",
                "titles": title,
                "redirects": 1,
                "converttitles": 1,
            },
            stats,
        )
        pages = (data.get("query") or {}).get("pages") or []
        if pages and not pages[0].get("missing"):
            return pages[0].get("title")

    # Fallback: search within category namespace (14)
    query = seed.replace("_", " ").strip()
    search = client.get_json(
        {
            "action": "query",
            "list": "search",
            "srnamespace": 14,
            "srlimit": 5,
            "srsearch": query,
        },
        stats,
    )
    results = ((search.get("query") or {}).get("search") or [])
    for r in results:
        title = r.get("title")
        if isinstance(title, str) and title.lower().startswith("category:"):
            return title

    return None


def iter_category_members(
    client: ApiClient,
    category_title: str,
    *,
    member_type: str,
    namespace: Optional[int],
    limit: int,
    stats: CrawlStats,
) -> Iterable[Dict[str, Any]]:
    """Iterate categorymembers with continuation."""
    cmcontinue: Optional[str] = None
    while True:
        params: Dict[str, Any] = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category_title,
            "cmtype": member_type,
            "cmlimit": min(int(limit), 500),
        }
        if namespace is not None:
            params["cmnamespace"] = int(namespace)
        if cmcontinue:
            params["cmcontinue"] = cmcontinue

        data = client.get_json(params, stats)
        members = ((data.get("query") or {}).get("categorymembers") or [])
        for m in members:
            yield m

        cont = data.get("continue") or {}
        cmcontinue = cont.get("cmcontinue")
        if not cmcontinue:
            return


def batch_page_info(client: ApiClient, pageids: list[int], stats: CrawlStats) -> Dict[int, Dict[str, Any]]:
    """Fetch fullurl for pageids in one request."""
    if not pageids:
        return {}

    data = client.get_json(
        {
            "action": "query",
            "prop": "info",
            "inprop": "url",
            "pageids": "|".join(str(pid) for pid in pageids),
        },
        stats,
    )
    pages = ((data.get("query") or {}).get("pages") or [])
    out: Dict[int, Dict[str, Any]] = {}
    for p in pages:
        pid = p.get("pageid")
        if isinstance(pid, int):
            out[pid] = p
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Build Fallout 76 page catalogue via MediaWiki API")
    ap.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "lore" / "fallout76_canon",
        help="Output lore folder (default: <repo>/lore/fallout76_canon)",
    )
    ap.add_argument(
        "--seed",
        action="append",
        default=[],
        help="Seed category (repeatable). Default seeds are used if omitted.",
    )
    ap.add_argument("--max-depth", type=int, default=2, help="Category traversal depth (default: 2)")
    ap.add_argument("--max-pages", type=int, default=4000, help="Safety cap on pages written (default: 4000)")
    ap.add_argument("--batch", type=int, default=200, help="Categorymembers batch size (default: 200)")
    ap.add_argument("--delay", type=float, default=2.0, help="Seconds between requests (default: 2.0)")
    ap.add_argument("--timeout", type=float, default=60.0, help="Request timeout seconds (default: 60)")
    ap.add_argument("--maxlag", type=int, default=5, help="MediaWiki maxlag (default: 5)")
    ap.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Log level (DEBUG, INFO, WARNING, ERROR)",
    )
    ap.add_argument(
        "--user-agent",
        type=str,
        default="ESP32-AI-Radio-FO76-Catalogue/1.0 (Windows; python; contact: local)",
        help="User-Agent header identifying this crawler",
    )
    ap.add_argument(
        "--resume",
        action="store_true",
        help="Resume from <output>/metadata/wiki_catalogue_run.json and append to the existing catalogue file.",
    )
    ap.add_argument(
        "--skip-existing",
        type=Path,
        help="Path to existing catalogue JSONL - pages in this file will be skipped (for deep runs)",
    )
    args = ap.parse_args()

    out_root = args.output
    metadata = out_root / "metadata"
    metadata.mkdir(parents=True, exist_ok=True)

    run_path = metadata / "wiki_catalogue_run.json"
    log_path = metadata / "catalogue.log"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    catalogue_path = metadata / f"wiki_catalogue_{stamp}.jsonl"

    _setup_logging(log_path, args.log_level)
    logging.info("Starting FO76 catalogue pull")

    stats = CrawlStats()
    client = ApiClient(
        user_agent=args.user_agent,
        min_delay_seconds=args.delay,
        timeout_seconds=args.timeout,
        maxlag=args.maxlag,
    )

    seeds_in = args.seed if args.seed else DEFAULT_SEED_CATEGORIES
    stats.seeds_total = len(seeds_in)

    resolved_seeds: list[str] = []
    missing_seeds: list[dict[str, Any]] = []

    # Resume state
    visited_categories: set[str] = set()
    seen_pages: set[int] = set()
    existing_pages: set[int] = set()  # Pages from --skip-existing catalogue
    queue: list[tuple[str, int, str]] = []

    if args.resume and run_path.exists():
        try:
            previous = json.loads(run_path.read_text(encoding="utf-8"))
            prev_outputs = (previous.get("outputs") or {})
            prev_catalogue = prev_outputs.get("catalogue")
            if isinstance(prev_catalogue, str) and prev_catalogue:
                catalogue_path = Path(prev_catalogue)
            prev_state = previous.get("resume_state") or {}
            for c in prev_state.get("visited_categories") or []:
                if isinstance(c, str):
                    visited_categories.add(c)
            for item in prev_state.get("queue") or []:
                if (
                    isinstance(item, list)
                    and len(item) == 3
                    and isinstance(item[0], str)
                    and isinstance(item[1], int)
                    and isinstance(item[2], str)
                ):
                    queue.append((item[0], item[1], item[2]))
            # Reconstruct seen pages from existing catalogue output
            if catalogue_path.exists():
                for raw in catalogue_path.read_text(encoding="utf-8").splitlines():
                    try:
                        obj = json.loads(raw)
                    except Exception:
                        continue
                    pid = obj.get("pageid")
                    if isinstance(pid, int):
                        seen_pages.add(pid)
            logging.info(
                "Resuming: visited_categories=%d queued=%d seen_pages=%d catalogue=%s",
                len(visited_categories),
                len(queue),
                len(seen_pages),
                catalogue_path,
            )
        except Exception as e:
            logging.warning("Resume requested but state load failed; starting fresh: %s", e)
            visited_categories.clear()
            seen_pages.clear()
            queue.clear()

    # Load existing pages to skip (if --skip-existing provided)
    if args.skip_existing:
        skip_path = args.skip_existing
        if skip_path.exists():
            logging.info("Loading existing pages from: %s", skip_path)
            for line in skip_path.read_text(encoding="utf-8").splitlines():
                try:
                    obj = json.loads(line)
                    pid = obj.get("pageid")
                    if isinstance(pid, int):
                        existing_pages.add(pid)
                except Exception:
                    continue
            logging.info("Loaded %d existing page IDs to skip", len(existing_pages))
        else:
            logging.warning("Skip-existing file not found: %s", skip_path)

    # Only resolve seeds if not resuming with an existing queue.
    if not queue:
        for seed in seeds_in:
            resolved = resolve_category_title(client, seed, stats)
            if resolved:
                logging.info("Seed category resolved: %s -> %s", seed, resolved)
                resolved_seeds.append(resolved)
                stats.seeds_resolved += 1
            else:
                logging.warning("Seed category missing: %s", seed)
                missing_seeds.append({"seed": seed, "attempted_variants": _title_variants(seed)})
                stats.seeds_missing += 1

        queue = [(cat, 0, cat) for cat in resolved_seeds]

    def flush_batch(page_batch: list[int], page_context: dict[int, dict[str, Any]]) -> None:
        nonlocal out_f, pbar
        if not page_batch or stats.pages_written >= int(args.max_pages):
            return

        remaining = int(args.max_pages) - stats.pages_written
        if remaining <= 0:
            return

        batch = page_batch[:remaining]
        info = batch_page_info(client, batch, stats)
        for pageid in batch:
            pinfo = info.get(pageid) or {"pageid": pageid}
            record = {
                "pageid": pageid,
                "title": pinfo.get("title"),
                "fullurl": pinfo.get("fullurl"),
                "ns": pinfo.get("ns"),
                **page_context.get(pageid, {}),
            }
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
            stats.pages_written += 1
            if pbar:
                pbar.update(1)

    open_mode = "a" if args.resume and catalogue_path.exists() else "w"
    
    # Setup progress bar
    pbar = None
    if HAS_TQDM:
        pbar = tqdm(total=int(args.max_pages), desc="Cataloguing", unit="pages", 
                    initial=stats.pages_written, dynamic_ncols=True)
    
    with catalogue_path.open(open_mode, encoding="utf-8") as out_f:
        while queue and stats.pages_written < int(args.max_pages):
            category_title, depth, seed_root = queue.pop(0)
            if category_title in visited_categories:
                continue
            visited_categories.add(category_title)
            stats.categories_visited += 1

            if pbar:
                pbar.set_postfix({"cat": category_title[:40], "depth": f"{depth}/{int(args.max_depth)}"})
            logging.info("Category (%d/%d): %s", depth, int(args.max_depth), category_title)

            # Enqueue subcategories
            if depth < int(args.max_depth):
                for m in iter_category_members(
                    client,
                    category_title,
                    member_type="subcat",
                    namespace=None,
                    limit=int(args.batch),
                    stats=stats,
                ):
                    title = m.get("title")
                    if isinstance(title, str) and title.lower().startswith("category:"):
                        if title not in visited_categories:
                            queue.append((title, depth + 1, seed_root))

            # Pull page members (main namespace only)
            page_batch: list[int] = []
            page_context: dict[int, dict[str, Any]] = {}

            for m in iter_category_members(
                client,
                category_title,
                member_type="page",
                namespace=0,
                limit=int(args.batch),
                stats=stats,
            ):
                if stats.pages_written >= int(args.max_pages):
                    break
                pid = m.get("pageid")
                if not isinstance(pid, int):
                    continue
                stats.pages_seen += 1
                if pid in seen_pages:
                    continue
                # Skip if in existing catalogue (from --skip-existing)
                if pid in existing_pages:
                    stats.duplicates_skipped += 1
                    continue
                seen_pages.add(pid)
                page_context[pid] = {"seed": seed_root, "category": category_title, "depth": depth}
                page_batch.append(pid)

                # Flush in smaller chunks so --max-pages can stop promptly.
                remaining = int(args.max_pages) - stats.pages_written
                flush_threshold = min(50, max(1, remaining))
                if len(page_batch) >= flush_threshold:
                    flush_batch(page_batch, page_context)
                    page_batch.clear()
                    page_context.clear()
                    if stats.pages_written >= int(args.max_pages):
                        break

            # Flush remaining
            if page_batch and stats.pages_written < int(args.max_pages):
                flush_batch(page_batch, page_context)

            # Persist run state every category
            run_state = {
                "started_at": stamp,
                "finished_at": datetime.now().isoformat(),
                "api_base": API_BASE,
                "settings": {
                    "output": str(out_root),
                    "max_depth": int(args.max_depth),
                    "max_pages": int(args.max_pages),
                    "batch": int(args.batch),
                    "delay": float(args.delay),
                    "timeout": float(args.timeout),
                    "maxlag": int(args.maxlag),
                    "user_agent": args.user_agent,
                },
                "seeds": {
                    "input": seeds_in,
                    "resolved": resolved_seeds,
                    "missing": missing_seeds,
                },
                "stats": stats.__dict__,
                "resume_state": {
                    "visited_categories": sorted(visited_categories),
                    "queue": [[c, d, s] for (c, d, s) in queue],
                    "seen_pages_count": len(seen_pages),
                },
                "outputs": {
                    "catalogue": str(catalogue_path),
                    "log": str(log_path),
                },
            }
            run_path.write_text(json.dumps(run_state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if pbar:
        pbar.close()

    logging.info("Done. Pages written=%d categories=%d", stats.pages_written, stats.categories_visited)
    logging.info("Catalogue: %s", catalogue_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
