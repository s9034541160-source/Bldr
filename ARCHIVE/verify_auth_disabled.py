#!/usr/bin/env python3
"""
Verification script to check if authentication is properly disabled
"""

import os
from dotenv import load_dotenv

def verify_auth_disabled():
    """Verify that SKIP_AUTH is set to true in the .env file"""
    # Load environment variables
    load_dotenv()
    
    print("Verifying authentication disabled configuration...")
    
    # Check if SKIP_AUTH is set to true
    skip_auth = os.getenv('SKIP_AUTH', 'false')
    print(f"SKIP_AUTH = {skip_auth}")
    
    if skip_auth.lower() == 'true':
        print("\n✅ Authentication is disabled!")
        print("You should now be able to access the system without login.")
        return True
    else:
        print("\n❌ Authentication is still enabled!")
        print("Set SKIP_AUTH=true in your .env file to disable authentication.")
        return False

if __name__ == "__main__":
    verify_auth_disabled()