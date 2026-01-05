import os
import sys
import time
import datetime
import threading
import random
import argparse
import numpy as np
import torch
import torchaudio as ta
import requests
from chatterbox.tts_turbo import ChatterboxTurboTTS

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_REF_AUDIO_URL = "https://storage.googleapis.com/chatterbox-demo-samples/prompts/female_random_podcast.wav"
REF_AUDIO_FILENAME = os.path.join(PROJECT_ROOT, "station_assets", "voices", "mr_new_vegas.mp3")
OUTPUT_FILENAME = os.path.join(PROJECT_ROOT, "station_assets", "tests", "output_cli.wav")
DEFAULT_TEXT = "It's me again... Mr. New Vegas... reminding you that you're nobody... 'til somebody loves you."

# Logging Setup
LOG_DIR = "c:/esp32-project/logs/chatterbox_logs"
os.makedirs(LOG_DIR, exist_ok=True)
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = os.path.join(LOG_DIR, f"cli_debug_{timestamp}.log")

class TeeLogger(object):
    def __init__(self, stream, log_file):
        self.stream = stream
        self.log_file = log_file

    def write(self, message):
        self.stream.write(message)
        self.stream.flush()
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(message)
        except Exception:
            pass # Ignore logging errors to avoid infinite recursion

    def flush(self):
        self.stream.flush()

sys.stdout = TeeLogger(sys.stdout, LOG_FILE)
sys.stderr = TeeLogger(sys.stderr, LOG_FILE)

def set_seed(seed: int):
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    random.seed(seed)
    np.random.seed(seed)

def heartbeat(start_time, stop_event):
    while not stop_event.is_set():
        elapsed = time.time() - start_time
        print(f"... running for {elapsed:.1f}s ...")
        time.sleep(5)

def download_file(url, filename):
    if not os.path.exists(filename):
        print(f"Downloading default reference audio from {url}...")
        response = requests.get(url)
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"Saved to {filename}")
    else:
        print(f"Using existing reference audio: {filename}")

def main():
    parser = argparse.ArgumentParser(description="Chatterbox CLI Demo")
    parser.add_argument("--text", type=str, default=DEFAULT_TEXT, help="Text to synthesize")
    parser.add_argument("--output", type=str, default=OUTPUT_FILENAME, help="Output WAV file path")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    print(f"Logging to {LOG_FILE}")
    start_total = time.time()
    stop_heartbeat = threading.Event()
    heartbeat_thread = threading.Thread(target=heartbeat, args=(start_total, stop_heartbeat))
    heartbeat_thread.daemon = True
    heartbeat_thread.start()

    try:
        # 0. Set Seed
        set_seed(args.seed)
        print(f"Seed set to {args.seed}")

        # 1. Setup Device
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {device}")

        # 2. Get Reference Audio
        if not os.path.exists(REF_AUDIO_FILENAME):
            print(f"Reference audio not found at {REF_AUDIO_FILENAME}. Downloading default...")
            download_file(DEFAULT_REF_AUDIO_URL, "female_random_podcast.wav")
            ref_audio = "female_random_podcast.wav"
        else:
            print(f"Using reference audio: {REF_AUDIO_FILENAME}")
            ref_audio = REF_AUDIO_FILENAME

        # 3. Load Model
        print("Loading Chatterbox-Turbo model...")
        start_load = time.time()
        model = ChatterboxTurboTTS.from_pretrained(device)
        end_load = time.time()
        print(f"Model loaded in {end_load - start_load:.2f} seconds")

        # 4. Generate Audio
        print(f"Generating audio for text: '{args.text}'")
        start_gen = time.time()
        wav = model.generate(
            args.text,
            audio_prompt_path=ref_audio,
            temperature=0.7,
            top_p=0.8,
            top_k=1000,
            repetition_penalty=1.2,
            min_p=0.0,
            norm_loudness=True
        )
        end_gen = time.time()
        duration = end_gen - start_gen
        print(f"Audio generated in {duration:.2f} seconds")
        
        # 5. Save Output
        ta.save(args.output, wav, model.sr)
        print(f"Success! Audio saved to {args.output}")

    except KeyboardInterrupt:
        print("\nProcess interrupted by user!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        stop_heartbeat.set()
        total_time = time.time() - start_total
        print(f"Total execution time: {total_time:.2f} seconds")

if __name__ == "__main__":
    main()
