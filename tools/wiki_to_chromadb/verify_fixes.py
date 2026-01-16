"""
Test both fixes:
1. Filter out decorative separator lines (=====)
2. Strip markup from section titles before searching
"""

import sys
sys.path.insert(0, 'tools/wiki_to_chromadb')

from wiki_parser_v2 import extract_pages, clean_wikitext
from extractors import StructuralExtractor
from chunker_v2 import strip_section_title_markup

def test_fixes():
    """Test that both fixes work correctly"""
    xml_path = 'lore/fallout_wiki_complete.xml'
    
    test_pages = [
        'Community Center Terminal Entries',  # Had decorative separators
        'Cooper Howard',  # Had section titles with wiki markup
        'Companion',  # Mix of issues
    ]
    
    print("Testing section extraction fixes...\n")
    print("=" * 80)
    
    total_sections = 0
    total_missing = 0
    
    for page_title in test_pages:
        for page_data in extract_pages(xml_path):
            if page_data['title'] == page_title:
                wikitext = page_data['wikitext']
                
                # Extract sections (should now filter decorators)
                sections = StructuralExtractor.extract_section_tree(wikitext)
                plain_text, _ = clean_wikitext(wikitext)
                
                missing = []
                for section in sections:
                    # Test with markup stripping
                    cleaned_title = strip_section_title_markup(section.title)
                    
                    if cleaned_title not in plain_text and section.title not in plain_text:
                        missing.append(f"{section.title} -> {cleaned_title}")
                
                total_sections += len(sections)
                total_missing += len(missing)
                
                status = "[PASS]" if not missing else "[FAIL]"
                print(f"{status} {page_title}")
                print(f"       Sections: {len(sections)}, Missing: {len(missing)}")
                
                if missing and len(missing) <= 5:
                    for m in missing:
                        print(f"         - {m}")
                elif missing:
                    print(f"         - {missing[0]}")
                    print(f"         ... and {len(missing) - 1} more")
                print()
                break
        else:
            print(f"[SKIP] {page_title} - not found in XML\n")
    
    print("=" * 80)
    print(f"Summary: {total_sections} total sections, {total_missing} missing")
    
    if total_missing == 0:
        print("[SUCCESS] All sections can be found in plain text!")
    else:
        pct = (total_missing / total_sections * 100) if total_sections > 0 else 0
        print(f"[PARTIAL] {pct:.1f}% of sections still missing")
        print("\nRemaining issues may be edge cases that need investigation.")

if __name__ == '__main__':
    print("Starting verification...")
    try:
        test_fixes()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
