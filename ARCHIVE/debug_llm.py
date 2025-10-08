#!/usr/bin/env python3
"""
Debug script to test LLM connection
"""

import os
os.environ["OPENAI_API_KEY"] = "not-needed"

from langchain_openai import ChatOpenAI

def test_llm_connection():
    """Test LLM connection"""
    print("Testing LLM connection...")
    
    # Initialize LLM
    llm = ChatOpenAI(
        base_url="http://localhost:1234/v1",
        model="deepseek-r1-0528-qwen3-8b",
        temperature=0.1
    )
    
    print("LLM initialized, sending test query...")
    
    # Test query
    try:
        response = llm.invoke("Say hello in one word")
        print(f"Response: {response}")
        if hasattr(response, 'content'):
            print(f"Content: {response.content}")
        else:
            print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_llm_connection()