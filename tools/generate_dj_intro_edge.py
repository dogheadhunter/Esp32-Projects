import os
import asyncio
import random
import edge_tts
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

# Common English Voices
VOICES = {
    "guy": "en-US-GuyNeural",       # Male, very natural
    "aria": "en-US-AriaNeural",     # Female, very natural
    "jenny": "en-US-JennyNeural",   # Female, conversational
    "christopher": "en-US-ChristopherNeural", # Male, formal
    "eric": "en-US-EricNeural"      # Male, casual
}

async def _generate_edge_tts(text, output_file, voice="en-US-GuyNeural"):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def generate_dj_intro_edge(title, artist, output_folder, voice_name="guy"):
    """
    Generates a DJ intro MP3 file using Microsoft Edge's Online Neural TTS.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 1. Select Template
    template = random.choice(TEMPLATES)
    text = template.format(title=title, artist=artist)
    print(f"DJ Says: \"{text}\"")

    # 2. Select Voice
    voice_id = VOICES.get(voice_name.lower(), "en-US-GuyNeural")
    
    # 3. Generate MP3 directly (Edge TTS outputs mp3)
    # Filename safe string
    safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
    output_filename = f"intro_{safe_title.replace(' ', '_')}.mp3"
    output_path = os.path.join(output_folder, output_filename)

    try:
        asyncio.run(_generate_edge_tts(text, output_path, voice_id))
        print(f"Saved: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error generating Edge TTS: {e}")
        return None

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate DJ Intro using Edge TTS")
    parser.add_argument("--title", required=True, help="Song Title")
    parser.add_argument("--artist", required=True, help="Song Artist")
    parser.add_argument("--output", default="station_assets/dj_clips", help="Output folder")
    parser.add_argument("--voice", default="guy", help="Voice name (guy, aria, jenny, christopher, eric)")
    
    args = parser.parse_args()
    
    generate_dj_intro_edge(args.title, args.artist, args.output, args.voice)
