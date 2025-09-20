#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple test script for the Normative Technical Documentation (NTD) system
"""

import sys
from pathlib import Path

# Add the core directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "core"))

def test_ntd_import():
    """Test that we can import the NTD modules"""
    try:
        import ntd_preprocessor
        print("✅ Successfully imported ntd_preprocessor")
        return True
    except ImportError as e:
        print(f"❌ Failed to import ntd_preprocessor: {e}")
        return False

def test_ntd_initialization():
    """Test NTD system initialization"""
    try:
        from ntd_preprocessor import initialize_ntd_system
        normative_db, normative_checker = initialize_ntd_system("./data")
        print("✅ Successfully initialized NTD system")
        print(f"   Loaded {len(normative_db.documents)} documents")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize NTD system: {e}")
        return False

def test_document_retrieval():
    """Test document retrieval functionality"""
    try:
        from ntd_preprocessor import initialize_ntd_system
        normative_db, normative_checker = initialize_ntd_system("./data")
        
        # Try to get a specific document
        doc = normative_db.get_document("СП 20.13330.2016")
        if doc:
            print("✅ Successfully retrieved document")
            print(f"   Code: {doc.code}")
            print(f"   Title: {doc.title}")
            print(f"   Category: {doc.category}")
            return True
        else:
            print("❌ Document not found")
            return False
    except Exception as e:
        print(f"❌ Failed document retrieval test: {e}")
        return False

if __name__ == "__main__":
    print("Running NTD System Tests...\n")
    
    tests = [
        test_ntd_import,
        test_ntd_initialization,
        test_document_retrieval
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)