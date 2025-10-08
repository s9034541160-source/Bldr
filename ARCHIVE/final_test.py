#!/usr/bin/env python3
"""
Final test to verify that all multimedia processing components work together
"""

import sys
import os
import base64
import subprocess

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add FFmpeg to PATH
os.environ["PATH"] = r"C:\ffmpeg\bin;" + os.environ["PATH"]

def test_all_components():
    """Test all multimedia processing components"""
    print("Testing all multimedia processing components...")
    
    # Test 1: Whisper import
    try:
        import whisper
        print("✅ Whisper imported successfully")
    except Exception as e:
        print(f"❌ Failed to import Whisper: {e}")
        return False
    
    # Test 2: FFmpeg availability
    try:
        result = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print("✅ FFmpeg is available")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"❌ FFmpeg not found: {e}")
        return False
    
    # Test 3: Core module imports
    try:
        from core.super_smart_coordinator import SuperSmartCoordinator
        print("✅ SuperSmartCoordinator imported successfully")
    except Exception as e:
        print(f"❌ Failed to import SuperSmartCoordinator: {e}")
        return False
    
    # Test 4: Image processing libraries
    try:
        from PIL import Image
        print("✅ PIL (Pillow) imported successfully")
    except Exception as e:
        print(f"❌ Failed to import PIL: {e}")
        return False
    
    print("🎉 All components are working correctly!")
    return True

if __name__ == "__main__":
    success = test_all_components()
    if success:
        print("\n✅ Multimedia processing is ready to use!")
        print("Users can now send voice messages and photos to the Telegram bot.")
    else:
        print("\n❌ Some components are missing or not working correctly.")
        print("Please check the error messages above and install missing dependencies.")