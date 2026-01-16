"""
Debug script to check why sections aren't being found in plain text.
"""

import sys
sys.path.insert(0, 'tools/wiki_to_chromadb')

from wiki_parser_v2 import extract_pages, clean_wikitext
from extractors import StructuralExtractor

def debug_page(title_to_find: str):
    """Debug a specific page to see section extraction"""
    xml_path = 'lore/fallout_wiki_complete.xml'
    
    print(f"\n{'='*80}")
    print(f"Searching for page: {title_to_find}")
    print('='*80)
    
    for page_data in extract_pages(xml_path):
        if page_data['title'] == title_to_find:
            wikitext = page_data['wikitext']
            
            print(f"\n[PAGE FOUND] {page_data['title']}")
            print(f"   Wikitext length: {len(wikitext)} chars\n")
            
            # Extract sections from RAW wikitext
            sections = StructuralExtractor.extract_section_tree(wikitext)
            
            print(f"[SECTIONS] Found {len(sections)} sections in RAW wikitext:")
            for i, section in enumerate(sections[:10], 1):  # Show first 10
                print(f"   {i}. Level {section.level}: '{section.title}'")
            
            if len(sections) > 10:
                print(f"   ... and {len(sections) - 10} more sections")
            
            # Now clean the wikitext
            plain_text, metadata = clean_wikitext(wikitext)
            
            print(f"\n[PLAIN TEXT] After cleaning:")
            print(f"   Plain text length: {len(plain_text)} chars")
            print(f"   First 500 chars:\n")
            print(f"   {plain_text[:500]}\n")
            
            # Check if section titles exist in plain text
            print(f"[CHECK] Checking if section titles exist in plain text:")
            missing_count = 0
            for section in sections[:10]:
                if section.title in plain_text:
                    print(f"   [OK] Found: '{section.title}'")
                else:
                    print(f"   [MISSING] '{section.title}'")
                    missing_count += 1
            
            if missing_count > 0:
                print(f"\n[WARNING] {missing_count} section titles NOT found in plain text!")
                print(f"   This is why 'Could not find section' errors occur.")
                print(f"\n[ROOT CAUSE] Section headers like '== Title ==' are stripped")
                print(f"   during wikitext cleaning, so the title text doesn't appear")
                print(f"   in the same place in plain_text.")
            else:
                print(f"\n[SUCCESS] All section titles found in plain text")
            
            return
    
    print(f"[ERROR] Page '{title_to_find}' not found in XML")


if __name__ == '__main__':
    # Test with a page that had errors in the log
    print("Starting debug script...")
    import os
    xml_path = 'lore/fallout_wiki_complete.xml'
    if not os.path.exists(xml_path):
        print(f"ERROR: XML file not found at {xml_path}")
    else:
        print(f"XML file found: {os.path.getsize(xml_path)} bytes")
    
    # Try a simpler page name first
    print("\n" + "="*80)
    print("Test 1: Vault 101 (should work)")
    print("="*80)
    debug_page('Vault 101')
    
    print("\n\n" + "="*80)
    print("Test 2: Community Center Terminal Entries (from error log)")
    print("="*80)
    debug_page('Community Center Terminal Entries')
