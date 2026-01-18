
import json
import os
from pathlib import Path
from collections import Counter
import sys

def verify_dataset(base_path: str):
    print(f"Verifying dataset at: {base_path}")
    
    stats = {
        "total_files": 0,
        "valid_json": 0,
        "invalid_json": 0,
        "type_mismatches": 0,
        "empty_descriptions": 0,
        "zero_confidence": 0,
    }
    
    type_distribution = Counter()
    issues = []
    
    # Directory to Type mapping
    dir_to_type = {
        'characters': 'character',
        'locations': 'location',
        'factions': 'faction',
        'technology': 'technology',
        'creatures': 'creature',
        'documents': 'document',
        'mutations': 'mutation',
        'perks': 'perk',
        'diseases': 'disease',
        'quests': 'quest',
        'events': 'event',
        'items': 'item',
        'unknown': 'unknown'
    }

    # critical_checks = {
    #    "id_substring": (expected_type, expected_dir)
    # }
    critical_checks = {
        "buttercup": {"type": "character", "found": False},
        "rose_fallout_76": {"type": "character", "found": False},
        "tax_evasion": {"type": "quest", "found": False}
    }

    base = Path(base_path)
    
    for category_dir in base.iterdir():
        if not category_dir.is_dir():
            continue
            
        category_name = category_dir.name
        expected_type = dir_to_type.get(category_name)
        
        print(f"Scanning {category_name} (Expected Type: {expected_type})...")
        
        for file_path in category_dir.glob("*.json"):
            stats["total_files"] += 1
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    stats["valid_json"] += 1
                    
                    # 1. Check Mandatory Fields
                    if not all(k in data for k in ["id", "name", "type", "description"]):
                        issues.append(f"Missing fields in {file_path.name}")
                        continue

                    current_type = data.get("type")
                    type_distribution[current_type] += 1
                    
                    # 2. Check Type Matches Directory
                    if expected_type and current_type != expected_type:
                        # Allow 'unknown' type in 'unknown' folder, but not mismatched types in specific folders
                        # Also allow 'robot' or subtypes if logic evolves, but for now strict check
                        stats["type_mismatches"] += 1
                        issues.append(f"Type Mismatch: {file_path.name} is '{current_type}', expected '{expected_type}' in {category_name}")

                    # 3. Check Description
                    if not data.get("description") or len(data.get("description").strip()) < 10:
                        stats["empty_descriptions"] += 1
                        issues.append(f"Empty/Short Description: {file_path.name}")

                    # 4. Critical Entity Checks
                    for key, check in critical_checks.items():
                        if key in data.get("id"): # Check if ID contains the key
                            check["found"] = True
                            if data.get("type") != check["type"]:
                                issues.append(f"CRITICAL FAILURE: {file_path.name} is classified as '{data.get('type')}', expected '{check['type']}'")
                                
            except json.JSONDecodeError:
                stats["invalid_json"] += 1
                issues.append(f"Invalid JSON: {file_path.name}")
            except Exception as e:
                issues.append(f"Error reading {file_path.name}: {str(e)}")

    print("\n" + "="*50)
    print("VERIFICATION REPORT")
    print("="*50)
    print(f"Total Files: {stats['total_files']}")
    print(f"Valid JSON: {stats['valid_json']}")
    print(f"Invalid JSON: {stats['invalid_json']}")
    print(f"Type Mismatches: {stats['type_mismatches']}")
    print(f"Empty Descriptions: {stats['empty_descriptions']}")
    print("-" * 30)
    print("Type Distribution:")
    for t, count in type_distribution.most_common():
        print(f"  {t}: {count}")
    
    print("-" * 30)
    print("Critical Authenticity Checks:")
    all_critical_passed = True
    for key, check in critical_checks.items():
        if not check["found"]:
            print(f"  [FAIL] Entity containing '{key}' NOT FOUND in dataset.")
            all_critical_passed = False
        else:
             print(f"  [PASS] Entity '{key}' found.")

    if issues:
        print("\n" + "="*50)
        print("ISSUES FOUND (First 20):")
        for i, issue in enumerate(issues[:20]):
            print(f"  - {issue}")
        if len(issues) > 20:
            print(f"  ... and {len(issues) - 20} more.")
    else:
        print("\n[SUCCESS] No dataset integrity issues found.")
        
    return 0 if (not issues and all_critical_passed) else 1

if __name__ == "__main__":
    path = r"c:\esp32-project\lore\fallout76_canon\entities"
    if len(sys.argv) > 1:
        path = sys.argv[1]
    verify_dataset(path)
