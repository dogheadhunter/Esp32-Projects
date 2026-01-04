import pyttsx3

def list_voices():
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    
    print(f"{'ID':<5} | {'Name':<40} | {'Language'}")
    print("-" * 60)
    
    for i, voice in enumerate(voices):
        # Try to get language, might be empty or a list
        lang = voice.languages[0] if voice.languages else "Unknown"
        print(f"{i:<5} | {voice.name:<40} | {lang}")

if __name__ == "__main__":
    list_voices()
