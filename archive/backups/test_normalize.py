import json
from pathlib import Path

# Test specific file
file_path = Path(r"c:\esp32-project\lore\fallout76_canon\entities\creature\unknown_dave_mirelurk.json")
with open(file_path) as f:
    entity = json.load(f)

current_id = entity.get('id', '')
current_type = entity.get('type', '')
id_prefix = current_id.split('_')[0] if '_' in current_id else ''

print(f"File: {file_path.name}")
print(f"Current ID: {current_id}")
print(f"ID Prefix: {id_prefix}")
print(f"Current Type: {current_type}")
print(f"Type == 'unknown': {current_type == 'unknown'}")

# Check if should be skipped
if current_type == 'unknown':
    print("SKIPPED: Type is 'unknown'")
else:
    target_type = current_type
    print(f"Target Type: {target_type}")
    print(f"ID Prefix matches target: {id_prefix == target_type}")
    
    if id_prefix != target_type:
        id_suffix = '_'.join(current_id.split('_')[1:])
        new_id = f"{target_type}_{id_suffix}"
        print(f"MISMATCH DETECTED!")
        print(f"New ID would be: {new_id}")
    else:
        print("ID already correct, no change needed")
