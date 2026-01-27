#!/usr/bin/env python3
"""Generate narration audio using TTS services."""

import os
from pathlib import Path

def print_elevenlabs_instructions():
    """Print instructions for ElevenLabs TTS."""
    print("="*60)
    print("ElevenLabs TTS (Recommended)")
    print("="*60)
    print("\n1. Sign up at: https://elevenlabs.io (free tier available)")
    print("2. Go to 'Speech Synthesis'")
    print("3. Select a natural voice (recommended: Rachel, Adam, Antoni, Elli)")
    print("4. Copy text from demo/DEMO_SCRIPT.md section by section")
    print("5. Generate and download MP3 files")
    print("6. Save to: demo/audio/section1.mp3, section2.mp3, etc.")
    print("\nVoice Settings:")
    print("- Stability: 0.5-0.7 (for natural variation)")
    print("- Similarity: 0.75 (default)")
    print("- Style: 0.0 (neutral)")
    print("="*60 + "\n")

def print_playht_instructions():
    """Print instructions for PlayHT TTS."""
    print("="*60)
    print("PlayHT TTS")
    print("="*60)
    print("\n1. Sign up at: https://play.ht")
    print("2. Select a natural voice (e.g., Michael, Joanna, Matthew)")
    print("3. Paste text from demo/DEMO_SCRIPT.md")
    print("4. Generate and download MP3")
    print("5. Save to: demo/audio/")
    print("="*60 + "\n")

def print_amazon_polly_instructions():
    """Print instructions for Amazon Polly."""
    print("="*60)
    print("Amazon Polly (AWS)")
    print("="*60)
    print("\n1. Install AWS CLI: pip install boto3")
    print("2. Configure AWS credentials: aws configure")
    print("3. Run:")
    print("""
import boto3

polly = boto3.client('polly')

# Read script
with open('demo/DEMO_SCRIPT.md', 'r') as f:
    text = f.read()

# Generate speech
response = polly.synthesize_speech(
    Text=text,
    OutputFormat='mp3',
    VoiceId='Joanna'  # or 'Matthew', 'Amy', etc.
)

# Save audio
with open('demo/audio/narration.mp3', 'wb') as f:
    f.write(response['AudioStream'].read())
""")
    print("\nRecommended voices: Joanna, Matthew, Amy")
    print("="*60 + "\n")

def print_google_tts_instructions():
    """Print instructions for Google Cloud TTS."""
    print("="*60)
    print("Google Cloud Text-to-Speech")
    print("="*60)
    print("\n1. Install: pip install google-cloud-texttospeech")
    print("2. Set up Google Cloud credentials")
    print("3. Run:")
    print("""
from google.cloud import texttospeech

client = texttospeech.TextToSpeechClient()

# Read script
with open('demo/DEMO_SCRIPT.md', 'r') as f:
    text = f.read()

# Configure voice
voice = texttospeech.VoiceSelectionParams(
    language_code='en-US',
    name='en-US-Neural2-F'  # Natural voice
)

# Generate speech
response = client.synthesize_speech(
    input=texttospeech.SynthesisInput(text=text),
    voice=voice,
    audio_config=texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
)

# Save audio
with open('demo/audio/narration.mp3', 'wb') as f:
    f.write(response.audio_content)
""")
    print("="*60 + "\n")

def create_audio_directory():
    """Create audio directory if it doesn't exist."""
    audio_dir = Path("demo/audio")
    audio_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created directory: {audio_dir}")

def main():
    """Main function."""
    print("="*60)
    print("TTS Narration Generator")
    print("="*60)
    print("\nThis script provides instructions for generating narration")
    print("using various Text-to-Speech services.\n")
    
    create_audio_directory()
    
    print("\nChoose a TTS service:\n")
    print("1. ElevenLabs (Recommended - best natural voices)")
    print("2. PlayHT")
    print("3. Amazon Polly (AWS)")
    print("4. Google Cloud TTS")
    print("5. Show all options")
    
    choice = input("\nEnter choice (1-5) or press Enter for ElevenLabs: ").strip()
    
    if choice == "1" or choice == "":
        print_elevenlabs_instructions()
    elif choice == "2":
        print_playht_instructions()
    elif choice == "3":
        print_amazon_polly_instructions()
    elif choice == "4":
        print_google_tts_instructions()
    elif choice == "5":
        print_elevenlabs_instructions()
        print_playht_instructions()
        print_amazon_polly_instructions()
        print_google_tts_instructions()
    else:
        print("Invalid choice. Showing ElevenLabs instructions:")
        print_elevenlabs_instructions()
    
    print("\n" + "="*60)
    print("Next Steps")
    print("="*60)
    print("\n1. Generate narration audio using your chosen TTS service")
    print("2. Save audio files to: demo/audio/")
    print("3. Use audio files in OBS Studio or video editing software")
    print("4. Follow demo script: demo/DEMO_SCRIPT.md")
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
