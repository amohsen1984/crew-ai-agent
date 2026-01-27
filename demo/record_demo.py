#!/usr/bin/env python3
"""Automated demo recording setup script."""

import subprocess
import time
import os
import platform
from pathlib import Path

def check_prerequisites():
    """Check if all prerequisites are met."""
    print("Checking prerequisites...\n")
    
    checks = {
        "Docker": subprocess.run(["docker", "--version"], capture_output=True).returncode == 0,
        "Docker Compose": subprocess.run(["docker-compose", "--version"], capture_output=True).returncode == 0,
    }
    
    all_passed = True
    for name, passed in checks.items():
        if passed:
            print(f"✅ {name} found")
        else:
            print(f"❌ {name} not found")
            all_passed = False
    
    return all_passed

def check_docker_running():
    """Check if Docker daemon is running."""
    try:
        result = subprocess.run(["docker", "ps"], capture_output=True, timeout=5)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False

def start_services():
    """Start Docker services."""
    print("\n" + "="*60)
    print("Starting Docker Services")
    print("="*60)
    
    if not check_docker_running():
        print("❌ Docker daemon is not running. Please start Docker Desktop.")
        return False
    
    print("Starting Docker containers...")
    try:
        subprocess.run(["docker-compose", "up", "-d"], check=True)
        print("✅ Containers started")
        print("Waiting for services to be ready...")
        time.sleep(10)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start containers: {e}")
        return False

def open_browser():
    """Open browser to dashboard."""
    url = "http://localhost:8501"
    print(f"\nOpening browser to {url}...")
    
    system = platform.system()
    try:
        if system == "Darwin":  # macOS
            subprocess.run(["open", url])
        elif system == "Linux":
            subprocess.run(["xdg-open", url])
        elif system == "Windows":
            subprocess.run(["start", url], shell=True)
        else:
            print(f"⚠️  Please manually open: {url}")
            return False
        print("✅ Browser opened")
        return True
    except Exception as e:
        print(f"⚠️  Could not open browser automatically: {e}")
        print(f"   Please manually open: {url}")
        return False

def open_terminal_with_logs():
    """Open terminal with Docker logs."""
    print("\nOpening terminal with Docker logs...")
    
    system = platform.system()
    command = "docker-compose logs -f"
    cwd = os.getcwd()
    
    try:
        if system == "Darwin":  # macOS
            script = f'tell application "Terminal" to do script "cd {cwd} && {command}"'
            subprocess.run(["osascript", "-e", script])
            print("✅ Terminal opened")
        elif system == "Linux":
            # Try common terminal emulators
            terminals = ["gnome-terminal", "xterm", "konsole", "terminator"]
            for term in terminals:
                try:
                    subprocess.Popen([term, "-e", f"bash -c '{command}; exec bash'"])
                    print(f"✅ Opened {term}")
                    return True
                except FileNotFoundError:
                    continue
            print("⚠️  Please manually open a terminal and run:")
            print(f"   cd {cwd}")
            print(f"   {command}")
        elif system == "Windows":
            subprocess.Popen(["cmd", "/c", "start", "cmd", "/k", command])
            print("✅ Command prompt opened")
        else:
            print("⚠️  Please manually open a terminal and run:")
            print(f"   cd {cwd}")
            print(f"   {command}")
        return True
    except Exception as e:
        print(f"⚠️  Could not open terminal automatically: {e}")
        print("   Please manually open a terminal and run:")
        print(f"   cd {cwd}")
        print(f"   {command}")
        return False

def check_audio_files():
    """Check if TTS audio files exist."""
    audio_dir = Path("demo/audio")
    if audio_dir.exists():
        audio_files = list(audio_dir.glob("*.mp3"))
        if audio_files:
            print(f"✅ Found {len(audio_files)} audio file(s) in demo/audio/")
            return True
        else:
            print("⚠️  No audio files found in demo/audio/")
            print("   Generate TTS narration using: python demo/generate_narration.py")
            return False
    else:
        print("⚠️  Audio directory not found: demo/audio/")
        print("   Generate TTS narration using: python demo/generate_narration.py")
        return False

def print_next_steps():
    """Print next steps for recording."""
    print("\n" + "="*60)
    print("Next Steps")
    print("="*60)
    print("\n1. ✅ Docker services are running")
    print("2. ✅ Browser should be open to dashboard")
    print("3. ✅ Terminal should be showing Docker logs")
    print("\n4. Open OBS Studio:")
    print("   - Create scene: 'Demo Recording'")
    print("   - Add source: Display Capture (full screen)")
    print("   - Add source: Audio Input Capture (microphone)")
    print("   - Configure: 1920x1080, 30fps, MP4")
    print("\n5. Start recording in OBS Studio")
    print("\n6. Follow the demo script:")
    print("   - Read: demo/DEMO_SCRIPT.md")
    print("   - Follow section by section")
    print("\n7. Stop recording when complete")
    print("\n8. Edit video (optional):")
    print("   - Sync audio narration")
    print("   - Add text overlays")
    print("   - Remove pauses")
    print("\n" + "="*60)

def main():
    """Main function."""
    print("="*60)
    print("Demo Recording Setup")
    print("="*60)
    print()
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please install missing software.")
        return
    
    # Check Docker daemon
    if not check_docker_running():
        print("\n❌ Docker daemon is not running.")
        print("   Please start Docker Desktop and try again.")
        return
    
    # Start services
    if not start_services():
        print("\n❌ Failed to start services.")
        return
    
    # Open browser
    open_browser()
    
    # Open terminal
    open_terminal_with_logs()
    
    # Check audio files
    check_audio_files()
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main()
