# Demo Materials

This directory contains all materials needed for creating a comprehensive demo presentation of the Intelligent User Feedback Analysis System.

## Contents

### Planning Documents
- **DEMO_PLAN.md** - Detailed demo plan with timing and structure
- **DEMO_SCRIPT.md** - Complete narration script for the demo

### Architecture Diagrams
- **architecture_diagram.py** - Python script to generate visual diagrams
- **architecture_text.txt** - Text-based architecture diagrams
- **aws_production_architecture.md** - Detailed AWS architecture documentation
- **diagrams/** - Generated diagram images (run `architecture_diagram.py` to generate)

### Video Recording
- **video_recording_setup.md** - Complete guide for recording the demo video
- **record_demo.py** - Automated setup script for recording
- **generate_narration.py** - Helper script for TTS narration generation

### Audio Files (Generated)
- **audio/** - Directory for generated TTS narration audio files

## Quick Start

### 1. Generate Diagrams

```bash
# Install diagram dependencies
pip install diagrams

# Generate diagrams
python demo/architecture_diagram.py
```

### 2. Generate Narration Audio (Optional)

Use a TTS service to generate natural-sounding narration:

```bash
# Get instructions for TTS services
python demo/generate_narration.py

# Recommended: Use ElevenLabs (https://elevenlabs.io)
# - Sign up (free tier available)
# - Select a natural voice (Rachel, Adam, Antoni, Elli)
# - Copy text from demo/DEMO_SCRIPT.md section by section
# - Generate and download MP3 files
# - Save to demo/audio/section1.mp3, section2.mp3, etc.
```

### 3. Set Up Recording Environment

```bash
# Run setup script
python demo/record_demo.py

# Or manually:
# 1. Start Docker: docker-compose up -d
# 2. Open browser: http://localhost:8501
# 3. Open terminal: docker-compose logs -f
# 4. Configure OBS Studio (see video_recording_setup.md)
```

### 4. Record Demo

1. Open OBS Studio
2. Configure scene (Display Capture + Audio)
3. If using pre-recorded TTS, add Media Source with audio files
4. Start recording
5. Follow `DEMO_SCRIPT.md` section by section
6. Stop recording when complete

### 5. Post-Production (Optional)

Edit the recording to:
- Sync TTS narration audio (if pre-recorded)
- Add text overlays
- Remove pauses/retakes
- Add transitions

Export as `demo/demo_final.mp4` (1920x1080, 30fps, MP4).

## Demo Structure

The demo follows this structure:

1. **Introduction** (2 min) - Project overview and tech stack
2. **Architecture** (3 min) - System design and agent pipeline
3. **Features Demo** (8-10 min) - Live demonstration of all features
4. **AWS Production** (3-4 min) - Production deployment architecture
5. **Closing** (1 min) - Summary and next steps

**Total Duration:** ~17-20 minutes

## Key Demo Points

### Must Show:
- ✅ Dashboard overview
- ✅ Starting processing workflow
- ✅ Real-time progress tracking
- ✅ Configuration of priority rules
- ✅ Threshold configuration
- ✅ Analytics dashboard
- ✅ QA comparison metrics
- ✅ Docker logs showing agent activity

### Architecture Highlights:
- 7-agent pipeline
- Event-driven design
- Scalable AWS architecture
- Production-ready deployment

## Tips for Recording

1. **Practice First:** Run through the demo once without recording
2. **Check Audio:** Test audio levels before recording
3. **Screen Layout:** Ensure browser and terminal are clearly visible
4. **Pace Yourself:** Don't rush - pause if needed (can edit later)
5. **Show Docker Logs:** Keep terminal visible to show agent activity
6. **Highlight Key Features:** Use cursor/mouse to point at important elements
7. **TTS Narration:** Use natural-sounding voices (not robotic) from ElevenLabs or similar

## TTS Service Recommendations

### ElevenLabs (Recommended)
- **URL:** https://elevenlabs.io
- **Why:** Best natural voices, free tier available
- **Recommended Voices:** Rachel, Adam, Antoni, Elli
- **Cost:** Free tier includes 10,000 characters/month

### PlayHT
- **URL:** https://play.ht
- **Why:** Good natural voices, easy to use
- **Recommended Voices:** Michael, Joanna, Matthew

### Amazon Polly (If you have AWS)
- **Why:** High quality, pay-per-use
- **Recommended Voices:** Joanna, Matthew, Amy

## Troubleshooting

### Diagrams Not Generating
- Install dependencies: `pip install diagrams`
- May need Graphviz: `brew install graphviz` (macOS) or `apt install graphviz` (Linux)

### TTS Issues
- Use ElevenLabs for best natural voices
- Adjust voice settings (stability, similarity) for more natural sound
- Generate section by section for better control

### Recording Quality Issues
- Use OBS Studio for best results
- Increase bitrate for better quality
- Use hardware encoder if available

## File Structure

```
demo/
├── README.md                          # This file
├── DEMO_PLAN.md                       # Demo plan with timing
├── DEMO_SCRIPT.md                     # Complete narration script
├── architecture_diagram.py            # Diagram generation script
├── architecture_text.txt              # Text-based diagrams
├── aws_production_architecture.md     # AWS architecture docs
├── video_recording_setup.md           # Recording guide
├── record_demo.py                     # Setup automation script
├── generate_narration.py              # TTS narration helper
├── requirements.txt                   # Python dependencies
├── diagrams/                          # Generated diagrams
│   ├── current_architecture.png
│   ├── agent_pipeline.png
│   ├── aws_architecture.png
│   └── data_flow.png
├── audio/                             # Generated TTS narration
│   ├── section1.mp3
│   ├── section2.mp3
│   └── ...
└── recording_raw.mp4                  # Raw recording (after recording)
└── demo_final.mp4                     # Final edited video (after editing)
```

## Next Steps

1. Review `DEMO_PLAN.md` to understand the structure
2. Read `DEMO_SCRIPT.md` to prepare narration
3. Generate TTS narration using `generate_narration.py` (optional)
4. Generate diagrams using `architecture_diagram.py`
5. Set up recording environment using `record_demo.py`
6. Record demo following the script
7. Edit and finalize video

Good luck with your demo! 🎬
