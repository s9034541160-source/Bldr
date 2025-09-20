#!/usr/bin/env python3
"""
Test agents import
"""

import os
import sys

# Set environment variable for OpenAI API key (not actually needed for LM Studio)
os.environ["OPENAI_API_KEY"] = "not-needed"

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

try:
    from core.agents.coordinator_agent import CoordinatorAgent
    print('✅ CoordinatorAgent import successful')
except Exception as e:
    print(f'❌ CoordinatorAgent import failed: {e}')

try:
    from core.agents.specialist_agents import SpecialistAgentsManager
    print('✅ SpecialistAgentsManager import successful')
except Exception as e:
    print(f'❌ SpecialistAgentsManager import failed: {e}')