"""
Deep dive into why some sections aren't in plain text.
"""

import sys
sys.path.insert(0, 'tools/wiki_to_chromadb')

from wiki_parser_v2 import extract_pages, clean_wikitext
from extractors import StructuralExtractor
import mwparserfromhell

def debug_section_content(page_title: str, section_title: str):
    """Debug why a specific section isn't found"""
    xml_path = 'lore/fallout_wiki_complete.xml'
    
    for page_data in extract_pages(xml_path):
        if page_data['title'] == page_title:
            wikitext = page_data['wikitext']
            
            print(f"Page: {page_title}")
            print(f"Looking for section: '{section_title}'")
            print("=" * 80)
            
            # Find the section in raw wikitext
            lines = wikitext.split('\n')
            section_line_idx = None
            
            for idx, line in enumerate(lines):
                if section_title in line and '==' in line:
                    section_line_idx = idx
                    print(f"\nFound section header at line {idx}:")
                    print(f"  {line}")
                    
                    # Show context (5 lines after)
                    print(f"\nContent after header:")
                    for i in range(idx + 1, min(idx + 6, len(lines))):
                        print(f"  {i}: {lines[i]}")
                    break
            
            if section_line_idx is None:
                print(f"\n[NOT FOUND] Section '{section_title}' not found in raw wikitext")
                return
            
            # Now check what happens during cleaning
            plain_text, _ = clean_wikitext(wikitext)
            
            # Strip markup from section title
            parsed = mwparserfromhell.parse(section_title)
            cleaned_title = parsed.strip_code().strip()
            
            print(f"\n" + "=" * 80)
            print(f"After cleaning wikitext:")
            print(f"  Original section title: '{section_title}'")
            print(f"  Cleaned section title:  '{cleaned_title}'")
            print(f"  Found in plain text: {cleaned_title in plain_text}")
            
            if cleaned_title in plain_text:
                # Find context around it
                idx = plain_text.find(cleaned_title)
                print(f"\nContext in plain text:")
                print(f"  ...{plain_text[max(0, idx-50):idx + len(cleaned_title) + 50]}...")
            else:
                print(f"\n[ISSUE] Cleaned title NOT found in plain text")
                print(f"\nFirst 500 chars of plain text:")
                print(f"  {plain_text[:500]}")
            
            return

if __name__ == '__main__':
    # Test the problematic cases
    print("Test 1: Caravan Pack (wikilink section)\n")
    debug_section_content("Courier's Stash", "[[Caravan Pack]]")
    
    print("\n\n" + "=" * 100)
    print("Test 2: See Also (plain text section)\n")
    debug_section_content("Craig", "See Also")
    
    print("\n\n" + "=" * 100)
    print("Test 3: Fallout Series (quote issue)\n")
    debug_section_content("Corrieanne Stein", "''Fallout'' Series")
