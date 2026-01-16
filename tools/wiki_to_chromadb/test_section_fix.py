
import sys
import os
import re

# Simulate the issue
def strip_markup(text):
    text = re.sub(r'\[\[([^\]\|]+)\|?([^\]]*)\]\]', r'\2' if r'\2' else r'\1', text) # Simple wikilink strip
    text = re.sub(r'\{\{[^}]+\}\}', '', text) # Simple template strip
    return text.strip()

wikitext = """
== [[S1E1 - The End]] ==
Some text here.

== [[S1E2 - The Beginning]] ==
More text.

== 12 Gauge Round (Junk) {{Icon|FNVDM|link=Dead Money}} ==
Even more text.
"""

cleaned_text = """
S1E1 - The End
Some text here.

S1E2 - The Beginning
More text.

12 Gauge Round (Junk) 
Even more text.
"""

# Current Extract logic (simplified)
section_pattern = r'^(={1,6})\s*(.+?)\s*\1\s*$'
sections = []
for line in wikitext.split('\n'):
    match = re.match(section_pattern, line.strip())
    if match:
        sections.append(match.group(2).strip())

print("Extracted Sections (Raw):")
for s in sections:
    print(f"  '{s}'")

# Current Check logic
print("\nChecking against cleaned text:")
for s in sections:
    found = cleaned_text.find(s)
    if found == -1:
        print(f"  ❌ Could not find '{s}'")
    else:
        print(f"  ✅ Found '{s}'")

# Proposed Fix logic
print("\nChecking with stripped title:")
def clean_title_for_search(title):
    # This needs to match mwparserfromhell's behavior mostly
    # But since we don't have that library here easily in this snippet without imports
    # We will simulate valid stripping behavior
    
    # Strip links [[Target|Display]] -> Display
    t = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', title)
    # Strip templates {{Template}} -> ''
    t = re.sub(r'\{\{[^}]+\}\}', '', t)
    return t.strip()

for s in sections:
    clean_s = clean_title_for_search(s)
    found = cleaned_text.find(clean_s)
    if found == -1:
        print(f"  ❌ Could not find '{clean_s}' (Original: '{s}')")
    else:
        print(f"  ✅ Found '{clean_s}' (Original: '{s}')")
