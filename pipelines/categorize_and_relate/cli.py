#!/usr/bin/env python3
"""
CLI tool for Audio -> Whisper -> Categorize & Relate pipeline
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
import requests
import signal
import os

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent
RECORDINGS_DIR = PROJECT_ROOT / "recordings"
WEB_DIR = PROJECT_ROOT / "web"
SERVER_DIR = PROJECT_ROOT / "server"

# Server processes
backend_process = None
frontend_process = None

def start_servers():
    """Start both backend and frontend servers"""
    global backend_process, frontend_process
    
    print("🚀 Starting servers...")
    
    # Start FastAPI backend
    try:
        backend_process = subprocess.Popen(
            ["uv", "run", "uvicorn", "server.main:app", "--reload", "--port", "8000"],
            cwd=PROJECT_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("   ✅ Backend started on http://localhost:8000")
    except Exception as e:
        print(f"   ❌ Failed to start backend: {e}")
        return False
    
    # Start web UI server
    try:
        frontend_process = subprocess.Popen(
            ["uv", "run", "python", "-m", "http.server", "5173", "--directory", "web"],
            cwd=PROJECT_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("   ✅ Web UI started on http://localhost:5173")
    except Exception as e:
        print(f"   ❌ Failed to start web UI: {e}")
        return False
    
    # Wait for servers to start
    print("   ⏳ Waiting for servers to initialize...")
    time.sleep(3)
    
    # Check if servers are responding
    try:
        resp = requests.get("http://localhost:8000/health", timeout=5)
        if resp.status_code == 200:
            print("   ✅ Backend health check passed")
        else:
            print("   ⚠️  Backend health check failed")
    except Exception:
        print("   ❌ Backend not responding")
    
    try:
        resp = requests.get("http://localhost:5173", timeout=5)
        if resp.status_code == 200:
            print("   ✅ Web UI health check passed")
        else:
            print("   ⚠️  Web UI health check failed")
    except Exception:
        print("   ❌ Web UI not responding")
    
    print("\n🎉 Pipeline ready!")
    print("   📱 Web UI: http://localhost:5173/index.html")
    print("   🔗 API: http://localhost:8000/docs")
    return True

def stop_servers():
    """Stop both servers"""
    global backend_process, frontend_process
    
    print("🛑 Stopping servers...")
    
    if backend_process:
        backend_process.terminate()
        try:
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()
        print("   ✅ Backend stopped")
    
    if frontend_process:
        frontend_process.terminate()
        try:
            frontend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            frontend_process.kill()
        print("   ✅ Web UI stopped")

def process_audio_file(audio_file: Path):
    """Process an audio file through the pipeline"""
    if not audio_file.exists():
        print(f"❌ Audio file not found: {audio_file}")
        return
    
    print(f"🎵 Processing audio file: {audio_file.name}")
    
    try:
        with open(audio_file, 'rb') as f:
            files = {'file': (audio_file.name, f, 'audio/webm')}
            resp = requests.post("http://localhost:8000/process-audio", files=files, timeout=30)
        
        if resp.status_code == 200:
            result = resp.json()
            print("✅ Processing complete!")
            
            metadata = result.get('metadata', {})
            print(f"   📝 Transcript: {metadata.get('transcript', 'N/A')}")
            print(f"   📁 Saved as: {metadata.get('audio_file', 'N/A')}")
            print(f"   🕒 Timestamp: {metadata.get('timestamp', 'N/A')}")
            
            # Pretty print result
            print("\n📊 Analysis Result:")
            print(json.dumps(result.get('result', {}), indent=2))
        else:
            print(f"❌ Processing failed: {resp.status_code}")
            print(resp.text)
    
    except Exception as e:
        print(f"❌ Error processing file: {e}")

def list_recordings():
    """List all saved recordings"""
    try:
        resp = requests.get("http://localhost:8000/recordings", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            recordings = data.get('recordings', [])
            count = data.get('count', 0)
            
            if count == 0:
                print("📭 No recordings found")
                return
            
            print(f"📚 Found {count} recording(s):")
            print()
            
            for i, rec in enumerate(recordings, 1):
                print(f"   {i}. {rec.get('timestamp', 'Unknown')} - {rec.get('audio_file', 'Unknown')}")
                print(f"      📝 \"{rec.get('transcript', 'No transcript')[:60]}...\"")
                print(f"      📁 Audio exists: {'✅' if rec.get('audio_exists') else '❌'}")
                print()
        else:
            print(f"❌ Failed to fetch recordings: {resp.status_code}")
    
    except Exception as e:
        print(f"❌ Error fetching recordings: {e}")

def show_status():
    """Show server status"""
    print("🔍 Checking server status...")
    
    # Check backend
    try:
        resp = requests.get("http://localhost:8000/health", timeout=5)
        if resp.status_code == 200:
            print("   ✅ Backend: Running on http://localhost:8000")
        else:
            print(f"   ⚠️  Backend: Responding with {resp.status_code}")
    except Exception:
        print("   ❌ Backend: Not running")
    
    # Check frontend
    try:
        resp = requests.get("http://localhost:5173", timeout=5)
        if resp.status_code == 200:
            print("   ✅ Web UI: Running on http://localhost:5173")
        else:
            print(f"   ⚠️  Web UI: Responding with {resp.status_code}")
    except Exception:
        print("   ❌ Web UI: Not running")
    
    # Check recordings
    if RECORDINGS_DIR.exists():
        audio_files = list(RECORDINGS_DIR.glob("*_recording.*"))
        metadata_files = list(RECORDINGS_DIR.glob("*_metadata.json"))
        print(f"   📚 Recordings: {len(audio_files)} audio files, {len(metadata_files)} metadata files")
    else:
        print("   📭 Recordings: Directory not found")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Shutting down...")
    stop_servers()
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Audio -> Whisper -> Categorize & Relate CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start servers
    subparsers.add_parser('start', help='Start backend and web UI servers')
    
    # Stop servers
    subparsers.add_parser('stop', help='Stop all servers')
    
    # Status
    subparsers.add_parser('status', help='Show server status')
    
    # Process file
    process_parser = subparsers.add_parser('process', help='Process an audio file')
    process_parser.add_argument('file', type=Path, help='Audio file to process')
    
    # List recordings
    subparsers.add_parser('recordings', help='List all saved recordings')
    
    # Serve (start and keep running)
    subparsers.add_parser('serve', help='Start servers and keep running (Ctrl+C to stop)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    if args.command == 'start':
        start_servers()
    
    elif args.command == 'stop':
        stop_servers()
    
    elif args.command == 'status':
        show_status()
    
    elif args.command == 'process':
        process_audio_file(args.file)
    
    elif args.command == 'recordings':
        list_recordings()
    
    elif args.command == 'serve':
        if start_servers():
            print("\n🔄 Servers running... Press Ctrl+C to stop")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                signal_handler(None, None)

if __name__ == "__main__":
    main()
