# FO76 Lore Catalogue + Scrape (API-first, no LLM)

This repo now supports a **two-phase** workflow for building a Fallout 76 lore dataset:

1) **Catalogue** FO76 pages via the Fallout Fandom **MediaWiki API** (polite, resumable)
2) **Inspect / sort** the catalogue locally
3) **Scrape only selected pages** into `lore/fallout76_canon/`
4) Run **deterministic canon normalization** (`canon_fixups.py`) after you confirm the scrape looks correct

Nothing in this workflow uses a local LLM.

Note: The previous Ollama-based validator (`review_entities_llm.py`) has been removed. Validation is now strictly:
- API-based catalogue + local inspection
- Deterministic normalization via `canon_fixups.py`

---

## What was added/changed

### New scripts

- [tools/lore-scraper/catalogue_fallout76_api.py](tools/lore-scraper/catalogue_fallout76_api.py)
  - Builds a FO76 page catalogue by traversing category trees via the API.
  - Writes outputs under `lore/fallout76_canon/metadata/`.
  - **Skips and logs** missing categories.
  - Uses conservative defaults (delay, `maxlag`, retries/backoff).

- [tools/lore-scraper/selection_from_catalogue.py](tools/lore-scraper/selection_from_catalogue.py)
  - Converts a catalogue JSONL into a `scrape_selection.txt` file (one title per line).

### Updated scripts

- [tools/lore-scraper/scrape_fallout76.py](tools/lore-scraper/scrape_fallout76.py)
  - Added `--selection` mode (titles/URLs, one per line) to scrape exactly what you picked.
  - Added `metadata/scrape.log` logging inside the lore output.
  - Added API title resolution (redirects/missing detection) so 404s become **skip+log** instead of repeated failures.
  - Added `--reset` with automatic zip backup (unless `--no-backup`).

- [tools/lore-scraper/canon_fixups.py](tools/lore-scraper/canon_fixups.py)
  - Now skips any JSON under `lore/fallout76_canon/metadata/` so catalogue/run-state JSON files are never modified.

Canon normalization notes: see [tools/lore-scraper/README_fixups.md](tools/lore-scraper/README_fixups.md).

---

## Outputs (all inside lore output)

These scripts write to:

- `lore/fallout76_canon/metadata/wiki_catalogue_YYYYMMDD_HHMMSS.jsonl`
  - One JSON object per line (JSONL)
  - Fields include: `pageid`, `title`, `fullurl`, `seed`, `category`, `depth`

- `lore/fallout76_canon/metadata/wiki_catalogue_run.json`
  - Run settings, resolved/missing seed categories, counters

- `lore/fallout76_canon/metadata/catalogue.log`
  - Detailed crawl log (good for diagnosing throttling/missing categories)

- `lore/fallout76_canon/metadata/scrape.log`
  - Detailed per-page scrape log for the HTML scrape step

---

## Step 1: Build the catalogue (API)

From repo root:

```powershell
python .\tools\lore-scraper\catalogue_fallout76_api.py --max-pages 4000 --max-depth 2 --delay 2.0 --log-level INFO
```

Notes:
- This uses the **free** API endpoint: `https://fallout.fandom.com/api.php`
- Defaults are intentionally polite:
  - single-threaded
  - `--delay 2.0` seconds between requests
  - `maxlag=5`
  - exponential backoff on 429/5xx
- If a seed category is missing, it is **skipped** and logged.

If you want a bigger catalogue:

```powershell
python .\tools\lore-scraper\catalogue_fallout76_api.py --max-pages 20000 --max-depth 2 --delay 2.0 --log-level INFO
```

---

## Step 2: Inspect/sort locally

Open the newest `wiki_catalogue_*.jsonl` under:

- `lore/fallout76_canon/metadata/`

You can sort/filter however you like (PowerShell, Python, Excel).

---

## Step 3: Create a selection list

Convert a catalogue into a plain text selection list (titles):

```powershell
python .\tools\lore-scraper\selection_from_catalogue.py \
  --catalogue .\lore\fallout76_canon\metadata\wiki_catalogue_YYYYMMDD_HHMMSS.jsonl \
  --out .\lore\fallout76_canon\metadata\scrape_selection.txt
```

The output file is one title per line. You may edit it manually (delete noisy entries, etc.).

---

## Step 4: Scrape selected pages (HTML scrape, no LLM)

Scrape only the pages in your selection file.

Recommended: scrape first **without fixups**, so you can verify the raw scrape quality.

```powershell
python .\tools\lore-scraper\scrape_fallout76.py --reset --yes --selection .\lore\fallout76_canon\metadata\scrape_selection.txt --no-fixups
```

If you’re happy with the scraped output, you can let it run fixups automatically by removing `--no-fixups`:

```powershell
python .\tools\lore-scraper\scrape_fallout76.py --reset --yes --selection .\lore\fallout76_canon\metadata\scrape_selection.txt
```

Troubleshooting:
- Check `lore/fallout76_canon/metadata/scrape.log` for missing titles / 404s / non-FO76 content skips.

---

## Step 5: Run canon fixups (after inspection)

If you scraped with `--no-fixups`, run fixups manually:

```powershell
python .\tools\lore-scraper\canon_fixups.py
```

---

## Seed categories used by default

The catalogue script defaults to these (and will skip+log any that don’t exist):

- Fallout 76 quests
- Fallout 76 locations
- Fallout 76 characters
- Fallout 76 factions
- Fallout 76 creatures
- Fallout 76 events
- Fallout 76 holotapes
- Fallout 76 notes

---

## Respectful crawling knobs

If you want to be even more conservative:

- Increase delay: `--delay 3.0`
- Reduce batch size: `--batch 100`
- Keep depth low: `--max-depth 1` (less complete, but very gentle)

If you see throttling (429) or maxlag warnings in `catalogue.log`, slow down and resume later.
