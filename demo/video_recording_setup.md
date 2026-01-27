# Video Recording Setup Guide

## Prerequisites

### Software Requirements
1. **Screen Recording Software:**
   - macOS: QuickTime Player (built-in) or OBS Studio (recommended)
   - Windows: OBS Studio or Camtasia
   - Linux: OBS Studio or SimpleScreenRecorder

2. **Text-to-Speech (TTS) Software:**
   - **ElevenLabs** (Recommended - natural voices, no cloning needed)
   - **PlayHT** (Natural voices available)
   - **Amazon Polly** (AWS - high quality)
   - **Google Cloud Text-to-Speech** (Natural voices)
   - **Azure Speech Services** (Microsoft)

3. **Video Editing (Optional):**
   - DaVinci Resolve (Free, professional)
   - Adobe Premiere Pro
   - Final Cut Pro (macOS)

### Hardware Requirements
- Headphones (to monitor audio)
- Dual monitor setup (recommended - one for recording, one for controls)

---

## Step 1: Generate Narration with Natural TTS

### Option A: ElevenLabs (Recommended - Best Natural Voices)

1. **Sign up:** https://elevenlabs.io (free tier available)

2. **Select a Natural Voice:**
   - Go to "Speech Synthesis"
   - Browse available voices (e.g., "Rachel", "Adam", "Antoni")
   - Choose a natural-sounding voice (not robotic)

3. **Generate Narration:**
   - Paste text from `demo/DEMO_SCRIPT.md` section by section
   - Adjust voice settings (stability, similarity, style)
   - Generate audio
   - Download as MP3

4. **Save files:** `demo/audio/section1.mp3`, `demo/audio/section2.mp3`, etc.

**Recommended ElevenLabs Voices:**
- Rachel (female, professional)
- Adam (male, clear)
- Antoni (male, friendly)
- Elli (female, warm)

### Option B: PlayHT (Natural Voices)

1. **Sign up:** https://play.ht

2. **Select Voice:**
   - Browse natural voices (e.g., "Michael", "Joanna", "Matthew")
   - Choose a professional-sounding voice

3. **Generate Audio:**
   - Paste text from demo script
   - Generate and download MP3

### Option C: Amazon Polly (AWS)

```bash
# Install AWS CLI and configure
pip install boto3

# Generate speech
aws polly synthesize-speech \
  --output-format mp3 \
  --voice-id Joanna \
  --text "$(cat demo/DEMO_SCRIPT.md)" \
  demo/audio/narration.mp3
```

**Recommended Polly Voices:**
- Joanna (female, US English)
- Matthew (male, US English)
- Amy (female, British English)

### Option D: Google Cloud Text-to-Speech

```bash
# Install gcloud CLI
pip install google-cloud-texttospeech

# Use Python script (see below)
```

### Option E: Azure Speech Services

```bash
# Install Azure SDK
pip install azure-cognitiveservices-speech

# Use Python script (see below)
```

### Quick TTS Script

Create `demo/generate_narration.py` to automate TTS generation (see below).

---

## Step 3: Screen Layout Setup

### Recommended Layout

```
┌─────────────────────────────────────────────────────────┐
│                    Screen Recording Area                  │
│                                                           │
│  ┌──────────────────────────┐  ┌──────────────────────┐  │
│  │                          │  │                      │  │
│  │   Browser (Streamlit)   │  │   Terminal (Docker)  │  │
│  │        (60%)             │  │       (40%)          │  │
│  │                          │  │                      │  │
│  │  http://localhost:8501  │  │  docker-compose logs │  │
│  │                          │  │                      │  │
│  └──────────────────────────┘  └──────────────────────┘  │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### Setup Instructions

1. **Open Browser:**
   - Navigate to http://localhost:8501
   - Resize to 60% of screen width
   - Position on left side

2. **Open Terminal:**
   - Run: `docker-compose logs -f`
   - Resize to 40% of screen width
   - Position on right side

3. **Hide Unnecessary Elements:**
   - Hide browser bookmarks bar
   - Hide terminal prompt (optional)
   - Close other applications

---

## Step 4: OBS Studio Setup (Recommended)

### Installation

```bash
# macOS
brew install --cask obs

# Linux (Ubuntu/Debian)
sudo apt install obs-studio

# Windows
# Download from https://obsproject.com
```

### Scene Configuration

1. **Create Scene:** "Demo Recording"

2. **Add Sources:**
   - **Display Capture** (full screen)
   - **Media Source** (for pre-recorded TTS narration audio)
   - **Audio Output Capture** (system audio - for alerts/notifications)

3. **Audio Settings:**
   - Sample Rate: 48kHz
   - Channels: Stereo
   - Bitrate: 192 kbps

4. **Video Settings:**
   - Base Resolution: 1920x1080
   - Output Resolution: 1920x1080
   - FPS: 30

5. **Output Settings:**
   - Recording Format: MP4
   - Encoder: x264 (or hardware encoder if available)
   - Bitrate: 6000 kbps (for good quality)

### Recording Setup Script

Create `demo/start_recording.sh`:

```bash
#!/bin/bash
# Start recording setup

echo "Starting demo recording setup..."

# Start Docker containers if not running
if ! docker ps | grep -q "crew-ai-agent"; then
    echo "Starting Docker containers..."
    docker-compose up -d
    sleep 5
fi

# Open browser
echo "Opening browser..."
open http://localhost:8501  # macOS
# xdg-open http://localhost:8501  # Linux
# start http://localhost:8501  # Windows

# Open terminal with logs
echo "Opening terminal with Docker logs..."
osascript -e 'tell application "Terminal" to do script "cd '$(pwd)' && docker-compose logs -f"'  # macOS
# For Linux/Windows, manually open terminal and run: docker-compose logs -f

echo "Setup complete! Start recording in OBS Studio."
```

---

## Step 5: Recording Process

### Pre-Recording Checklist

- [ ] Docker containers running
- [ ] Browser open to dashboard
- [ ] Terminal showing Docker logs
- [ ] OBS Studio configured
- [ ] Audio levels tested
- [ ] Screen layout verified
- [ ] Demo script ready
- [ ] TTS narration audio ready (if pre-recorded)

### Recording Steps

1. **Start OBS Recording:**
   - Click "Start Recording"
   - Verify red recording indicator

2. **Follow Demo Script:**
   - Follow `demo/DEMO_SCRIPT.md` section by section
   - Pause between sections if needed
   - Can edit pauses out later

3. **Key Actions to Capture:**
   - Dashboard overview
   - Clicking "Process Feedback"
   - Docker logs showing activity
   - Configuration changes
   - Analytics views
   - QA comparison

4. **Stop Recording:**
   - Click "Stop Recording" in OBS
   - File saved to default location

---

## Step 6: Post-Production (Optional)

### Using DaVinci Resolve (Free)

1. **Import Media:**
   - Import video recording
   - Import TTS narration audio files

2. **Sync Audio:**
   - Align TTS narration with video actions
   - Remove pauses/retakes
   - Adjust timing if needed

3. **Add Overlays:**
   - Text overlays for key points
   - Timestamps (optional)
   - Logo/watermark (optional)

4. **Edit:**
   - Cut unnecessary parts
   - Smooth transitions
   - Add background music (low volume, optional)

5. **Export:**
   - Format: MP4
   - Resolution: 1920x1080
   - Frame rate: 30 fps
   - Bitrate: 6000 kbps

### Quick Edit Script (FFmpeg)

```bash
#!/bin/bash
# Quick video editing with FFmpeg

INPUT="demo/recording_raw.mp4"
AUDIO="demo/audio/narration.mp3"
OUTPUT="demo/demo_final.mp4"

# Replace audio track with TTS narration
ffmpeg -i "$INPUT" -i "$AUDIO" -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 "$OUTPUT"

# Add text overlay (example)
# ffmpeg -i "$OUTPUT" -vf "drawtext=text='Demo':fontcolor=white:fontsize=24:x=10:y=10" "demo/demo_with_text.mp4"
```

---

## Step 7: Automated Recording Script

Create `demo/record_demo.py`:

```python
#!/usr/bin/env python3
"""Automated demo recording script with voice cloning."""

import subprocess
import time
import os
from pathlib import Path

def check_prerequisites():
    """Check if all prerequisites are met."""
    checks = {
        "Docker": subprocess.run(["docker", "--version"], capture_output=True).returncode == 0,
        "Docker Compose": subprocess.run(["docker-compose", "--version"], capture_output=True).returncode == 0,
    }
    
    for name, passed in checks.items():
        if not passed:
            print(f"❌ {name} not found")
            return False
        print(f"✅ {name} found")
    return True

def start_services():
    """Start Docker services."""
    print("Starting Docker services...")
    subprocess.run(["docker-compose", "up", "-d"], check=True)
    print("Waiting for services to be ready...")
    time.sleep(10)

def open_browser():
    """Open browser to dashboard."""
    url = "http://localhost:8501"
    print(f"Opening browser to {url}...")
    
    import platform
    system = platform.system()
    if system == "Darwin":  # macOS
        subprocess.run(["open", url])
    elif system == "Linux":
        subprocess.run(["xdg-open", url])
    elif system == "Windows":
        subprocess.run(["start", url], shell=True)

def generate_narration():
    """Generate narration using TTS."""
    print("\n" + "="*60)
    print("Narration Generation with TTS")
    print("="*60)
    print("\nTo generate narration:")
    print("1. Use ElevenLabs (recommended) or other TTS service")
    print("2. Select a natural-sounding voice (not robotic)")
    print("3. Use the demo script (demo/DEMO_SCRIPT.md) to generate audio")
    print("4. Save audio files to demo/audio/")
    print("\nRecommended TTS services:")
    print("- ElevenLabs: https://elevenlabs.io (best natural voices)")
    print("- PlayHT: https://play.ht")
    print("- Amazon Polly (if you have AWS account)")
    print("\nOr record live narration during screen recording.")
    print("="*60 + "\n")

def main():
    """Main function."""
    print("="*60)
    print("Demo Recording Setup")
    print("="*60 + "\n")
    
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please install missing software.")
        return
    
    start_services()
    open_browser()
    generate_narration()
    
    print("\n" + "="*60)
    print("Setup Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Open OBS Studio")
    print("2. Configure scene (Display Capture + Audio)")
    print("3. Open terminal: docker-compose logs -f")
    print("4. Start recording")
    print("5. Follow demo script: demo/DEMO_SCRIPT.md")
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
```

---

## Troubleshooting

### Audio Issues

**Problem:** No audio in recording
- **Solution:** Check OBS audio sources are enabled and levels are up

**Problem:** Audio out of sync
- **Solution:** In editing software, adjust audio track timing

### Video Quality Issues

**Problem:** Blurry text
- **Solution:** Increase bitrate to 8000+ kbps, ensure 1920x1080 resolution

**Problem:** Laggy recording
- **Solution:** Use hardware encoder (NVENC, QuickSync), reduce bitrate

### Docker Issues

**Problem:** Containers not starting
- **Solution:** Check `docker-compose logs`, ensure ports aren't in use

**Problem:** No logs showing
- **Solution:** Run `docker-compose logs -f` in separate terminal

---

## Quick Start Commands

```bash
# 1. Generate TTS narration (optional)
# Use ElevenLabs or other TTS service with demo/DEMO_SCRIPT.md
# Save audio files to demo/audio/

# 2. Set up recording environment
python demo/record_demo.py

# 3. Start OBS Studio and configure

# 4. Open terminal for Docker logs
docker-compose logs -f

# 5. Start recording and follow demo script
# Follow: demo/DEMO_SCRIPT.md
# If using pre-recorded TTS, add audio track in OBS
```

---

## Final Output

- **Raw Recording:** `demo/recording_raw.mp4`
- **Final Video:** `demo/demo_final.mp4`
- **Audio Files:** `demo/audio/*.mp3` (TTS narration)
- **Duration:** ~17-20 minutes
- **Format:** MP4, 1920x1080, 30fps, H.264, AAC audio
