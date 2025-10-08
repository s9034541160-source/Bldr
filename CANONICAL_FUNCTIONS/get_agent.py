# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: get_agent
# Основной источник: C:\Bldr\core\agents\roles_agents.py
# Дубликаты (для справки):
#   - C:\Bldr\core\agents\specialist_agents.py
#================================================================================
    def get_agent(self, role: str) -> RoleAgent:
        """
        Get or create role agent for role.
        
        Args:
            role: Role name
            
        Returns:
            Role agent instance
        """
        if role not in self.agents:
            self.agents[role] = RoleAgent(role, self.lm_studio_url, self.tools_system)
        return self.agents[role]