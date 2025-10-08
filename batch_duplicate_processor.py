#!/usr/bin/env python3
"""
Batch processor for eliminating duplicates with minimal user interaction.
This tool processes multiple functions in sequence with automated assistance.
"""

import csv
import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

def load_duplicate_tracker(csv_file):
    """Load the duplicate tracker CSV file."""
    duplicates = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert FileList back to a list
            file_list = row['FileList'].split(';') if row['FileList'] else []
            row['FileList'] = file_list
            duplicates.append(row)
    return duplicates

def save_duplicate_tracker(csv_file, duplicates):
    """Save the duplicate tracker CSV file."""
    fieldnames = ['FunctionName', 'FileCount', 'FileList', 'ChosenPrimaryFile', 'Status', 'Notes']
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in duplicates:
            # Convert FileList back to semicolon-separated string
            row['FileList'] = ';'.join(row['FileList']) if isinstance(row['FileList'], list) else row['FileList']
            writer.writerow(row)

def get_functions_by_status(duplicates, status):
    """Get all functions with a specific status."""
    return [d for d in duplicates if d['Status'] == status]

def get_functions_by_priority(duplicates, status='Pending'):
    """Get functions sorted by priority (file count descending)."""
    filtered = [d for d in duplicates if d['Status'] == status]
    filtered.sort(key=lambda x: int(x['FileCount']), reverse=True)
    return filtered

def auto_analyze_function(func_data):
    """Perform automated analysis of a function."""
    func_name = func_data['FunctionName']
    primary_file = func_data['ChosenPrimaryFile']
    file_list = func_data['FileList']
    file_count = int(func_data['FileCount'])
    
    print(f"\n🔬 AUTO-ANALYZING: {func_name} ({file_count} duplicates)")
    print("-" * 60)
    
    # Basic analysis
    analysis = {
        'function_name': func_name,
        'primary_file': primary_file,
        'duplicate_count': file_count,
        'archive_files': 0,
        'recent_files': 0,
        'core_files': 0,
        'tool_files': 0,
        'agent_files': 0,
        'recommendation': 'review'
    }
    
    # Categorize files
    for file_path in file_list:
        if 'archive' in file_path.lower() or 'backup' in file_path.lower():
            analysis['archive_files'] += 1
        elif 'core' in file_path.lower():
            analysis['core_files'] += 1
        elif 'tool' in file_path.lower():
            analysis['tool_files'] += 1
        elif 'agent' in file_path.lower():
            analysis['agent_files'] += 1
        
        # Check if file is recent (this would need actual file system checks)
        # For now, we'll just note it as a possibility
    
    # Make recommendation based on analysis
    if analysis['archive_files'] > 0:
        analysis['recommendation'] = 'high_priority_cleanup'
    elif analysis['core_files'] > 0:
        analysis['recommendation'] = 'careful_merge'
    elif analysis['tool_files'] > 0:
        analysis['recommendation'] = 'standard_merge'
    
    # Print analysis
    print(f"Primary file: {os.path.basename(primary_file)}")
    print(f"Archive files: {analysis['archive_files']}")
    print(f"Core files: {analysis['core_files']}")
    print(f"Tool files: {analysis['tool_files']}")
    print(f"Agent files: {analysis['agent_files']}")
    print(f"Recommendation: {analysis['recommendation']}")
    
    return analysis

def generate_batch_report(analysis_results, output_file=None):
    """Generate a batch processing report."""
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"batch_processing_report_{timestamp}.md"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# BATCH DUPLICATE PROCESSING REPORT\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 📊 ANALYSIS SUMMARY\n\n")
        f.write(f"Processed {len(analysis_results)} functions:\n\n")
        
        # Categorize by recommendation
        recommendations = {}
        for result in analysis_results:
            rec = result['recommendation']
            if rec not in recommendations:
                recommendations[rec] = []
            recommendations[rec].append(result)
        
        for rec, funcs in recommendations.items():
            f.write(f"### {rec.upper().replace('_', ' ')} ({len(funcs)} functions)\n\n")
            for func in funcs:
                f.write(f"- **{func['function_name']}** ({func['duplicate_count']} duplicates)\n")
                f.write(f"  - Primary: {os.path.basename(func['primary_file'])}\n")
                f.write(f"  - Archive: {func['archive_files']}, Core: {func['core_files']}, "
                       f"Tool: {func['tool_files']}, Agent: {func['agent_files']}\n\n")
    
    print(f"📄 Batch report saved to: {output_file}")
    return output_file

def process_batch(duplicates, max_functions=10):
    """Process a batch of functions with automated analysis."""
    print("🤖 BATCH DUPLICATE PROCESSOR")
    print("=" * 50)
    
    # Get pending functions sorted by priority
    pending_functions = get_functions_by_priority(duplicates, 'Pending')
    
    if not pending_functions:
        print("✅ No pending functions found!")
        return []
    
    print(f"Found {len(pending_functions)} pending functions")
    print(f"Processing up to {max_functions} functions in this batch")
    
    # Process functions
    analysis_results = []
    processed_count = 0
    
    for func_data in pending_functions:
        if processed_count >= max_functions:
            break
            
        analysis = auto_analyze_function(func_data)
        analysis_results.append(analysis)
        processed_count += 1
    
    # Generate report
    report_file = generate_batch_report(analysis_results)
    
    print(f"\n✅ Batch processing complete!")
    print(f"📊 Analyzed {len(analysis_results)} functions")
    print(f"📄 Report saved to: {report_file}")
    print(f"\n📋 Next steps:")
    print(f"   1. Review the batch report: {report_file}")
    print(f"   2. Start with high priority functions (archive files)")
    print(f"   3. Use semi_automated_duplicate_eliminator.py for detailed processing")
    
    return analysis_results

def main():
    """Main batch processor."""
    csv_file = "duplication_master_list_updated.csv"
    
    print("🚀 Bldr Empire - Batch Duplicate Processor")
    print("=" * 50)
    
    # Check if CSV exists
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        print("   Please run the duplicate elimination workflow first.")
        return
    
    # Load duplicates
    duplicates = load_duplicate_tracker(csv_file)
    print(f"✅ Loaded {len(duplicates)} duplicate functions")
    
    # Process batch
    results = process_batch(duplicates, max_functions=20)
    
    if results:
        # Show summary
        print(f"\n🔍 BATCH ANALYSIS SUMMARY")
        print("=" * 30)
        
        # Count by recommendation
        rec_counts = {}
        for result in results:
            rec = result['recommendation']
            rec_counts[rec] = rec_counts.get(rec, 0) + 1
        
        for rec, count in rec_counts.items():
            print(f"{rec.replace('_', ' ').title()}: {count} functions")

if __name__ == "__main__":
    main()