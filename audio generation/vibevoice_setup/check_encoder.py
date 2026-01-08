import torch
from transformers import AutoModel
import sys
import os

# Ensure VibeVoice module is reachable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "VibeVoice")))

# Import to register the model architecture
from vibevoice.modular.modeling_vibevoice_streaming_inference import VibeVoiceStreamingForConditionalGenerationInference

def check_encoder_weights():
    print("Loading model...")
    # We use the base model class or the specific inference class
    model = VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
        "microsoft/VibeVoice-Realtime-0.5B", 
        trust_remote_code=True,
        device_map="cpu"
    )
    
    print("Checking keys...")
    encoder_keys = [k for k in model.state_dict().keys() if "encoder" in k]
    
    if len(encoder_keys) > 0:
        print(f"Found {len(encoder_keys)} encoder keys!")
        for k in encoder_keys[:10]:
            print(f" - {k}")
    else:
        print("No encoder keys found.")

    # Also check acoustic tokenizer specific keys
    at_keys = [k for k in model.state_dict().keys() if "acoustic_tokenizer" in k]
    print(f"\nFound {len(at_keys)} acoustic tokenizer keys.")
    for k in at_keys[:20]:
        print(f" - {k}")

if __name__ == "__main__":
    check_encoder_weights()
