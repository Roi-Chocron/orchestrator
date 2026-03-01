import asyncio
import os
import yaml
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from typing import List, Dict, Any, Optional

from orchestrator.core.decomposer import Decomposer
from orchestrator.core.router import Router
from orchestrator.core.merger import Merger
from orchestrator.agents.base_agent import AgentResult

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class Orchestrator:
    def __init__(self, config_path="orchestrator/config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.decomposer = Decomposer(self.config)
        self.router = Router(self.config)
        self.merger = Merger(self.config)
        self.log_path = "orchestrator/logs/task_postmortems.md"

    async def _run_subtask(self, subtask: Dict[str, Any], context: str) -> AgentResult:
        agent_type = subtask["agent_type"]
        agent_instance = self.router.get_agent(agent_type)
        print(f"Running subtask with {agent_type} agent: {subtask['description']}")
        result = await agent_instance.run(
            task=subtask["description"],
            context=context,
            input_data=subtask.get("input", "")
        )
        return result

    async def run_task(self, task_description: str) -> Dict[str, Any]:
        print(f"Orchestrator received task: {task_description}")

        # Classify complexity (simplified for MVP)
        # In a real system, this would be an LLM call
        complexity = "complex" if len(task_description.split()) > 10 else "trivial"

        if complexity == "trivial":
            print("Task classified as trivial, running directly with PlannerAgent.")
            planner_agent = self.router.get_agent("planner") # Use planner for trivial
            trivial_result = await planner_agent.run(task=task_description, context="", input_data="")
            self._log_task_postmortem(
                task_description=task_description,
                cost=trivial_result.cost,
                duration=trivial_result.duration,
                succeeded_agents=["planner"],
                failed_agents=[],
                root_cause="",
                recommendation=""
            )
            return {
                "final_output": trivial_result.output,
                "total_cost": trivial_result.cost,
                "total_duration": trivial_result.duration,
                "logs": "Trivial task completed."
            }

        print("Task classified as complex, decomposing...")
        batches = await self.decomposer.decompose(task_description)
        if not batches:
            return {"error": "Decomposition failed or returned empty batches."}

        total_cost = 0.0
        total_duration = 0.0
        overall_context = ""
        succeeded_agents = []
        failed_agents = []

        for i, batch in enumerate(batches):
            print(f"Running Batch {i+1}/{len(batches)}")
            batch_results = await asyncio.gather(*[
                self._run_subtask(subtask, overall_context) for subtask in batch
            ])

            batch_outputs = []
            for result in batch_results:
                total_cost += result.cost
                total_duration += result.duration
                if result.success:
                    batch_outputs.append(result.output)
                    succeeded_agents.append(result.agent_type)
                else:
                    failed_agents.append(result.agent_type)
                    print(f"Agent {result.agent_type} failed: {result.error}")

            # Merge batch results into overall context for the next batch
            if batch_outputs:
                batch_context = "\n".join(batch_outputs)
                merger_result = await self.merger.merge_batch_results(batch_context, overall_context)
                overall_context = merger_result.output
                total_cost += merger_result.cost
                total_duration += merger_result.duration
                if not merger_result.success:
                    failed_agents.append("merger")
                    print(f"Merger failed for batch {i+1}: {merger_result.error}")

        final_result = await self.merger.merge_final_results(task_description, overall_context)
        total_cost += final_result.cost
        total_duration += final_result.duration
        if not final_result.success:
            failed_agents.append("merger")
            print(f"Final merger failed: {final_result.error}")

        self._log_task_postmortem(
            task_description=task_description,
            cost=total_cost,
            duration=total_duration,
            succeeded_agents=list(set(succeeded_agents)), # Unique agents
            failed_agents=list(set(failed_agents)),       # Unique agents
            root_cause="N/A", # To be improved by meta_analyst
            recommendation="N/A" # To be improved by meta_analyst
        )

        return {
            "final_output": final_result.output,
            "total_cost": total_cost,
            "total_duration": total_duration,
            "logs": "Task completed through orchestration."
        }

    def _log_task_postmortem(self, task_description: str, cost: float, duration: float,
                             succeeded_agents: List[str], failed_agents: List[str],
                             root_cause: str, recommendation: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"""
---
Task ID: {datetime.now().timestamp()}
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
        print(f"Task postmortem logged to {self.log_path}")