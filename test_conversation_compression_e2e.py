#!/usr/bin/env python3
"""End-to-end test for conversation history compression with coordinator and roles agents"""

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from core.agents.coordinator_agent import CoordinatorAgent
from core.agents.roles_agents import RolesAgentsManager
from core.agents.conversation_history_compressed import compressed_conversation_history

def test_conversation_compression_e2e():
    """End-to-end test for conversation history compression"""
    user_id = "e2e_test_user"
    
    # Clear any existing history for this user
    compressed_conversation_history.clear_history(user_id)
    
    # Initialize coordinator agent
    coordinator = CoordinatorAgent(lm_studio_url="http://localhost:1234/v1")
    
    # Set request context
    coordinator.set_request_context({
        "user_id": user_id,
        "channel": "ai_shell"
    })
    
    # Test 1: Simple greeting query (should use early exit)
    print("=== Test 1: Simple greeting query ===")
    greeting_query = "Привет!"
    greeting_response = coordinator.process_query(greeting_query)
    print(f"Query: {greeting_query}")
    print(f"Response: {greeting_response}")
    print()
    
    # Test 2: Self-introduction query (should use early exit)
    print("=== Test 2: Self-introduction query ===")
    intro_query = "Расскажи о себе"
    intro_response = coordinator.process_query(intro_query)
    print(f"Query: {intro_query}")
    print(f"Response: {intro_response}")
    print()
    
    # Test 3: Multiple construction-related queries to trigger compression
    print("=== Test 3: Multiple construction queries ===")
    construction_queries = [
        "Как рассчитать смету для ленточного фундамента?",
        "Какие нормы СП нужно учитывать при проектировании железобетонных конструкций?",
        "Как выполнить расчет несущей способности свай?",
        "Какие требования по охране труда при производстве бетонных работ?",
        "Как составить проект производства работ для устройства фундаментов?",
        "Какие документы нужны для сдачи объекта в эксплуатацию?",
        "Как рассчитать объем земляных работ для котлована?",
        "Какие материалы использовать для гидроизоляции фундамента?",
        "Как выполнить теплотехнический расчет наружных стен?",
        "Какие требования к качеству бетона по ГОСТ?",
        "Как составить акт скрытых работ при армировании фундамента?",
        "Какие нормы расхода материалов по ГЭСН для отделочных работ?"
    ]
    
    for i, query in enumerate(construction_queries):
        print(f"Query {i+1}: {query}")
        response = coordinator.process_query(query)
        print(f"Response: {response[:200]}..." if len(response) > 200 else f"Response: {response}")
        print()
    
    # Get history stats
    stats = compressed_conversation_history.get_history_stats(user_id)
    print("=== Conversation History Stats ===")
    print(f"Total messages: {stats['total_messages']}")
    print(f"Total tokens: {stats['total_tokens']}")
    print(f"Summary count: {stats['summary_count']}")
    print(f"Recent messages: {stats['recent_messages']}")
    print()
    
    # Get formatted history
    formatted_history = compressed_conversation_history.get_formatted_history(user_id)
    print("=== Formatted History (first 500 chars) ===")
    print(formatted_history[:500] + "..." if len(formatted_history) > 500 else formatted_history)
    print()
    
    # Get full history
    full_history = compressed_conversation_history.get_full_history(user_id)
    print("=== Full History Analysis ===")
    summary_count = sum(1 for msg in full_history if msg["role"] == "summary")
    user_msg_count = sum(1 for msg in full_history if msg["role"] == "user")
    assistant_msg_count = sum(1 for msg in full_history if msg["role"] == "assistant")
    
    print(f"Full history length: {len(full_history)}")
    print(f"Summary messages: {summary_count}")
    print(f"User messages: {user_msg_count}")
    print(f"Assistant messages: {assistant_msg_count}")
    print()
    
    # Test 4: Roles agents manager with context
    print("=== Test 4: Roles agents with compressed history ===")
    roles_manager = RolesAgentsManager(lm_studio_url="http://localhost:1234/v1")
    
    # Get formatted history for a role agent
    role_history = compressed_conversation_history.get_formatted_history(user_id, max_tokens=300)
    print("Role agent context (first 300 chars):")
    print(role_history[:300] + "..." if len(role_history) > 300 else role_history)
    print()
    
    # Clear history
    compressed_conversation_history.clear_history(user_id)
    print("=== History cleared ===")

if __name__ == "__main__":
    test_conversation_compression_e2e()