import torch
import sys
import os

def inspect_pt_file(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return

    try:
        data = torch.load(file_path, map_location='cpu', weights_only=False)
        print(f"Successfully loaded {file_path}")
        print(f"Type: {type(data)}")
        
        if isinstance(data, dict):
            print("\nKeys found:")
            for key, value in data.items():
                print(f" - {key}: {type(value)}")
                # Inspect internal structure if it's a ModelOutput
                if hasattr(value, 'past_key_values'):
                     pkv = value.past_key_values
                     if pkv and len(pkv) > 0:
                         # pkv is usually tuple of tuples
                         print(f"   -> has past_key_values. Layers: {len(pkv)}")
                         if len(pkv[0]) > 0:
                             print(f"   -> Layer 0 Key shape: {pkv[0][0].shape}")
                             print(f"   -> Layer 0 Value shape: {pkv[0][1].shape}")
                
                if isinstance(value, torch.Tensor):
                    print(f"   Tensor shape {value.shape}, dtype {value.dtype}")
        else:
            print("\nData is not a dictionary.")
            if isinstance(data, torch.Tensor):
                print(f"Tensor shape: {data.shape}")

    except Exception as e:
        print(f"Failed to load file: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_voice.py <path_to_pt_file>")
    else:
        inspect_pt_file(sys.argv[1])
