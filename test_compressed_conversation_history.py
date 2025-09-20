#!/usr/bin/env python3
"""Test script to verify compressed conversation history functionality"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from core.agents.conversation_history_compressed import compressed_conversation_history

def test_compressed_conversation_history():
    """Test compressed conversation history functionality"""
    user_id = "test_user_compressed"
    
    # Clear any existing history for this user
    compressed_conversation_history.clear_history(user_id)
    
    # Add some messages
    compressed_conversation_history.add_message(user_id, {
        "role": "user",
        "content": "Привет, как дела?"
    })
    
    compressed_conversation_history.add_message(user_id, {
        "role": "assistant",
        "content": "Привет! У меня всё хорошо, спасибо. Как я могу вам помочь?"
    })
    
    compressed_conversation_history.add_message(user_id, {
        "role": "user",
        "content": "Расскажи о себе"
    })
    
    compressed_conversation_history.add_message(user_id, {
        "role": "assistant",
        "content": "Я - многофункциональный строительный ассистент, созданный для помощи в различных аспектах строительства. Я могу помочь с:\n\n1. Поиском и анализом строительных норм и правил (СП, ГОСТ, СНиП)\n2. Расчетом смет и бюджетов\n3. Созданием проектной документации\n4. Анализом изображений строительных объектов\n5. Генерацией официальных писем и документов\n6. Планированием строительных работ\n\nМоя цель - сделать вашу работу в строительной сфере более эффективной и точной."
    })
    
    # Add more messages to trigger compression
    for i in range(15):
        compressed_conversation_history.add_message(user_id, {
            "role": "user",
            "content": f"Вопрос {i+1}: Как рассчитать смету для фундамента?"
        })
        
        compressed_conversation_history.add_message(user_id, {
            "role": "assistant",
            "content": f"Для расчета сметы фундамента необходимо учитывать несколько факторов. Основные шаги включают:\n\n1. Определение типа фундамента (ленточный, свайный, плитный)\n2. Расчет объема бетона и арматуры\n3. Учет стоимости материалов и работ\n4. Применение коэффициентов по СП 52-101-2003\n\nРекомендую обратиться к ГЭСН 81-02-06-2001 для получения актуальных расценок."
        })
    
    # Get history stats
    stats = compressed_conversation_history.get_history_stats(user_id)
    print("Conversation history stats:")
    print(f"  Total messages: {stats['total_messages']}")
    print(f"  Total tokens: {stats['total_tokens']}")
    print(f"  Summary count: {stats['summary_count']}")
    print(f"  Recent messages: {stats['recent_messages']}")
    
    # Get formatted history
    formatted_history = compressed_conversation_history.get_formatted_history(user_id)
    print("\nFormatted history (first 500 chars):")
    print(formatted_history[:500] + "..." if len(formatted_history) > 500 else formatted_history)
    
    # Get full history
    full_history = compressed_conversation_history.get_full_history(user_id)
    print(f"\nFull history length: {len(full_history)}")
    
    # Clear history
    compressed_conversation_history.clear_history(user_id)
    print("\nHistory cleared")

if __name__ == "__main__":
    test_compressed_conversation_history()