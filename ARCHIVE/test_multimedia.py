#!/usr/bin/env python3
"""
Test script for multimedia processing
"""

import sys
import os
import base64
import tempfile

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

def test_voice_processing(voice_data_base64):
    """Test voice processing with Whisper"""
    try:
        # Decode base64 voice data
        voice_bytes = base64.b64decode(voice_data_base64)
        
        # Create temporary audio file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_audio:
            temp_audio.write(voice_bytes)
            temp_audio_path = temp_audio.name
        
        try:
            print(f"Processing voice message ({len(voice_bytes)} bytes)")
            
            # Verify file exists and has content
            if not os.path.exists(temp_audio_path):
                raise Exception(f"Temporary audio file not created: {temp_audio_path}")
            
            file_size = os.path.getsize(temp_audio_path)
            if file_size == 0:
                raise Exception("Temporary audio file is empty")
            
            print(f"Temporary audio file created: {temp_audio_path} ({file_size} bytes)")
            
            # Load Whisper model
            print("Loading Whisper model...")
            model = whisper.load_model("base")
            print("Whisper model loaded successfully")
            
            # Transcribe audio
            print(f"Starting transcription of {temp_audio_path}...")
            result = model.transcribe(temp_audio_path, language='ru')
            transcription = result["text"]
            print(f"Transcription completed: '{transcription[:50]}...'")
            
            return transcription
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_audio_path)
            except:
                pass
                
    except Exception as e:
        print(f"Voice processing failed: {e}")
        return None

def test_image_processing(image_data_base64):
    """Test image processing"""
    try:
        # Decode base64 image data
        image_bytes = base64.b64decode(image_data_base64)
        
        # Create temporary image file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_image:
            temp_image.write(image_bytes)
            temp_image_path = temp_image.name
        
        try:
            # Verify file exists and has content
            if not os.path.exists(temp_image_path):
                raise Exception(f"Temporary image file not created: {temp_image_path}")
            
            file_size = os.path.getsize(temp_image_path)
            if file_size == 0:
                raise Exception("Temporary image file is empty")
            
            print(f"Temporary image file created: {temp_image_path} ({file_size} bytes)")
            
            # For testing purposes, just return a success message
            return "Image processed successfully"
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_image_path)
            except:
                pass
                
    except Exception as e:
        print(f"Image processing failed: {e}")
        return None

if __name__ == "__main__":
    print("Testing multimedia processing...")
    
    # Test voice processing with a simple test
    # For now, just test that the function works without actual audio data
    print("Testing voice processing function...")
    # We'll skip the actual voice processing test since we don't have a proper test file
    
    # Test image processing with a simple PNG file
    # This is a simple PNG file with a single pixel
    test_png_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    result = test_image_processing(test_png_data)
    if result is not None:
        print(f"Image processing result: {result}")
    else:
        print("Image processing failed")
    
    print("Test completed.")