import os
import argparse
import pandas as pd
from pydub import AudioSegment
from pydub.silence import split_on_silence
import whisper
import torch
from tqdm import tqdm

def process_audio(input_file, output_dir, min_silence_len=500, silence_thresh=-40, keep_silence=200):
    # Setup directories
    wavs_dir = os.path.join(output_dir, "wavs")
    os.makedirs(wavs_dir, exist_ok=True)
    
    print(f"Loading audio file: {input_file} (This might take a moment...)")
    # Use from_file to automatically detect format (mp3, wav, etc.)
    audio = AudioSegment.from_file(input_file)
    audio = audio.set_frame_rate(24000).set_channels(1)  # Enforce 24kHz mono
    
    print("Splitting audio on silence...")
    # This splits the audio into chunks where silence is at least 500ms long
    chunks = split_on_silence(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
        keep_silence=keep_silence
    )
    
    print(f"Found {len(chunks)} chunks. Exporting and transcribing...")
    
    # Load Whisper model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading Whisper model on {device}...")
    model = whisper.load_model("medium", device=device) # 'medium' is a good balance for 3060
    
    metadata = []
    
    for i, chunk in enumerate(tqdm(chunks)):
        # Skip chunks that are too short (e.g. < 1 second) or too long (> 20 seconds)
        if len(chunk) < 1000 or len(chunk) > 20000:
            continue
            
        filename = f"julie_chunk_{i:04d}.wav"
        filepath = os.path.join(wavs_dir, filename)
        
        # Export audio
        chunk.export(filepath, format="wav")
        
        # Transcribe
        result = model.transcribe(filepath)
        text = result["text"].strip()
        
        if text:
            metadata.append({
                "file_name": os.path.join("wavs", filename), # Relative path for VibeVoice
                "text": text
            })
            
    # Save Metadata
    df = pd.DataFrame(metadata)
    csv_path = os.path.join(output_dir, "metadata.csv")
    df.to_csv(csv_path, index=False)
    
    print(f"\nDone! Processed {len(metadata)} valid segments.")
    print(f"Dataset saved to: {output_dir}")
    print(f"Metadata file: {csv_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare dataset for VibeVoice fine-tuning")
    parser.add_argument("--input_wav", type=str, required=True, help="Path to the source long WAV file")
    parser.add_argument("--output_dir", type=str, default="./dataset_julie", help="Where to save the dataset")
    
    args = parser.parse_args()
    
    process_audio(args.input_wav, args.output_dir)
