import os
import yaml
from typing import Dict, Any

from orchestrator.agents.base_agent import BaseAgent
from orchestrator.agents.planner_agent import PlannerAgent
from orchestrator.agents.coder_agent import CoderAgent
from orchestrator.agents.researcher_agent import ResearcherAgent
from orchestrator.agents.qa_agent import QAAgent
from orchestrator.agents.communicator_agent import CommunicatorAgent

class Router:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config["model"]
        self.agents = {
            "planner": PlannerAgent(self.model_name),
            "coder": CoderAgent(self.model_name),
            "researcher": ResearcherAgent(self.model_name),
            "qa": QAAgent(self.model_name),
            "communicator": CommunicatorAgent(self.model_name),
        }

    def get_agent(self, agent_type: str) -> BaseAgent:
        agent = self.agents.get(agent_type)
        if not agent:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return agent
