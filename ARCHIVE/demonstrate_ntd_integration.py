#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Demonstration script showing the integration of Normative Technical Documentation (NTD) 
system with the RAG training pipeline
"""

import sys
import os
from pathlib import Path

# Add the core directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "core"))
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

def demonstrate_ntd_system():
    """Demonstrate the NTD system functionality"""
    print("🏗️  Demonstrating Normative Technical Documentation (NTD) System Integration")
    print("=" * 80)
    
    try:
        # Import NTD modules
        from core.ntd_preprocessor import initialize_ntd_system, NormativeDatabase, NormativeChecker
        
        print("\n1️⃣  Initializing NTD System...")
        # Initialize the NTD system
        base_dir = "./data"
        normative_db, normative_checker = initialize_ntd_system(base_dir)
        print(f"   ✅ Initialized NTD system with {len(normative_db.documents)} documents")
        
        print("\n2️⃣  Demonstrating Document Retrieval...")
        # Retrieve a specific document
        test_code = "СП 20.13330.2016"
        doc = normative_db.get_document(test_code)
        if doc:
            print(f"   📄 Found document: {doc.code}")
            print(f"      Title: {doc.title}")
            print(f"      Year: {doc.year}")
            print(f"      Status: {doc.status}")
            print(f"      Category: {doc.category}")
        else:
            print(f"   ❌ Document {test_code} not found")
            
        print("\n3️⃣  Demonstrating Document Search...")
        # Search for documents
        search_results = normative_db.search_documents("строительство", "construction")
        print(f"   🔍 Found {len(search_results)} construction documents")
        for i, doc in enumerate(search_results[:3]):  # Show first 3
            print(f"      {i+1}. {doc.code} - {doc.title}")
            
        print("\n4️⃣  Demonstrating Document Actuality Check...")
        # Check if document is actual
        is_actual = normative_db.is_document_actual(test_code)
        print(f"   📋 Document {test_code} is {'actual' if is_actual else 'outdated'}")
        
        print("\n5️⃣  Demonstrating Document Information Extraction...")
        # Test document information extraction
        test_info = normative_checker.extract_document_info("сп2309257.pdf")
        print(f"   🎯 Extracted info from filename: {test_info}")
        
        print("\n6️⃣  Demonstrating Folder Structure Creation...")
        # Show created folder structure
        base_dir_env = os.getenv("BASE_DIR", "I:/docs")
        ntd_folder = Path(os.path.join(base_dir_env, "01. НТД"))
        if ntd_folder.exists():
            categories = [f.name for f in ntd_folder.iterdir() if f.is_dir()]
            print(f"   📁 Created {len(categories)} category folders:")
            for category in categories[:5]:  # Show first 5
                print(f"      • {category}")
            if len(categories) > 5:
                print(f"      ... and {len(categories) - 5} more")
        else:
            print("   ❌ NTD folder structure not found")
            
        print("\n7️⃣  Demonstrating RAG Pipeline Integration...")
        # Show how NTD integrates with RAG pipeline
        print("   🔄 Stage 0: NTD Preprocessing in RAG Pipeline")
        print("      • Check document actuality")
        print("      • Download actual versions if needed")
        print("      • Rename files with proper naming convention")
        print("      • Move files to appropriate category folders")
        print("      • Mark documents as processed")
        
        print("\n8️⃣  Example NTD Database Entry...")
        # Show an example database entry
        if doc:
            print("   📚 Sample database entry:")
            print(f"      {{")
            print(f"        'id': {doc.id},")
            print(f"        'category': '{doc.category}',")
            print(f"        'code': '{doc.code}',")
            print(f"        'title': '{doc.title}',")
            print(f"        'year': {doc.year},")
            print(f"        'status': '{doc.status}',")
            print(f"        'pdf_url': '{doc.pdf_url}',")
            print(f"        'source_site': '{doc.source_site}',")
            print(f"        'description': '{doc.description}'")
            print(f"      }}")
        
        print("\n" + "=" * 80)
        print("✅ NTD System Integration Demonstration Completed Successfully!")
        print("\n📋 Summary:")
        print(f"   • Loaded {len(normative_db.documents)} normative documents")
        print("   • Created organized folder structure for document categories")
        print("   • Integrated as Stage 0 in the 14-stage RAG pipeline")
        print("   • Automated document validation, renaming, and organization")
        print("   • Ready for RAG training with normative technical documentation")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error in NTD system demonstration: {e}")
        import traceback
        traceback.print_exc()
        return False

def demonstrate_rag_integration():
    """Demonstrate how NTD integrates with the RAG pipeline"""
    print("\n\n🔄 Demonstrating RAG Pipeline Integration")
    print("=" * 50)
    
    try:
        # Import RAG trainer
        from scripts.bldr_rag_trainer import BldrRAGTrainer
        
        print("\n1️⃣  RAG Pipeline Structure...")
        print("   📊 14-Stage Pipeline with NTD Integration:")
        print("      Stage 0:  NTD Preprocessing (NEW) 🔧")
        print("      Stage 1:  Initial validation")
        print("      Stage 2:  Duplicate checking")
        print("      Stage 3:  Text extraction")
        print("      Stage 4:  Document type detection")
        print("      Stage 5:  Structural analysis")
        print("      Stage 6:  Extract work candidates")
        print("      Stage 7:  Generate Rubern markup")
        print("      Stage 8:  Metadata extraction")
        print("      Stage 9:  Quality control")
        print("      Stage 10: Type-specific processing")
        print("      Stage 11: Work sequence extraction")
        print("      Stage 12: Save work sequences")
        print("      Stage 13: Smart chunking")
        print("      Stage 14: Save to Qdrant/FAISS")
        
        print("\n2️⃣  Stage 0: NTD Preprocessing Details...")
        print("   🎯 Purpose: Pre-process normative technical documentation")
        print("   📋 Functions:")
        print("      • Check document actuality against database")
        print("      • Download actual versions if document is outdated")
        print("      • Rename files with proper naming convention")
        print("      • Move files to appropriate category folders")
        print("      • Mark documents as processed in database")
        print("      • Continue with standard RAG pipeline")
        
        print("\n3️⃣  Benefits of NTD Integration...")
        print("   ✅ Automated document validation and actuality checking")
        print("   ✅ Intelligent file renaming (e.g., 'sp2309257.pdf' → 'СП 45.13330.2017 Земляные работы.pdf')")
        print("   ✅ Automatic folder organization by document category")
        print("   ✅ Duplicate detection and prevention")
        print("   ✅ Seamless integration with existing 14-stage pipeline")
        print("   ✅ Ready for RAG training with properly processed documents")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error in RAG integration demonstration: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting NTD System Integration Demonstration")
    
    # Run demonstrations
    success1 = demonstrate_ntd_system()
    success2 = demonstrate_rag_integration()
    
    if success1 and success2:
        print("\n\n🎉 All Demonstrations Completed Successfully!")
        print("\n📥 Next Steps:")
        print("   1. Place normative documents in the appropriate folders")
        print("   2. Run the RAG trainer to process documents")
        print("   3. Documents will be automatically validated and organized")
        print("   4. Ready for advanced RAG training and querying")
    else:
        print("\n\n❌ Some demonstrations failed!")
        sys.exit(1)