import os
import argparse
import random
import pyttsx3
from pydub import AudioSegment

# DJ Templates
TEMPLATES = [
    "Coming up next, we have {title} by {artist}.",
    "Here is a classic track. This is {artist} with {title}.",
    "You are listening to the station. Up next, {title}.",
    "Stay tuned for {title} by {artist}.",
    "Now playing, {artist}, {title}.",
    "Don't go anywhere, {title} is coming up right now.",
    "This is one of my favorites. {title} by {artist}."
]

def generate_dj_intro(title, artist, output_folder, voice_id=None, rate=150):
    """
    Generates a DJ intro MP3 file for a specific song.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 1. Select Template
    template = random.choice(TEMPLATES)
    text = template.format(title=title, artist=artist)
    print(f"DJ Says: \"{text}\"")

    # 2. Setup TTS Engine
    engine = pyttsx3.init()
    engine.setProperty('rate', rate) # Speed of speech
    
    # Set Voice (Optional)
    voices = engine.getProperty('voices')
    if voice_id is not None and voice_id < len(voices):
        engine.setProperty('voice', voices[voice_id].id)
    
    # 3. Generate WAV (pyttsx3 saves as WAV)
    temp_wav = os.path.join(output_folder, "temp_intro.wav")
    engine.save_to_file(text, temp_wav)
    engine.runAndWait()

    # 4. Convert to MP3 (using pydub)
    # Filename safe string
    safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
    output_filename = f"intro_{safe_title.replace(' ', '_')}.mp3"
    output_path = os.path.join(output_folder, output_filename)

    try:
        audio = AudioSegment.from_wav(temp_wav)
        audio.export(output_path, format="mp3", bitrate="128k")
        print(f"Saved: {output_path}")
    except Exception as e:
        print(f"Error converting to MP3: {e}")
        print("Ensure FFMPEG is installed and in your PATH.")
    finally:
        if os.path.exists(temp_wav):
            os.remove(temp_wav)

    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate DJ Intro MP3s")
    parser.add_argument("--title", required=True, help="Song Title")
    parser.add_argument("--artist", required=True, help="Song Artist")
    parser.add_argument("--output", default="station_assets/dj_clips", help="Output folder")
    parser.add_argument("--voice", type=int, default=0, help="Voice ID index (0, 1, etc.)")
    
    args = parser.parse_args()
    
    generate_dj_intro(args.title, args.artist, args.output, args.voice)
