import os
import argparse
import random
import requests
import json

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

def generate_dj_intro_elevenlabs(title, artist, output_folder, api_key, voice_id="21m00Tcm4TlvDq8ikWAM"):
    """
    Generates a DJ intro MP3 file using ElevenLabs API.
    Default voice_id is 'Rachel' (21m00Tcm4TlvDq8ikWAM).
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 1. Select Template
    template = random.choice(TEMPLATES)
    text = template.format(title=title, artist=artist)
    print(f"DJ Says: \"{text}\"")

    # 2. Setup API Request
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }

    # 3. Call API
    try:
        print("Sending request to ElevenLabs...")
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            # 4. Save MP3
            # Filename safe string
            safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            output_filename = f"intro_{safe_title.replace(' ', '_')}.mp3"
            output_path = os.path.join(output_folder, output_filename)
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            
            print(f"Saved: {output_path}")
            return output_path
        else:
            print(f"Error: API returned {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"Error calling ElevenLabs: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate DJ Intro MP3s via ElevenLabs")
    parser.add_argument("--title", required=True, help="Song Title")
    parser.add_argument("--artist", required=True, help="Song Artist")
    parser.add_argument("--output", default="station_assets/dj_clips", help="Output folder")
    parser.add_argument("--apikey", required=True, help="ElevenLabs API Key")
    parser.add_argument("--voice", default="21m00Tcm4TlvDq8ikWAM", help="Voice ID (default: Rachel)")
    
    args = parser.parse_args()
    
    generate_dj_intro_elevenlabs(args.title, args.artist, args.output, args.apikey, args.voice)
