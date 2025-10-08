"""
End-to-end test for letter generation functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
import time
import json

def test_letter_generation_api():
    """Test the letter generation API endpoints"""
    
    # Base URL for the API
    base_url = "http://localhost:8000"
    
    # Test getting templates
    print("Testing template retrieval...")
    try:
        response = requests.get(f"{base_url}/templates")
        if response.status_code == 200:
            templates = response.json()
            print(f"✓ Successfully retrieved {len(templates)} templates")
            
            # Check if we have the expected construction templates
            template_ids = [t['id'] for t in templates]
            expected_templates = [
                'compliance_sp31',
                'violation_gesn',
                'tender_response_fz44',
                'delay_notice',
                'payment_dispute',
                'safety_incident_sanpin',
                'ecology_ovos_fz7',
                'bim_clash_report',
                'budget_overrun',
                'hr_salary_claim'
            ]
            
            for template_id in expected_templates:
                if template_id in template_ids:
                    print(f"  ✓ Found template: {template_id}")
                else:
                    print(f"  ✗ Missing template: {template_id}")
        else:
            print(f"✗ Failed to retrieve templates: {response.status_code}")
    except Exception as e:
        print(f"✗ Error testing templates: {e}")
    
    # Test letter generation (this will use fallback since LM Studio is not running)
    print("\nTesting letter generation...")
    try:
        letter_data = {
            "description": "Нарушение СП31 в тендере LSR",
            "template_id": "compliance_sp31",
            "tone": -0.5,
            "dryness": 0.7,
            "humanity": 0.3,
            "length": "medium",
            "formality": "formal",
            "recipient": "ООО СтройПроект",
            "sender": "АО БЛДР",
            "subject": "Соответствие СП31"
        }
        
        response = requests.post(f"{base_url}/tools/generate_letter", json=letter_data)
        if response.status_code == 200:
            result = response.json()
            print("✓ Letter generation successful")
            print(f"  Status: {result.get('status')}")
            if 'letter' in result:
                print(f"  Letter length: {len(result['letter'])} characters")
                print(f"  First 100 chars: {result['letter'][:100]}...")
            if 'file_path' in result:
                print(f"  File path: {result['file_path']}")
        else:
            print(f"✗ Letter generation failed: {response.status_code}")
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"✗ Error testing letter generation: {e}")
    
    # Test letter improvement
    print("\nTesting letter improvement...")
    try:
        improve_data = {
            "draft": "Уважаемый клиент, у нас проблема с бетоном.",
            "description": "Concrete quality issues",
            "template_id": "compliance_sp31",
            "tone": 0.5,
            "dryness": 0.3,
            "humanity": 0.8,
            "length": "medium",
            "formality": "formal"
        }
        
        response = requests.post(f"{base_url}/tools/improve_letter", json=improve_data)
        if response.status_code == 200:
            result = response.json()
            print("✓ Letter improvement successful")
            print(f"  Status: {result.get('status')}")
            if 'letter' in result:
                print(f"  Letter length: {len(result['letter'])} characters")
                print(f"  First 100 chars: {result['letter'][:100]}...")
        else:
            print(f"✗ Letter improvement failed: {response.status_code}")
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"✗ Error testing letter improvement: {e}")

if __name__ == "__main__":
    print("Running end-to-end test for letter generation...")
    test_letter_generation_api()
    print("\nEnd-to-end test completed.")