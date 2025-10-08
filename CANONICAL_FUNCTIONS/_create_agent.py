# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _create_agent
# Основной источник: C:\Bldr\core\agents\coordinator_agent.py
# Дубликаты (для справки):
#   - C:\Bldr\core\agents\roles_agents.py
#================================================================================
    def _create_agent(self) -> AgentExecutor:
        """Create ReAct agent."""
        prompt_template = """{system_prompt}

Tools: {tools}
Tool Names: {tool_names}

Format (ReAct exactly):
Question: {input}
Thought: ...
Action: [tool_name]
Action Input: ...
Observation: ...
... (repeat)
Thought: Final answer
Final Answer: ...

Begin! Thought: {agent_scratchpad}"""

        tools_str = "\n".join([f"{t.name}: {t.description}" for t in self.tools])
        tool_names_str = ", ".join([t.name for t in self.tools])
        prompt = PromptTemplate.from_template(prompt_template).partial(
            system_prompt=self.system_prompt,
            tools=tools_str,
            tool_names=tool_names_str
        )

        agent = create_react_agent(self.llm, self.tools, prompt)

        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=False,  # Speed
            handle_parsing_errors=True,
            max_iterations=4,
            max_execution_time=3600.0
        )