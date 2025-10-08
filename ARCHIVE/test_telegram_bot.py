#!/usr/bin/env python3
"""
Test script for Telegram bot multimedia processing
"""

import base64
import requests
import os

# Get API token from environment
API_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc5MDAwNjgzNH0.zKZtA6_xVU40gnfuyc-0SqYOE0Yg_nWMvQdDD3VasFU'

def get_auth_headers():
    """Get authentication headers for API calls"""
    headers = {
        "Content-Type": "application/json"
    }
    if API_TOKEN:
        headers['Authorization'] = f'Bearer {API_TOKEN}'
    return headers

# Test voice processing
def test_voice_processing():
    print("Testing voice processing...")
    
    # Create a simple test voice message (base64 encoded)
    # This is a simple WAV file with silence
    test_wav_data = b'UklGRigAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQQAAAAA'
    voice_base64 = base64.b64encode(test_wav_data).decode('utf-8')
    
    # Prepare the payload
    chat_payload = {
        'message': 'Voice message',
        'context_search': False,
        'max_context': 1,
        'agent_role': 'coordinator',
        'voice_data': voice_base64,
        'request_context': {
            'channel': 'telegram',
            'chat_id': 'test_user',
            'user_id': 'test_user'
        }
    }
    
    try:
        # Send to AI chat endpoint
        headers = get_auth_headers()
        resp = requests.post('http://localhost:8000/api/ai/chat', json=chat_payload, headers=headers, timeout=30)
        print(f"Voice processing response status: {resp.status_code}")
        if resp.status_code == 200:
            response_data = resp.json()
            ai_response = response_data.get('response', '')
            print(f"Voice processing response: {ai_response}")
        else:
            print(f"Voice processing error: {resp.text}")
    except Exception as e:
        print(f"Voice processing exception: {e}")

# Test image processing
def test_image_processing():
    print("Testing image processing...")
    
    # Create a simple test image (base64 encoded)
    # This is a simple PNG file with a single pixel
    test_png_data = b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
    image_base64 = base64.b64encode(test_png_data).decode('utf-8')
    
    # Prepare the payload
    chat_payload = {
        'message': 'Analyze this image',
        'context_search': True,
        'max_context': 3,
        'agent_role': 'coordinator',
        'image_data': image_base64,
        'request_context': {
            'channel': 'telegram',
            'chat_id': 'test_user',
            'user_id': 'test_user'
        }
    }
    
    try:
        # Send to AI chat endpoint
        headers = get_auth_headers()
        resp = requests.post('http://localhost:8000/api/ai/chat', json=chat_payload, headers=headers, timeout=30)
        print(f"Image processing response status: {resp.status_code}")
        if resp.status_code == 200:
            response_data = resp.json()
            ai_response = response_data.get('response', '')
            print(f"Image processing response: {ai_response}")
        else:
            print(f"Image processing error: {resp.text}")
    except Exception as e:
        print(f"Image processing exception: {e}")

if __name__ == "__main__":
    print("Testing Telegram bot multimedia processing...")
    test_voice_processing()
    test_image_processing()
    print("Test completed.")