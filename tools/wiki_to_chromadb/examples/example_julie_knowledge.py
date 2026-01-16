"""
Example: What information would Julie know?

Julie is a DJ from Fallout 76, broadcasting from Appalachia around 2102 (25 years after the Great War).
Her knowledge is limited to:
- Events up to year 2102
- Appalachia region specifically
- Vault-Tec information (she's from Vault 76)
- Common knowledge available to early post-war survivors
"""
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from chromadb_ingest import ChromaDBIngestor, query_for_dj

# Initialize database
db = ChromaDBIngestor('chroma_db')

print("=" * 80)
print("JULIE'S KNOWLEDGE BASE (Fallout 76 DJ)")
print("=" * 80)
print("\nPersona: Julie from Vault 76, Appalachia")
print("Time Period: 2077-2102 (early post-war)")
print("Location: Appalachia (West Virginia)")
print("Knowledge: Vault 76, local events, pre-war history available to vault dwellers")
print("\n" + "=" * 80)

# Example queries Julie might use for her radio show
example_queries = [
    "What happened on Reclamation Day?",
    "Tell me about Vault 76 and the residents",
    "What is the Scorched plague?",
    "Pre-war West Virginia history",
    "What do we know about the Great War?"
]

for i, query in enumerate(example_queries, 1):
    print(f"\n{'='*80}")
    print(f"EXAMPLE {i}: Julie asks '{query}'")
    print('='*80)
    
    results = query_for_dj(db, "Julie (2102, Appalachia)", query, n_results=3)
    
    if results['metadatas'][0]:
        for j, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
            print(f"\n--- Result {j} ---")
            print(f"Title: {meta['wiki_title']}")
            print(f"Section: {meta.get('section', 'N/A')}")
            print(f"Time Period: {meta.get('time_period')} ({meta.get('year_min', 'N/A')} - {meta.get('year_max', 'N/A')})")
            print(f"Location: {meta.get('location')}")
            print(f"Content Type: {meta.get('content_type')}")
            print(f"Knowledge Tier: {meta.get('knowledge_tier')}")
            print(f"\nText Preview: {doc[:250]}...")
    else:
        print("  No results found")

# Show what Julie CANNOT access
print("\n" + "=" * 80)
print("WHAT JULIE DOESN'T KNOW (Events after 2102)")
print("=" * 80)

# Query for events she shouldn't know about
future_queries = [
    ("Sole Survivor and Institute", "2287 Commonwealth events"),
    ("NCR founding in Shady Sands", "2189 West Coast"),
    ("Hoover Dam battle", "2281 Mojave")
]

for query, description in future_queries:
    print(f"\n❌ {description}: '{query}'")
    results = query_for_dj(db, "Julie (2102, Appalachia)", query, n_results=1)
    
    if results['metadatas'][0]:
        meta = results['metadatas'][0][0]
        year_max = meta.get('year_max')
        location = meta.get('location')
        
        # Check if it should be filtered out
        if year_max and year_max > 2102:
            print(f"  ✓ Correctly filtered (year {year_max} > 2102)")
        elif location and location not in ["Appalachia", "general"]:
            print(f"  ✓ Correctly filtered (location: {location})")
        else:
            print(f"  ⚠️ Got result: {meta['wiki_title']} (year: {year_max}, location: {location})")
    else:
        print("  ✓ No results (correctly filtered)")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("""
Julie's knowledge is constrained by:
1. TEMPORAL: Only knows events up to 2102 (25 years after bombs fell)
   - She knows: Great War (2077), Vault 76 opening (2102), early Appalachia
   - She doesn't know: Commonwealth (2287), NCR founding (2189), Mojave (2281)

2. SPATIAL: Primarily knows Appalachia region
   - She knows: West Virginia, Vault 76, local factions (Responders, Free States)
   - Limited knowledge: Other regions (only common/vault-tec knowledge)

3. SOURCE: Vault-Tec records + early survivor experiences
   - She knows: Pre-war history from vault records, immediate post-war events
   - She doesn't know: Detailed events in other regions, future developments

This creates an authentic DJ persona that only references information her character
would realistically have access to in Fallout 76's timeline and setting.
""")
