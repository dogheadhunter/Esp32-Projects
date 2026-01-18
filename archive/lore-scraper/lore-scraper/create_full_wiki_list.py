"""
Download complete Fallout Wiki using page-by-page API approach.

Since MediaWiki export with generators doesn't support proper continuation,
we'll use the reliable approach: fetch metadata for all pages, then use
our existing scraper infrastructure to get content.

This creates a complete title list for the full wiki scrape.

Usage:
    python create_full_wiki_list.py
"""

import requests
import json
from pathlib import Path


WIKI_API = "https://fallout.wiki/api.php"
OUTPUT_FILE = Path(__file__).parent.parent.parent / 'lore' / 'fallout_complete_titles.txt'


def get_all_page_titles():
    """
    Fetch all article page titles from the wiki (namespace 0 only).
    
    Returns:
        List of page titles
    """
    session = requests.Session()
    continue_token = None
    all_titles = []
    
    print(f"Fetching all page titles from {WIKI_API}")
    print("(Main namespace only - articles, not templates/files/etc.)\n")
    
    while True:
        params = {
            "action": "query",
            "list": "allpages",
            "aplimit": "max",  # Maximum allowed (usually 500)
            "apnamespace": "0",  # Main namespace only (articles)
            "format": "json"
        }
        
        if continue_token:
            params["apcontinue"] = continue_token
        
        try:
            response = session.get(WIKI_API, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            pages = data.get("query", {}).get("allpages", [])
            for page in pages:
                all_titles.append(page["title"])
            
            print(f"  Fetched {len(all_titles)} titles...", end="\r")
            
            # Check for continuation
            if "continue" in data:
                continue_token = data["continue"]["apcontinue"]
            else:
                break
                
        except requests.RequestException as e:
            print(f"\n  Error: {e}")
            break
    
    print(f"\n  Total articles found: {len(all_titles)}")
    return all_titles


def save_titles(titles, output_path):
    """Save titles to text file, one per line."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for title in titles:
            # Convert spaces to underscores for URL compatibility
            title_normalized = title.replace(' ', '_')
            f.write(title_normalized + '\n')
    
    print(f"\nSaved to: {output_path}")
    print(f"File size: {output_path.stat().st_size / 1024:.1f} KB")


def main():
    print("="*60)
    print("Complete Fallout Wiki Title Extraction")
    print("="*60 + "\n")
    
    titles = get_all_page_titles()
    
    if titles:
        save_titles(titles, OUTPUT_FILE)
        
        print(f"\n{'='*60}")
        print(f"SUCCESS!")
        print(f"  Total titles: {len(titles)}")
        print(f"  Output file: {OUTPUT_FILE}")
        print(f"\nNext step:")
        print(f"  python tools\\lore-scraper\\scrape_fallout76.py \\")
        print(f"    --selection {OUTPUT_FILE} \\")
        print(f"    --output lore\\fallout_complete \\")
        print(f"    --rate-limit 0.5 \\")
        print(f"    --workers 10")
        print(f"{'='*60}")
    else:
        print("No titles retrieved!")


if __name__ == '__main__':
    main()
