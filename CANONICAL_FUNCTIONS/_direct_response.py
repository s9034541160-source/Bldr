# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _direct_response
# Основной источник: C:\Bldr\core\agents\coordinator_agent.py
# Дубликаты (для справки):
#   - C:\Bldr\core\agents\roles_agents.py
#================================================================================
    def _direct_response(self, query: str) -> str:
        """
        Generate direct response for greeting and self-introduction queries.
        
        Args:
            query: User query
            
        Returns:
            Direct response string
        """
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in ["привет", "здравствуй", "hello", "hi", "hey"]):
            return "Привет! Я ваш ассистент в строительной сфере. Рад помочь с вашими вопросами по строительству, сметам, проектам и нормативной документации."
        elif any(keyword in query_lower for keyword in ["расскажи о себе", "что ты умеешь", "кто ты", "what do you know", "what can you do", "tell me about yourself"]):
            return "Я - многофункциональный строительный ассистент, созданный для помощи в различных аспектах строительства. Я могу помочь с:\n\n1. Поиском и анализом строительных норм и правил (СП, ГОСТ, СНиП)\n2. Расчетом смет и бюджетов\n3. Созданием проектной документации\n4. Анализом изображений строительных объектов\n5. Генерацией официальных писем и документов\n6. Планированием строительных работ\n\nМоя цель - сделать вашу работу в строительной сфере более эффективной и точной."
        else:
            return f"Я получил ваш запрос: '{query}'. Я готов помочь с этим вопросом."