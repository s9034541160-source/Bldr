#!/usr/bin/env python3
"""
Test script to verify core module imports
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.super_smart_coordinator import SuperSmartCoordinator
    print("✅ SuperSmartCoordinator imported successfully")
except Exception as e:
    print(f"❌ Failed to import SuperSmartCoordinator: {e}")

try:
    import whisper
    print("✅ Whisper imported successfully")
except Exception as e:
    print(f"❌ Failed to import Whisper: {e}")

try:
    import ffmpeg
    print("✅ FFmpeg imported successfully")
except Exception as e:
    print(f"❌ Failed to import FFmpeg: {e}")