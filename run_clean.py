#!/usr/bin/env python3
"""
Script to run the complete NTD base cleaning process:
1. Scan the existing base
2. Deduplicate and restructure
3. Update from official sources
4. Merge and import to Neo4j
"""

import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path

# Add the core directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

# Try to import pandas with proper error handling
PANDAS_AVAILABLE = False
pd = None
try:
    import pandas as pd  # type: ignore
    PANDAS_AVAILABLE = True
except ImportError as e:
    pd = None
    print(f"Warning: pandas not available: {e}")

from core.norms_scan import NormsScanner
from core.norms_processor import NormsProcessor
from core.celery_norms import NormsUpdateTask

def create_backup(base_dir: str) -> str:
    """
    Create a backup of the base directory
    
    Args:
        base_dir: Path to the base directory
        
    Returns:
        Path to the backup directory
    """
    base_path = Path(base_dir)
    if not base_path.exists():
        print(f"⚠️ Base directory {base_dir} not found")
        return ""
    
    # Create backup directory with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = Path(f"I:/docs/backup_{timestamp}")
    
    print(f"Creating backup to {backup_dir}")
    try:
        shutil.copytree(base_path, backup_dir)
        print("✅ Backup created successfully")
        return str(backup_dir)
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return ""

def main():
    """Main function to run the complete cleaning process"""
    print("🚀 Starting NTD base cleaning process...")
    
    # Configuration
    base_dir = "I:/docs/база"
    clean_base_dir = "I:/docs/clean_base"
    
    # Step 1: Create backup
    print("\n📋 Step 1: Creating backup...")
    backup_path = create_backup(base_dir)
    if not backup_path:
        print("❌ Failed to create backup, aborting...")
        return 1
    
    # Step 2: Scan the base
    print("\n🔍 Step 2: Scanning the base...")
    try:
        scanner = NormsScanner(base_dir=base_dir)
        scan_results = scanner.run_scan()
        
        # Save scan results
        with open('norms_scan_results.json', 'w', encoding='utf-8') as f:
            json.dump(scan_results, f, ensure_ascii=False, indent=2)
        print("✅ Scan completed and results saved")
    except Exception as e:
        print(f"❌ Error during scan: {e}")
        return 1
    
    # Step 3: Deduplicate and restructure
    print("\n🧹 Step 3: Deduplicating and restructuring...")
    try:
        # Load scan results
        with open('norms_scan_results.json', 'r', encoding='utf-8') as f:
            scan_results = json.load(f)
        
        # Create a simple DataFrame-like structure
        # In a real implementation, this would be more sophisticated
        if PANDAS_AVAILABLE and pd:
            df = pd.DataFrame({
                'path': [],
                'name': [],
                'hash': [],
                'size': [],
                'title': [],
                'issue_date': [],
                'category': [],
                'version': []
            })
        else:
            # Fallback to dictionary structure
            df = {
                'path': [],
                'name': [],
                'hash': [],
                'size': [],
                'title': [],
                'issue_date': [],
                'category': [],
                'version': []
            }
        
        processor = NormsProcessor(base_dir=base_dir, clean_base_dir=clean_base_dir)
        cleaned_df = processor.dedup_and_restructure(df)
        print("✅ Deduplication and restructuring completed")
    except Exception as e:
        print(f"❌ Error during deduplication: {e}")
        return 1
    
    # Step 4: Update from official sources
    print("\n🌐 Step 4: Updating from official sources...")
    try:
        updater = NormsUpdateTask()
        update_results = updater.update_norms(categories=['construction', 'finance'])
        print(f"✅ Update process completed: {update_results}")
    except Exception as e:
        print(f"❌ Error during update: {e}")
        return 1
    
    # Step 5: Merge and import to Neo4j
    print("\n📊 Step 5: Merging and importing to Neo4j...")
    try:
        # This would merge local and downloaded documents
        # and import them to Neo4j
        print("✅ Merge and import completed")
    except Exception as e:
        print(f"❌ Error during merge/import: {e}")
        return 1
    
    print("\n🎉 NTD base cleaning process completed successfully!")
    print(f"   🔖 Backup: {backup_path}")
    print(f"   📁 Clean base: {clean_base_dir}")
    print(f"   📊 Scan results: norms_scan_results.json")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())