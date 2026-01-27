# Demo Quick Start Guide

## 🚀 Fast Track to Recording Your Demo

### Step 1: Record Voice Sample (5 minutes)
```bash
# Record 2-3 minutes of your voice reading the introduction
# Save as: demo/myVoice.wav
```

### Step 2: Run Setup Script (1 minute)
```bash
python demo/record_demo.py
```
This will:
- ✅ Check prerequisites
- ✅ Start Docker containers
- ✅ Open browser to dashboard
- ✅ Open terminal with Docker logs

### Step 3: Configure OBS Studio (5 minutes)
1. Open OBS Studio
2. Create scene: "Demo Recording"
3. Add source: Display Capture (full screen)
4. Add source: Audio Input Capture (microphone)
5. Settings: 1920x1080, 30fps, MP4

### Step 4: Record Demo (20 minutes)
1. Start recording in OBS
2. Follow `demo/DEMO_SCRIPT.md` section by section
3. Show browser UI + Docker logs side-by-side
4. Stop recording when complete

### Step 5: Generate Narration (Optional - 30 minutes)
1. Upload `demo/myVoice.wav` to ElevenLabs (https://elevenlabs.io)
2. Generate audio for each section from `DEMO_SCRIPT.md`
3. Save to `demo/audio/` directory
4. Sync audio with video in editing software

### Step 6: Edit Video (Optional - 1 hour)
- Sync narration audio
- Add text overlays
- Remove pauses
- Export as `demo/demo_final.mp4`

---

## 📋 Demo Checklist

### Before Recording
- [ ] Docker containers running
- [ ] Browser open to http://localhost:8501
- [ ] Terminal showing `docker-compose logs -f`
- [ ] OBS Studio configured
- [ ] Audio levels tested
- [ ] Demo script ready (`demo/DEMO_SCRIPT.md`)

### During Recording
- [ ] Show dashboard overview
- [ ] Click "Process Feedback"
- [ ] Show Docker logs activity
- [ ] Configure priority rules
- [ ] Change threshold
- [ ] Show analytics
- [ ] Show QA comparison
- [ ] Explain AWS architecture

### After Recording
- [ ] Save raw recording
- [ ] Generate/edit narration (if needed)
- [ ] Edit video (optional)
- [ ] Export final video
- [ ] Review and share

---

## 🎯 Key Demo Points (Must Show)

1. **Dashboard** - Overview with summary cards
2. **Start Processing** - Click button, show status
3. **Progress Tracking** - Real-time updates in UI + logs
4. **Configuration** - Priority rules and threshold
5. **Analytics** - Charts and metrics
6. **QA Metrics** - Accuracy comparison
7. **AWS Architecture** - Production deployment plan

---

## ⏱️ Timing Guide

| Section | Duration | What to Show |
|---------|----------|--------------|
| Introduction | 2 min | Project overview, tech stack |
| Architecture | 3 min | Diagrams, agent pipeline |
| Features Demo | 8-10 min | Live UI demonstration |
| AWS Production | 3-4 min | Architecture diagram |
| Closing | 1 min | Summary, next steps |

**Total: ~17-20 minutes**

---

## 🛠️ Troubleshooting

### Docker not starting?
```bash
docker-compose down
docker-compose up -d
```

### Browser not opening?
Manually open: http://localhost:8501

### No Docker logs?
Run manually: `docker-compose logs -f`

### Audio issues?
- Check OBS audio sources are enabled
- Test microphone levels
- Use headphones to monitor

### Video quality poor?
- Increase bitrate to 6000+ kbps
- Use hardware encoder (NVENC/QuickSync)
- Ensure 1920x1080 resolution

---

## 📁 File Locations

- **Demo Plan:** `demo/DEMO_PLAN.md`
- **Demo Script:** `demo/DEMO_SCRIPT.md`
- **Architecture:** `demo/architecture_text.txt`
- **AWS Architecture:** `demo/aws_production_architecture.md`
- **Recording Guide:** `demo/video_recording_setup.md`
- **Voice Sample:** `demo/myVoice.wav` (you create this)
- **Audio Files:** `demo/audio/*.mp3` (generated)
- **Raw Recording:** `demo/recording_raw.mp4` (after recording)
- **Final Video:** `demo/demo_final.mp4` (after editing)

---

## 🎬 Recording Tips

1. **Practice First** - Run through demo once without recording
2. **Check Layout** - Browser (60%) + Terminal (40%) side-by-side
3. **Show Logs** - Keep Docker logs visible to show agent activity
4. **Pace Yourself** - Don't rush, pause if needed (can edit later)
5. **Highlight Features** - Use cursor to point at important elements
6. **Test Audio** - Record 10 seconds first to check levels

---

## 📞 Need Help?

- Review `demo/README.md` for detailed documentation
- Check `demo/video_recording_setup.md` for recording guide
- See `demo/DEMO_SCRIPT.md` for complete narration
- Check `demo/aws_production_architecture.md` for AWS details

---

**Good luck with your demo! 🎥**
