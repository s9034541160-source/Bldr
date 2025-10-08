# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: process_query
# Основной источник: C:\Bldr\core\agents\coordinator_agent.py
# Дубликаты (для справки):
#   - C:\Bldr\backend\api\tools_api.py
#================================================================================
    def process_query(self, query: str) -> str:
        """
        Main entry: Plan → Response.
        """
        try:
            # Add to history
            if self.request_context and "user_id" in self.request_context and conversation_history:
                user_id = self.request_context["user_id"]
                conversation_history.add_message(user_id, {"role": "user", "content": query})
            
            # Generate plan
            plan = self.generate_plan(query)
            
            # Early direct/voice
            tasks = plan.get("tasks", [])
            if len(tasks) == 1:
                task = tasks[0]
                if task.get("tool") == "direct_response":
                    response = self._direct_response(query)
                    # Add to history
                    if self.request_context and "user_id" in self.request_context and conversation_history:
                        conversation_history.add_message(user_id, {"role": "assistant", "content": response})
                    return response
                
                if task.get("tool") == "transcribe_audio":
                    params = task.get("input", {}) or {"audio_path": self.request_context.get("audio_path", "")}
                    response = self._transcribe_audio(json.dumps(params))
                    # Add to history
                    if self.request_context and "user_id" in self.request_context and conversation_history:
                        conversation_history.add_message(user_id, {"role": "assistant", "content": response})
                    return response
            
            # Complex: Convert to natural
            response = self._convert_plan_to_natural_language(plan, query)
            
            # Add to history
            if self.request_context and "user_id" in self.request_context and conversation_history:
                conversation_history.add_message(user_id, {"role": "assistant", "content": response})
            
            return response
            
        except Exception as e:
            print(f"process_query error: {e}")
            # Fallback direct if greeting
            query_lower = query.lower()
            greeting_keywords = ["привет", "здравствуй", "hello", "hi", "hey"]
            self_intro_keywords = ["расскажи о себе", "что ты умеешь", "кто ты"]
            if any(kw in query_lower for kw in greeting_keywords + self_intro_keywords):
                return self._direct_response(query)
            return f"Ошибка обработки: {str(e)[:100]}. Перефразируйте запрос."