"""
Simple wiki exporter using MediaWiki API exportall generator.

This uses a single streaming approach to download all pages directly
without pre-fetching titles, which is much faster.

Usage:
    python export_wiki_simple.py
"""

import requests
from pathlib import Path
import time


WIKI_API = "https://fallout.wiki/api.php"
OUTPUT_FILE = Path(__file__).parent.parent.parent / 'lore' / 'fallout_wiki_dump.xml'


def export_all_pages_streaming():
    """
    Export all wiki pages using generator=allpages with export action.
    Uses continuation to handle pagination automatically.
    """
    print(f"Exporting all pages from {WIKI_API}")
    print(f"Output: {OUTPUT_FILE}\n")
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    session = requests.Session()
    continue_params = {}
    pages_exported = 0
    batch_num = 0
    start_time = time.time()
    
    # Write XML header
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.11/">\n')
        f.write('  <siteinfo>\n')
        f.write('    <sitename>Independent Fallout Wiki</sitename>\n')
        f.write('    <base>https://fallout.wiki/wiki/</base>\n')
        f.write('  </siteinfo>\n')
        
        while True:
            batch_num += 1
            
            params = {
                'action': 'query',
                'generator': 'allpages',
                'gaplimit': '50',  # 50 pages per batch (conservative)
                'export': '1',
                'exportnowrap': '1',
                'format': 'xml'
            }
            params.update(continue_params)
            
            try:
                print(f"Batch {batch_num}: Fetching...", end=' ', flush=True)
                response = session.get(WIKI_API, params=params, timeout=120)
                response.raise_for_status()
                
                # The response is raw XML with <page> elements
                # We need to extract just the <page> tags and append them
                content = response.text
                
                # Simple extraction: find all <page>...</page> blocks
                import re
                page_blocks = re.findall(r'(<page>.*?</page>)', content, re.DOTALL)
                
                for page_block in page_blocks:
                    f.write('  ')
                    f.write(page_block)
                    f.write('\n')
                    pages_exported += 1
                
                print(f"✓ {len(page_blocks)} pages ({pages_exported} total, {time.time()-start_time:.1f}s)")
                
                # Check for continuation
                if '<continue ' in content:
                    # Extract continuation parameters from XML
                    gap_continue = re.search(r'gapcontinue="([^"]+)"', content)
                    if gap_continue:
                        continue_params = {'gapcontinue': gap_continue.group(1)}
                    else:
                        break
                else:
                    break
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"✗ Error: {e}")
                break
        
        # Close XML
        f.write('</mediawiki>\n')
    
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"Export complete!")
    print(f"  Pages exported: {pages_exported}")
    print(f"  Time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
    print(f"  File size: {OUTPUT_FILE.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"  Output: {OUTPUT_FILE}")
    print(f"{'='*60}")


if __name__ == '__main__':
    export_all_pages_streaming()
