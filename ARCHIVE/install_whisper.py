#!/usr/bin/env python3
"""
Script to install Whisper dependency for voice processing in Telegram bot
"""

import subprocess
import sys
import os

def install_whisper():
    """Install Whisper dependency"""
    try:
        # Try to install Whisper
        print("Installing openai-whisper...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openai-whisper"])
        print("✅ openai-whisper installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install openai-whisper: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during installation: {e}")
        return False

def check_whisper():
    """Check if Whisper is available"""
    try:
        import whisper
        print("✅ Whisper is available")
        # Try to load a model to verify it works
        print("Loading Whisper base model...")
        model = whisper.load_model("base")
        print("✅ Whisper base model loaded successfully")
        return True
    except ImportError:
        print("❌ Whisper is not available")
        return False
    except Exception as e:
        print(f"❌ Error with Whisper: {e}")
        return False

def main():
    """Main function"""
    print("🔍 Checking Whisper availability...")
    if check_whisper():
        print("🎉 Whisper is already installed and working!")
        return True
    
    print("🔄 Installing Whisper...")
    if install_whisper():
        print("🔍 Verifying installation...")
        if check_whisper():
            print("🎉 Whisper installation completed successfully!")
            return True
        else:
            print("❌ Whisper installation completed but verification failed")
            return False
    else:
        print("❌ Failed to install Whisper")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)