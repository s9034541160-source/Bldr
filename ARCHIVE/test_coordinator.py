#!/usr/bin/env python3
"""
Test script for the Coordinator
"""

import sys
import os

# Add the core directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from core.coordinator import Coordinator
from core.model_manager import ModelManager
from core.tools_system import ToolsSystem

def main():
    print("Testing Coordinator initialization...")
    
    try:
        # Initialize the required components
        model_manager = ModelManager()
        tools_system = ToolsSystem(None, model_manager)  # Pass None for rag_system for now
        rag_system = None  # We don't have a real RAG system for testing
        
        # Initialize the coordinator
        coord = Coordinator(model_manager, tools_system, rag_system)
        print("✅ Coordinator initialized successfully!")
        
        # Test a simple request
        test_request = "Рассчитай смету для строительства фундамента"
        print(f"\nTesting request: {test_request}")
        
        # Analyze the request
        plan = coord.analyze_request(test_request)
        print(f"✅ Request analysis completed!")
        print(f"Plan: {plan}")
        
        # Try to process the request
        response = coord.process_request(test_request)
        print(f"✅ Request processing completed!")
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"❌ Error testing coordinator: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()