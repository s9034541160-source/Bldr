# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: query
# Основной источник: C:\Bldr\core\model_manager.py
# Дубликаты (для справки):
#   - C:\Bldr\enterprise_rag_trainer_full.py
#   - C:\Bldr\scripts\bldr_rag_trainer.py
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def query(self, role: str, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Query model with role-specific configuration.
        
        Args:
            role: Role name
            messages: List of message dictionaries
            **kwargs: Additional arguments for the model
            
        Returns:
            Model response as string
        """
        client = self.get_model_client(role)
        if not client:
            return f"Error: Model client for role {role} not available"
        
        try:
            # Add system prompt with capabilities
            system_prompt = get_capabilities_prompt(role)
            if system_prompt:
                messages = [{"role": "system", "content": system_prompt}] + messages
            
            response = client.invoke(messages, **kwargs)
            if hasattr(response, 'content'):
                return str(response.content)
            else:
                return str(response)
        except Exception as e:
            logging.error(f"Error querying model for role {role}: {e}")
            return f"Error querying model: {str(e)}"