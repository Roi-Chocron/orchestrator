import asyncio
import time
import os
import google.generativeai as genai
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class AgentResult:
    output: str
    tokens_used: int
    cost: float
    duration: float
    success: bool
    error: Optional[str] = None
    agent_type: Optional[str] = None

class BaseAgent:
    def __init__(self, model_name: str, agent_type: str):
        self.model_name = model_name
        self.agent_type = agent_type
        self.client = genai.GenerativeModel(model_name)
        self.max_retries = 3
        self.timeout = 30 # seconds

    def _get_system_prompt(self) -> str:
        prompt_file = f"orchestrator/prompts/{self.agent_type}_current.md"
        if os.path.exists(prompt_file):
            with open(prompt_file, 'r') as f:
                return f.read()
        else:
            return self._get_default_system_prompt()

    def _get_default_system_prompt(self) -> str:
        # This will be overridden by child classes
        return "You are a helpful AI assistant."

    async def run(self, task: str, context: str, input_data: Any) -> AgentResult:
        system_prompt = self._get_system_prompt()
        full_prompt = f"{system_prompt}\n\nTask: {task}\nContext: {context}\nInput: {input_data}"

        output = ""
        tokens_used = 0
        cost = 0.0
        success = False
        error = None
        duration = 0.0

        for i in range(self.max_retries):
            start_time = asyncio.get_event_loop().time()
            try:
                # Using asyncio.to_thread for blocking API call
                response = await asyncio.wait_for(
                    asyncio.to_thread(self.client.generate_content, full_prompt),
                    timeout=self.timeout
                )
                output = response.text
                # Placeholder for actual token and cost calculation
                # In a real scenario, you'd get this from the API response
                tokens_used = len(full_prompt.split()) + len(output.split())
                cost = tokens_used * 0.000001 # Example cost per token
                success = True
                duration = asyncio.get_event_loop().time() - start_time
                break # Success, break out of retry loop
            except asyncio.TimeoutError:
                error = f"Agent {self.agent_type} timed out after {self.timeout} seconds."
                print(error)
            except Exception as e:
                error = str(e)
                print(f"Agent {self.agent_type} call failed: {error}")

            duration = asyncio.get_event_loop().time() - start_time
            if i < self.max_retries - 1:
                wait_time = 2 ** i # Exponential backoff
                print(f"Retrying {self.agent_type} agent in {wait_time} seconds...")
                await asyncio.sleep(wait_time)

        return AgentResult(
            output=output,
            tokens_used=tokens_used,
            cost=cost,
            duration=duration,
            success=success,
            error=error,
            agent_type=self.agent_type
        )
