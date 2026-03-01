import os
import yaml
import json
import asyncio
import google.generativeai as genai
from typing import List, Dict, Any

class Decomposer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config["model"]
        self.client = genai.GenerativeModel(self.model_name)

    async def decompose(self, task: str) -> List[List[Dict[str, Any]]]:
        prompt = (
            f"Decompose this task into parallel batches. Each batch contains subtasks with no dependencies on each other. "
            f"Batch N+1 may depend on batch N. For each subtask specify: agent_type, description, input, expected_output, complexity. "
            f"Return JSON only. The 'agent_type' must be one of: planner, coder, researcher, qa, communicator.\n\n"
            f"Task: {task}\n\n"
            f"JSON format example:\n"
            f"[\n"
            f"  [\n"
            f"    {{\"agent_type\": \"researcher\", \"description\": \"Subtask 1.1 description\", \"input\": \"input for 1.1\", \"expected_output\": \"output for 1.1\", \"complexity\": \"low\"}},\n"
            f"    {{\"agent_type\": \"coder\", \"description\": \"Subtask 1.2 description\", \"input\": \"input for 1.2\", \"expected_output\": \"output for 1.2\", \"complexity\": \"medium\"}}\n"
            f"  ],\n"
            f"  [\n"
            f"    {{\"agent_type\": \"qa\", \"description\": \"Subtask 2.1 description\", \"input\": \"input for 2.1\", \"expected_output\": \"output for 2.1\", \"complexity\": \"high\"}}\n"
            f"  ]\n"
            f"]"
        )
        print("Calling Gemini for decomposition...")
        try:
            response = await asyncio.to_thread(self.client.generate_content, prompt)
            json_output = response.text.strip()
            # Attempt to clean up common LLM errors like markdown code blocks
            if json_output.startswith("```json"):
                json_output = json_output[len("```json"):].strip()
            if json_output.endswith("```"):
                json_output = json_output[:-len("```")].strip()

            batches = json.loads(json_output)
            print("Decomposition successful.")
            return batches
        except Exception as e:
            print(f"Decomposition failed: {e}")
            print(f"LLM Response: {response.text}") # For debugging
            return []
