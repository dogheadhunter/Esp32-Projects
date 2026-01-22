"""
ChromaDB False Positive Audit Script

Scans ChromaDB for potential false positives in quest content.
Identifies mechanics pages, meta content, and item pages that may have
been incorrectly tagged as quest content.

Phase 1B-R, Task 1B-R.2.4
"""

import sys
import os
import re
from typing import Dict, List, Any
from collections import defaultdict

# Add paths for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "tools", "wiki_to_chromadb"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "tools", "script-generator"))

from chromadb_ingest import ChromaDBIngestor


# False positive patterns (matching StoryExtractor.QUEST_EXCLUDE_TITLE_PATTERNS)
FALSE_POSITIVE_PATTERNS = {
    "Mechanics": r"^Fallout \d+ (Perks|Stats|Items|Weapons|Armor|Achievements|Quests)$",
    "Walkthrough": r"^Walkthrough:",
    "Category": r"^Category:",
    "List": r"^List of",
    "Template": r"^Template:",
    "Portal": r"^Portal:",
    "Perk Items": r".*\(perk\)$",
    "Weapon Items": r".*\(weapon\)$",
    "Armor Items": r".*\(armor\)$",
    "Generic Items": r".*\(item\)$",
}


def audit_false_positives(chroma_db_path: str = "chroma_db") -> Dict[str, Any]:
    """
    Audit ChromaDB for false positives in quest content.
    
    Args:
        chroma_db_path: Path to ChromaDB
    
    Returns:
        Dict with audit results
    """
    print(f"\n{'=' * 70}")
    print("ChromaDB False Positive Audit")
    print(f"{'=' * 70}\n")
    
    # Load ChromaDB
    try:
        ingestor = ChromaDBIngestor(chroma_db_path)
        print(f"✓ ChromaDB loaded: {ingestor.collection.count()} total chunks\n")
    except Exception as e:
        print(f"✗ Failed to load ChromaDB: {e}")
        return {"success": False, "error": str(e)}
    
    # Query for quest-tagged content
    print("Querying quest-tagged content...")
    try:
        results = ingestor.collection.query(
            query_texts=["quest objective reward walkthrough"],
            n_results=500,
            where={
                "$or": [
                    {"infobox_type": "infobox quest"},
                    {"content_type": "quest"},
                    {"content_type": "questline"}
                ]
            }
        )
    except Exception as e:
        print(f"✗ Query failed: {e}")
        return {"success": False, "error": str(e)}
    
    if not results or not results.get("ids"):
        print("✗ No quest content found")
        return {"success": False, "error": "No quest content found"}
    
    # Extract unique titles
    titles = set()
    title_chunks: Dict[str, int] = defaultdict(int)
    
    num_results = len(results["ids"][0]) if results.get("ids") else 0
    for idx in range(num_results):
        metadata = results.get("metadatas", [{}])[0][idx] if results.get("metadatas") else {}
        title = metadata.get("wiki_title", "unknown")
        titles.add(title)
        title_chunks[title] += 1
    
    total_chunks = num_results
    total_titles = len(titles)
    
    print(f"✓ Found {total_chunks} quest-tagged chunks from {total_titles} unique titles\n")
    
    # Check for false positives
    false_positives: Dict[str, List[str]] = defaultdict(list)
    false_positive_chunk_count = 0
    
    for title in titles:
        for category, pattern in FALSE_POSITIVE_PATTERNS.items():
            if re.match(pattern, title):
                false_positives[category].append(title)
                false_positive_chunk_count += title_chunks[title]
                break
    
    # Generate report
    print(f"{'=' * 70}")
    print("FALSE POSITIVE ANALYSIS")
    print(f"{'=' * 70}\n")
    
    if not false_positives:
        print("✅ No false positives detected!\n")
        false_positive_rate = 0.0
    else:
        total_false_positive_titles = sum(len(titles) for titles in false_positives.values())
        false_positive_rate = (false_positive_chunk_count / total_chunks) * 100 if total_chunks > 0 else 0
        
        print(f"False Positive Categories:\n")
        for category, fp_titles in sorted(false_positives.items()):
            print(f"  {category}: {len(fp_titles)} titles")
            for title in sorted(fp_titles)[:5]:  # Show first 5
                chunks = title_chunks[title]
                print(f"    - {title} ({chunks} chunks)")
            if len(fp_titles) > 5:
                print(f"    ... and {len(fp_titles) - 5} more")
            print()
        
        print(f"Total false positive titles: {total_false_positive_titles}/{total_titles} ({total_false_positive_titles/total_titles*100:.1f}%)")
        print(f"Total false positive chunks: {false_positive_chunk_count}/{total_chunks} ({false_positive_rate:.1f}%)\n")
    
    # Determine pass/fail
    print(f"{'=' * 70}")
    print("AUDIT RESULT")
    print(f"{'=' * 70}\n")
    
    if false_positive_rate < 5.0:
        print(f"✅ PASS - False positive rate {false_positive_rate:.1f}% < 5%")
        status = "PASS"
    elif false_positive_rate < 10.0:
        print(f"⚠️  WARNING - False positive rate {false_positive_rate:.1f}% between 5-10%")
        status = "WARNING"
    else:
        print(f"❌ FAIL - False positive rate {false_positive_rate:.1f}% > 10%")
        status = "FAIL"
    
    print()
    
    return {
        "success": True,
        "status": status,
        "total_chunks": total_chunks,
        "total_titles": total_titles,
        "false_positive_chunks": false_positive_chunk_count,
        "false_positive_titles": sum(len(titles) for titles in false_positives.values()),
        "false_positive_rate": false_positive_rate,
        "false_positives_by_category": {
            category: len(titles) for category, titles in false_positives.items()
        },
        "examples": {
            category: titles[:3] for category, titles in false_positives.items()
        }
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Audit ChromaDB for false positives")
    parser.add_argument(
        "--chroma-db",
        default="chroma_db",
        help="Path to ChromaDB directory (default: chroma_db)"
    )
    
    args = parser.parse_args()
    
    result = audit_false_positives(args.chroma_db)
    
    if not result["success"]:
        sys.exit(1)
    
    if result["status"] == "FAIL":
        sys.exit(2)
    elif result["status"] == "WARNING":
        sys.exit(3)
    else:
        sys.exit(0)
