import os
from datetime import datetime
from typing import Dict, Any, List

class MetaAnalyst:
    def __init__(self, log_path="orchestrator/logs/task_postmortems.md"):
        self.log_path = log_path

    def analyze_and_log(self, task_id: str, task_description: str,
                        cost: float, duration: float,
                        succeeded_agents: List[str], failed_agents: List[str]):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Placeholder for actual root cause and recommendation analysis
        # In a more advanced system, an LLM would analyze agent outputs/errors
        root_cause = "Analysis pending (LLM-driven analysis not yet implemented)."
        recommendation = "Improve agent prompts based on trends (LLM-driven analysis not yet implemented)."

        log_entry = f"""
---
Task ID: {task_id}
Date: {timestamp}
Task: {task_description}
Cost: ${cost:.4f}
Duration: {duration:.2f} seconds
Succeeded Agents: {', '.join(succeeded_agents) if succeeded_agents else 'None'}
Failed Agents: {', '.join(failed_agents) if failed_agents else 'None'}
Root Cause: {root_cause}
Recommendation: {recommendation}
---
"""
        with open(self.log_path, 'a') as f:
            f.write(log_entry)
        print(f"Meta-analysis logged for Task ID: {task_id}")

    def get_agent_failure_count(self, agent_type: str, look_back_count: int = 10) -> int:
        failure_count = 0
        with open(self.log_path, 'r') as f:
            log_content = f.read()

        # Simple parsing for MVP - in production, might use regex or a proper parser
        entries = log_content.split('---')
        recent_entries = entries[-look_back_count:] # Look at the last N entries

        for entry in recent_entries:
            if f"Failed Agents: {agent_type}" in entry:
                failure_count += 1
            elif f"Failed Agents: " in entry and agent_type in entry.split("Failed Agents: ")[1].split("\n")[0]:
                 failure_count +=1
        return failure_count

    def get_recent_postmortems_for_agent(self, agent_type: str, count: int = 10) -> List[str]:
        recent_postmortems = []
        with open(self.log_path, 'r') as f:
            log_content = f.read()

        entries = log_content.split('---')
        # Reverse to get most recent first
        for entry in reversed(entries):
            if entry.strip() and f"Failed Agents: " in entry:
                failed_agents_line = entry.split("Failed Agents: ")[1].split("\n")[0]
                if agent_type in failed_agents_line:
                    recent_postmortems.append(entry.strip())
                    if len(recent_postmortems) >= count:
                        break
        return recent_postmortems
