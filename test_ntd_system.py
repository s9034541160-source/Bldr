#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the Normative Technical Documentation (NTD) system
"""

import os
import sys
import json
from pathlib import Path

# Add the core directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "core"))

try:
    from ntd_preprocessor import initialize_ntd_system, NormativeDatabase, NormativeChecker
except ImportError as e:
    print(f"Import error: {e}")
    # Try alternative import path
    try:
        import core.ntd_preprocessor as ntd_preprocessor
        initialize_ntd_system = ntd_preprocessor.initialize_ntd_system
        NormativeDatabase = ntd_preprocessor.NormativeDatabase
        NormativeChecker = ntd_preprocessor.NormativeChecker
    except ImportError as e2:
        print(f"Alternative import also failed: {e2}")
        sys.exit(1)

def test_ntd_system():
    """Test the NTD system functionality"""
    print("Testing NTD System...")
    
    # Initialize the NTD system
    base_dir = "./data"
    normative_db, normative_checker = initialize_ntd_system(base_dir)
    
    # Test 1: Check that documents were loaded
    print(f"\n1. Loaded {len(normative_db.documents)} normative documents")
    assert len(normative_db.documents) > 0, "No documents loaded"
    
    # Test 2: Check specific document retrieval
    test_code = "СП 20.13330.2016"
    doc = normative_db.get_document(test_code)
    print(f"\n2. Retrieved document: {test_code}")
    if doc:
        print(f"   Title: {doc.title}")
        print(f"   Category: {doc.category}")
        print(f"   Status: {doc.status}")
        assert doc.code == test_code, "Document code mismatch"
    else:
        print("   Document not found")
        assert False, f"Document {test_code} not found"
    
    # Test 3: Search for documents
    search_results = normative_db.search_documents("строительство", "construction")
    print(f"\n3. Found {len(search_results)} construction documents")
    assert len(search_results) > 0, "No construction documents found"
    
    # Test 4: Check document actuality
    is_actual = normative_db.is_document_actual(test_code)
    print(f"\n4. Document {test_code} is actual: {is_actual}")
    assert is_actual, f"Document {test_code} should be actual"
    
    # Test 5: Test document extraction
    test_info = normative_checker.extract_document_info("сп2309257.pdf")
    print(f"\n5. Extracted document info from filename: {test_info}")
    
    # Test 6: Check document processing
    check_result = normative_checker.check_document_actual("сп2309257.pdf")
    print(f"\n6. Document check result: {check_result['status']}")
    
    # Test 7: Verify folder structure
    base_dir_env = os.getenv("BASE_DIR", "I:/docs")
    folders = os.listdir(os.path.join(base_dir_env, "01. НТД"))
    print(f"\n7. Created category folders: {folders}")
    assert len(folders) >= 10, "Not all category folders created"
    
    print("\n✅ All tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_ntd_system()
        print("\n🎉 NTD System Test Completed Successfully!")
    except Exception as e:
        print(f"\n❌ NTD System Test Failed: {e}")
        sys.exit(1)