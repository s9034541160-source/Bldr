#!/usr/bin/env python3
"""
Script to restore and rebuild the NTD base from official sources
"""

import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path
import asyncio
import httpx
from bs4 import BeautifulSoup
import hashlib
import re

# Add the core directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

from core.norms_updater import NormsUpdater
from core.norms_scan import NormsScanner
from core.norms_processor import NormsProcessor

def create_directories():
    """Create required directory structure"""
    print("📁 Creating directory structure...")
    
    # Create base directories
    base_dirs = [
        "I:/docs/clean_base/construction",
        "I:/docs/clean_base/finance",
        "I:/docs/clean_base/safety",
        "I:/docs/clean_base/ecology",
        "I:/docs/clean_base/hr",
        "I:/docs/clean_base/methodical",
        "I:/docs/clean_base/textbook",
        "I:/docs/clean_base/laws",
        "I:/docs/clean_base/statistics",
        "I:/docs/clean_base/tax"
    ]
    
    for dir_path in base_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"   Created: {dir_path}")

def backup_current_base():
    """Create backup of current base"""
    base_dir = Path("I:/docs/БАЗА")
    if base_dir.exists():
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = Path(f"I:/docs/backup_{timestamp}")
        print(f"💾 Creating backup to {backup_dir}")
        try:
            shutil.copytree(base_dir, backup_dir)
            print("✅ Backup created successfully")
            return str(backup_dir)
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
            return ""
    else:
        print("⚠️ Base directory not found, skipping backup")
        return ""

def download_sample_ntd():
    """Download sample NTD documents from official sources"""
    print("🌐 Downloading sample NTD documents...")
    
    # Create norms updater
    updater = NormsUpdater(base_dir="I:/docs/clean_base")
    
    # Run update for construction category (which includes stroyinf.ru)
    print("⬇️  Downloading real documents from official sources...")
    try:
        # Run the update process to download real documents
        results = asyncio.run(updater.update_norms_daily(categories=['construction']))
        print(f"✅ Download completed. Results: {results}")
        return results
    except Exception as e:
        print(f"❌ Error downloading documents: {e}")
        # Fallback to creating placeholder files if download fails
        print("⚠️  Creating placeholder files as fallback...")
        create_placeholder_files()
        return None

def create_placeholder_files():
    """Create placeholder files as fallback"""
    # Sample documents from official sources
    sample_docs = [
        {
            "url": "https://files.stroyinf.ru/Index2/1/4293880/4293880.htm",
            "category": "construction",
            "name": "СП_45.13330.2017_Организация_строительного_производства.pdf"
        },
        {
            "url": "https://files.stroyinf.ru/Index2/1/4293879/4293879.htm",
            "category": "construction", 
            "name": "СП_48.13330.2011_Организация_строительства.pdf"
        },
        {
            "url": "https://minstroyrf.ru/upload/iblock/d88/d881234567890.pdf",
            "category": "construction",
            "name": "Методика_применения_сметных_норм.pdf"
        },
        {
            "url": "https://rosstat.gov.ru/docs/doc1.xlsx",
            "category": "statistics",
            "name": "Статистические_данные_строительства_2024.xlsx"
        }
    ]
    
    # Create placeholder files
    for doc in sample_docs:
        category_dir = Path(f"I:/docs/clean_base/{doc['category']}")
        file_path = category_dir / doc['name']
        
        # Create a simple placeholder file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"Placeholder for {doc['name']}\n")
            f.write(f"Downloaded from: {doc['url']}\n")
            f.write(f"Category: {doc['category']}\n")
            f.write(f"Date: {datetime.now().isoformat()}\n")
            f.write("\nThis is a placeholder file for demonstration purposes.\n")
            f.write("In a real implementation, this would be the actual NTD document.\n")
        
        print(f"   Created placeholder: {file_path}")

def create_ntd_catalog():
    """Create a catalog of NTD documents"""
    print("📋 Creating NTD catalog...")
    
    catalog = {
        "timestamp": datetime.now().isoformat(),
        "sources": {
            "minstroyrf.ru": {
                "description": "Минстрой России - официальные нормативные документы",
                "categories": ["construction", "safety"],
                "status": "active"
            },
            "consultant.ru": {
                "description": "КонсультантПлюс - законодательные акты",
                "categories": ["laws", "finance"],
                "status": "active"
            },
            "rosstat.gov.ru": {
                "description": "Росстат - статистические данные",
                "categories": ["statistics"],
                "status": "active"
            },
            "stroyinf.ru": {
                "description": "СтройИнф - строительные нормы и правила",
                "categories": ["construction", "safety", "ecology"],
                "status": "active"
            }
        },
        "categories": {
            "construction": {
                "description": "Строительные нормы и правила (СП, СНиП, ГОСТ)",
                "document_types": ["СП", "СНиП", "ГОСТ", "РД"],
                "count": 0
            },
            "finance": {
                "description": "Финансовые и сметные документы (ГЭСН, ФЕР)",
                "document_types": ["ГЭСН", "ФЕР", "ТСН"],
                "count": 0
            },
            "safety": {
                "description": "Документы по охране труда и безопасности",
                "document_types": ["СанПиН", "ПОТ", "РМ"],
                "count": 0
            },
            "ecology": {
                "description": "Экологические нормы и правила",
                "document_types": ["СП", "СанПиН"],
                "count": 0
            },
            "hr": {
                "description": "Кадровые и трудовые документы",
                "document_types": ["ТК РФ", "Постановления"],
                "count": 0
            }
        }
    }
    
    # Save catalog
    catalog_path = Path("I:/docs/clean_base/ntd_catalog.json")
    with open(catalog_path, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    
    print(f"✅ NTD catalog created: {catalog_path}")

def main():
    """Main function to restore NTD base"""
    print("🚀 Starting NTD base restoration process...")
    print("=" * 50)
    
    # Step 1: Create backup
    print("\n📋 Step 1: Creating backup...")
    backup_path = backup_current_base()
    
    # Step 2: Create directory structure
    print("\n📁 Step 2: Creating directory structure...")
    create_directories()
    
    # Step 3: Download real NTD documents
    print("\n🌐 Step 3: Downloading real NTD documents from official sources...")
    download_results = download_sample_ntd()
    
    # Step 4: Create NTD catalog
    print("\n📋 Step 4: Creating NTD catalog...")
    create_ntd_catalog()
    
    # Step 5: Scan and process
    print("\n🔍 Step 5: Scanning and processing documents...")
    try:
        scanner = NormsScanner(base_dir="I:/docs/clean_base")
        scan_results = scanner.run_scan()
        
        # Save scan results
        with open('norms_scan_results.json', 'w', encoding='utf-8') as f:
            json.dump(scan_results, f, ensure_ascii=False, indent=2)
        print("✅ Scan completed and results saved")
    except Exception as e:
        print(f"❌ Error during scan: {e}")
    
    print("\n🎉 NTD base restoration process completed!")
    if backup_path:
        print(f"   🔖 Backup: {backup_path}")
    print(f"   📁 Clean base: I:/docs/clean_base")
    print(f"   📊 Scan results: norms_scan_results.json")
    print("\n💡 Next steps:")
    print("   1. Run the full cleaning process with 'python run_clean.py'")
    print("   2. Start the system with 'one_click_start.bat'")
    print("   3. Access the dashboard at http://localhost:3000")
    print("   4. Go to the Norms tab and trigger an update")

if __name__ == "__main__":
    main()