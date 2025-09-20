#!/usr/bin/env python3
"""
Test script to verify the authentication welcome message fix.
This script checks that the welcome message displays the username instead of the role.
"""

import os
import re

def check_auth_header():
    """Check that AuthHeader.tsx displays username in welcome messages."""
    auth_header_path = "web/bldr_dashboard/src/components/AuthHeader.tsx"
    if not os.path.exists(auth_header_path):
        print("❌ AuthHeader.tsx not found")
        return False
    
    with open(auth_header_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that welcome messages use username, not role
    welcome_messages = re.findall(r'Добро пожаловать, \$\{user\.(\w+)!\}', content)
    
    if not welcome_messages:
        print("❌ No welcome messages found")
        return False
    
    # All welcome messages should use username
    for msg_var in welcome_messages:
        if msg_var != 'username':
            print(f"❌ Welcome message uses '{msg_var}' instead of 'username'")
            return False
    
    print("✅ AuthHeader.tsx correctly displays username in welcome messages")
    return True

def main():
    """Main test function."""
    print("Testing authentication welcome message fix...\n")
    
    if check_auth_header():
        print("\n🎉 Authentication welcome message fix verified successfully!")
        print("The system will now display 'Добро пожаловать, [username]!' instead of 'Добро пожаловать, [role]!'")
        return 0
    else:
        print("\n❌ Authentication welcome message fix verification failed!")
        return 1

if __name__ == "__main__":
    exit(main())