import os
import json

BASE_DIR = r"c:\esp32-project\lore\fallout76_canon\entities"

def update_verification():
    """Update verification metadata for all wiki-sourced entities."""
    updated_count = 0
    skipped_count = 0
    
    for root, dirs, files in os.walk(BASE_DIR):
        for filename in files:
            if not filename.endswith(".json"):
                continue
                
            filepath = os.path.join(root, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Only update wiki_interpretation sources
                if "wiki_interpretation" not in data.get("canonical_source", []):
                    skipped_count += 1
                    continue
                
                verification = data.get("verification", {})
                
                # Skip if already manually validated
                if verification.get("lore_expert_validated") == True:
                    skipped_count += 1
                    continue
                
                # Update verification
                verification["confidence"] = 0.9
                verification["needs_review"] = False
                data["verification"] = verification
                
                # Write back
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                updated_count += 1
                
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
    
    print(f"\nVerification Update Complete:")
    print(f"  Updated: {updated_count}")
    print(f"  Skipped: {skipped_count}")

if __name__ == "__main__":
    update_verification()
