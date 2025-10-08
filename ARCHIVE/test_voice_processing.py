#!/usr/bin/env python3
"""
Test voice processing with a real audio file
"""

import sys
import os
import base64

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add FFmpeg to PATH
os.environ["PATH"] = r"C:\ffmpeg\bin;" + os.environ["PATH"]

try:
    import whisper
    print("✅ Whisper imported successfully")
except Exception as e:
    print(f"❌ Failed to import Whisper: {e}")
    exit(1)

def test_voice_processing_with_file(audio_file_path):
    """Test voice processing with Whisper using a real audio file"""
    try:
        print(f"Processing audio file: {audio_file_path}")
        
        # Verify file exists and has content
        if not os.path.exists(audio_file_path):
            raise Exception(f"Audio file not found: {audio_file_path}")
        
        file_size = os.path.getsize(audio_file_path)
        if file_size == 0:
            raise Exception("Audio file is empty")
        
        print(f"Audio file size: {file_size} bytes")
        
        # Load Whisper model
        print("Loading Whisper model...")
        model = whisper.load_model("base")
        print("Whisper model loaded successfully")
        
        # Transcribe audio
        print(f"Starting transcription...")
        result = model.transcribe(audio_file_path, language='ru')
        transcription = result["text"]
        print(f"Transcription completed: '{transcription}'")
        
        return transcription
        
    except Exception as e:
        print(f"Voice processing failed: {e}")
        return None

if __name__ == "__main__":
    print("Testing voice processing with real audio file...")
    
    # Test with the created audio file
    result = test_voice_processing_with_file("test_audio.wav")
    if result is not None:
        print(f"Voice transcription: {result}")
    else:
        print("Voice processing failed")
    
    print("Test completed.")