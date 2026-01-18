# Canon Fixups

This folder contains one-off scripts to normalize the scraped FO76 lore JSON files.

## Apply FO76 canon fixups

From repo root:

```bash
python tools/lore-scraper/canon_fixups.py
```

What it does:
- Removes LLM contamination fields (e.g. `llm_log`)
- Normalizes `temporal.active_during` to the FO76 timeline (2077–2103)
- Enforces Julie (2102) knowledge constraints (e.g., Foundation/Crater/Meg are 2103+)
- Adds `verification.validation_notes` with canon-focused notes
