import os
import yaml
import asyncio
import google.generativeai as genai
from typing import Dict, Any

from orchestrator.agents.base_agent import AgentResult

class Merger:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config["model"]
        self.client = genai.GenerativeModel(self.model_name)

    async def merge_batch_results(self, batch_context: str, overall_context: str) -> AgentResult:
        prompt = (
            f"You are a sophisticated AI designed to merge information. "
            f"Combine the following new batch results with the existing overall context. "
            f"Focus on integrating new insights, resolving contradictions, and maintaining coherence. "
            f"Prioritize clarity and conciseness.\n\n"
            f"Existing Overall Context:\n{overall_context}\n\n"
            f"New Batch Results:\n{batch_context}\n\n"
            f"Merged Context:"
        )
        return await self._call_llm(prompt, "merger_batch_merge")

    async def merge_final_results(self, initial_task: str, overall_context: str) -> AgentResult:
        prompt = (
            f"You are a sophisticated AI designed to synthesize final answers. "
            f"Given the initial task and all accumulated information, generate a comprehensive, clear, and concise final response. "
            f"Ensure all aspects of the original task are addressed.\n\n"
            f"Initial Task: {initial_task}\n\n"
            f"Accumulated Information:\n{overall_context}\n\n"
            f"Final Answer:"
        )
        return await self._call_llm(prompt, "merger_final_merge")

    async def _call_llm(self, prompt: str, agent_type: str) -> AgentResult:
        start_time = asyncio.get_event_loop().time()
        output = ""
        tokens_used = 0
        cost = 0.0
        success = False
        error = None

        try:
            response = await asyncio.to_thread(self.client.generate_content, prompt)
            output = response.text
            # Placeholder for actual token and cost calculation
            # In a real scenario, you'd get this from the API response
            tokens_used = len(prompt.split()) + len(output.split())
            cost = tokens_used * 0.000001 # Example cost per token
            success = True
        except Exception as e:
            error = str(e)
            print(f"Merger LLM call failed: {error}")

        duration = asyncio.get_event_loop().time() - start_time
        return AgentResult(
            output=output,
            tokens_used=tokens_used,
            cost=cost,
            duration=duration,
            success=success,
            error=error,
            agent_type=agent_type
        )
