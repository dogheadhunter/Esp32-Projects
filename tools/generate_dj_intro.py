import os
import sys
import argparse
import random
import csv
import torch
import torchaudio
import numpy as np
import pyttsx3
from pydub import AudioSegment

# Add project root to path to import chatterbox
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chatterbox.tts_turbo import ChatterboxTurboTTS

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_AUDIO_PATH = os.path.join(PROJECT_ROOT, "station_assets", "voices", "mr_new_vegas.mp3")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL = None

# DJ Templates
TEMPLATES = [
    "Coming up next, we have {title}, by {artist}.",
    "Here is a classic track. This is {artist}, with {title}.",
    "You are listening to the station. Up next, {title}.",
    "Stay tuned for, {title}, by {artist}.",
    "Now playing, {artist}, {title}.",
    "Don't go anywhere, {title} is coming up right now.",
    "This is one of my favorites. {title}, by {artist}."
]

def set_seed(seed: int):
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    # Do not reset global random seed to avoid affecting template selection
    # random.seed(seed) 
    np.random.seed(seed)

def load_model():
    global MODEL
    if MODEL is None:
        print(f"Loading Chatterbox-Turbo on {DEVICE}...")
        MODEL = ChatterboxTurboTTS.from_pretrained(DEVICE)
        print("Model loaded.")
    return MODEL

def generate_ai_intro_direct(text, output_wav_path, seed=0):
    """
    Generates AI voice directly using the loaded model.
    """
    try:
        model = load_model()
        
        # Handle Seed (0 = Random)
        if seed == 0:
            seed = random.randint(1, 999999)
            print(f"Random Seed Selected: {seed}")
        
        set_seed(seed)

        print(f"Generating AI Voice for: '{text}'")
        
        # Check if reference audio exists
        ref_audio = REF_AUDIO_PATH
        if not os.path.exists(ref_audio):
            print(f"Warning: Reference audio not found at {ref_audio}. Using default/random.")
            return False

        wav = model.generate(
            text,
            audio_prompt_path=ref_audio,
            temperature=0.7,
            top_p=0.8,
            top_k=1000,
            repetition_penalty=1.2,
            min_p=0.0,
            norm_loudness=True
        )
        
        # Save to WAV
        torchaudio.save(output_wav_path, wav.cpu(), model.sr)
        return True

    except Exception as e:
        print(f"Error in AI generation: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_dj_intro(title, artist, output_folder, voice_id=None, rate=150, use_ai=False):
    """
    Generates a DJ intro MP3 file for a specific song.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 1. Select Template
    template = random.choice(TEMPLATES)
    full_text = template.format(title=title, artist=artist)
    print(f"DJ Says: \"{full_text}\"")

    temp_wav = os.path.join(output_folder, "temp_intro.wav")
    
    if use_ai:
        print("Using AI Generation...")
        
        # Generate Full Intro
        success = generate_ai_intro_direct(full_text, temp_wav)
        
        if success:
            try:
                audio = AudioSegment.from_wav(temp_wav)
                
                # Filename safe string
                safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
                output_filename = f"intro_{safe_title.replace(' ', '_')}.mp3"
                output_path = os.path.join(output_folder, output_filename)
                
                audio.export(output_path, format="mp3", bitrate="128k")
                print(f"Saved: {output_path}")
                
                # Cleanup
                if os.path.exists(temp_wav): os.remove(temp_wav)
                
                return output_path
                
            except Exception as e:
                print(f"Error converting audio: {e}")
                use_ai = False # Fallback
        else:
            print("AI Generation failed, falling back.")
            use_ai = False

    if not use_ai:
        # Fallback to pyttsx3 (Old Logic)
        engine = pyttsx3.init()
        engine.setProperty('rate', rate)
        voices = engine.getProperty('voices')
        if voice_id is not None and voice_id < len(voices):
            engine.setProperty('voice', voices[voice_id].id)
        
        engine.save_to_file(full_text, temp_wav)
        engine.runAndWait()

        # Convert to MP3
        safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        output_filename = f"intro_{safe_title.replace(' ', '_')}.mp3"
        output_path = os.path.join(output_folder, output_filename)

        try:
            audio = AudioSegment.from_wav(temp_wav)
            audio.export(output_path, format="mp3", bitrate="128k")
            print(f"Saved: {output_path}")
        except Exception as e:
            print(f"Error converting to MP3: {e}")
        finally:
            if os.path.exists(temp_wav): os.remove(temp_wav)

        return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate DJ Intro MP3s")
    parser.add_argument("--title", help="Song Title")
    parser.add_argument("--artist", help="Song Artist")
    parser.add_argument("--random_csv", help="Path to CSV file to pick a random song from")
    parser.add_argument("--output", default="station_assets/dj_clips", help="Output folder")
    parser.add_argument("--voice", type=int, default=0, help="Voice ID index (0, 1, etc.)")
    parser.add_argument("--ai", action="store_true", help="Use AI Voice (Chatterbox Turbo)")
    
    args = parser.parse_args()

    title = args.title
    artist = args.artist

    if args.random_csv:
        if not os.path.exists(args.random_csv):
            print(f"Error: CSV file not found at {args.random_csv}")
            sys.exit(1)
        
        try:
            with open(args.random_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                songs = list(reader)
                if not songs:
                    print("Error: CSV file is empty")
                    sys.exit(1)
                
                random_song = random.choice(songs)
                title = random_song.get('Title') or random_song.get('title')
                artist = random_song.get('Artist') or random_song.get('artist')
                
                if not title or not artist:
                    print(f"Error: Could not find Title or Artist in selected row: {random_song}")
                    sys.exit(1)
                    
                print(f"Selected Random Song: {title} by {artist}")
        except Exception as e:
            print(f"Error reading CSV: {e}")
            sys.exit(1)

    if not title or not artist:
        print("Error: You must provide --title and --artist OR --random_csv")
        sys.exit(1)
    
    generate_dj_intro(title, artist, args.output, args.voice, use_ai=args.ai)
