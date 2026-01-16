"""
Test the new markup patterns from the log.
"""

import sys
sys.path.insert(0, 'tools/wiki_to_chromadb')

from wiki_parser_v2 import extract_pages, clean_wikitext
from extractors import StructuralExtractor
from chunker_v2 import strip_section_title_markup

def test_markup_patterns():
    """Test various markup patterns from the log"""
    
    test_cases = [
        ("'''Fallout'' Series'", "Fallout Series"),  # Bold markup
        ("[[Gristle]]'s terminal", "Gristle's terminal"),  # Wikilink + possessive
        ("[[Caravan Pack]]", "Caravan Pack"),  # Plain wikilink
        ("> [[Brian Fitzgerald|Fitzgerald, B.]]", "> Fitzgerald, B."),  # Quote + piped wikilink
        ("Storm_MQ02_IntroPt1 - [[Into Lands Unknown]]", "Storm_MQ02_IntroPt1 - Into Lands Unknown"),
    ]
    
    print("Testing markup stripping patterns:\n")
    print("=" * 80)
    
    for original, expected in test_cases:
        cleaned = strip_section_title_markup(original)
        match = "✓" if cleaned == expected else "✗"
        
        print(f"{match} '{original}'")
        print(f"  Expected: '{expected}'")
        print(f"  Got:      '{cleaned}'")
        if cleaned != expected:
            print(f"  MISMATCH!")
        print()

def check_real_pages():
    """Check if sections actually exist in the problematic pages"""
    xml_path = 'lore/fallout_wiki_complete.xml'
    
    test_pages = [
        ("Corrieanne Stein", "'''Fallout'' Series'"),
        ("Courier's Stash", "[[Caravan Pack]]"),
        ("Courier's Stash", "Notes"),
        ("Craig", "See Also"),
        ("Courtenay Taylor", "Gallery"),
    ]
    
    print("\n" + "=" * 80)
    print("Checking if sections exist in actual wiki pages:\n")
    
    for page_title, section_title in test_pages:
        for page_data in extract_pages(xml_path):
            if page_data['title'] == page_title:
                wikitext = page_data['wikitext']
                sections = StructuralExtractor.extract_section_tree(wikitext)
                plain_text, _ = clean_wikitext(wikitext)
                
                # Check if this section title is in the extracted sections
                section_exists = any(s.title == section_title for s in sections)
                
                if section_exists:
                    cleaned = strip_section_title_markup(section_title)
                    found_in_plain = cleaned in plain_text or section_title in plain_text
                    
                    status = "[OK]" if found_in_plain else "[FAIL]"
                    print(f"{status} '{page_title}' has section '{section_title}'")
                    print(f"      Cleaned: '{cleaned}'")
                    print(f"      Found in plain text: {found_in_plain}")
                else:
                    print(f"[MISSING] '{page_title}' does NOT have section '{section_title}'")
                    print(f"          Available sections: {[s.title for s in sections[:5]]}")
                print()
                break
        else:
            print(f"[SKIP] Page '{page_title}' not found in XML\n")

if __name__ == '__main__':
    test_markup_patterns()
    check_real_pages()
