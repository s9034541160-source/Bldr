"""
Show the implementation of the 14-stage pipeline
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def show_file_content(file_path, title):
    """Show the content of a file"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content[:2000])  # Show first 2000 characters
            if len(content) > 2000:
                print(f"\n... (file truncated, showing first 2000 of {len(content)} characters)")
    except Exception as e:
        print(f"Error reading file: {e}")

def show_implementation():
    """Show the implementation of the 14-stage pipeline"""
    print("🚀 Bldr Empire v2 - 14-Stage Symbiotic Pipeline Implementation")
    
    # Show regex_patterns.py
    show_file_content("regex_patterns.py", "regex_patterns.py - Regex Patterns for Pipeline Stages")
    
    # Show key methods from bldr_rag_trainer.py
    print(f"\n{'='*60}")
    print("scripts/bldr_rag_trainer.py - Key Pipeline Stage Methods")
    print(f"{'='*60}")
    
    # Read the trainer file
    try:
        with open("scripts/bldr_rag_trainer.py", 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Show the stage methods
        stages = [
            "_stage4_document_type_detection",
            "_stage5_structural_analysis", 
            "_stage6_regex_to_rubern",
            "_stage7_rubern_markup",
            "_stage8_metadata_extraction"
        ]
        
        for stage in stages:
            print(f"\n--- {stage} ---")
            # Find the method
            start = content.find(f"def {stage}")
            if start != -1:
                # Find the end (next method or end of file)
                next_method = content.find("def _stage", start + 10)
                if next_method == -1:
                    end = len(content)
                else:
                    end = next_method
                
                method_content = content[start:end]
                print(method_content[:800])  # Show first 800 characters
                if len(method_content) > 800:
                    print("... (method truncated)")
            else:
                print(f"Method {stage} not found")
                
    except Exception as e:
        print(f"Error reading trainer file: {e}")

if __name__ == "__main__":
    show_implementation()