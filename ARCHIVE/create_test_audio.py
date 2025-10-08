#!/usr/bin/env python3
"""
Create a simple test audio file for testing
"""

import wave
import numpy as np
import os

def create_test_wav(filename="test_audio.wav"):
    """Create a simple test WAV file with a sine wave"""
    # Parameters
    sample_rate = 44100  # Hz
    duration = 2  # seconds
    frequency = 440  # Hz (A4 note)
    
    # Generate sine wave
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    sine_wave = np.sin(2 * np.pi * frequency * t)
    
    # Normalize to 16-bit range
    audio_data = (sine_wave * 32767).astype(np.int16)
    
    # Write to WAV file
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16 bits
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    print(f"Created test audio file: {filename}")
    print(f"File size: {os.path.getsize(filename)} bytes")

if __name__ == "__main__":
    create_test_wav()