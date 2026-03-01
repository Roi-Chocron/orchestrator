import os
import asyncio
import google.generativeai as genai
from typing import Dict, Any, List

class PromptOptimizer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config["model"]
        self.client = genai.GenerativeModel(self.model_name)
        self.prompts_path = "orchestrator/prompts"
        self.guides_path = "orchestrator/guides"

    async def optimize_prompt(self, agent_type: str, postmortems: List[str]):
        current_prompt_path = os.path.join(self.prompts_path, f"{agent_type}_current.md")
        guide_path = os.path.join(self.guides_path, f"{agent_type}_guide.md")

        current_prompt_content = ""
        if os.path.exists(current_prompt_path):
            with open(current_prompt_path, 'r') as f:
                current_prompt_content = f.read()

        guide_content = ""
        if os.path.exists(guide_path):
            with open(guide_path, 'r') as f:
                guide_content = f.read()

        postmortems_text = "\n\n".join(postmortems)

        prompt = (
            f"You are the Prompt Optimizer, an AI expert at crafting and refining system prompts for other AI agents. "
            f"Your goal is to improve the '{agent_type}' agent's performance based on its current prompt, improvement guide, and recent failures.\n\n"
            f"Here is the CURRENT SYSTEM PROMPT for the {agent_type} agent:\n```\n{current_prompt_content}\n```\n\n"
            f"Here is the IMPROVEMENT GUIDE for the {agent_type} agent:\n```\n{guide_content}\n```\n\n"
            f"Here are RECENT TASK POSTMORTEMS for the {agent_type} agent:\n```\n{postmortems_text}\n```\n\n"
            f"Considering all the above, rewrite the system prompt for the '{agent_type}' agent to make it more effective. "
            f"The new prompt should be concise, clear, and directly address the identified areas for improvement. "
            f"Return ONLY the new system prompt content, without any additional conversational text or markdown code block delimiters."
        )

        print(f"Calling Gemini to optimize prompt for {agent_type}...")
        try:
            response = await asyncio.to_thread(self.client.generate_content, prompt)
            new_prompt_content = response.text.strip()

            # Versioning for prompts
            version = 1
            while os.path.exists(os.path.join(self.prompts_path, f"{agent_type}_v{version}.md")):
                version += 1
            new_version_path = os.path.join(self.prompts_path, f"{agent_type}_v{version}.md")

            with open(new_version_path, 'w') as f:
                f.write(new_prompt_content)
            print(f"New prompt for {agent_type} saved to {new_version_path}")

            # Set as current
            with open(current_prompt_path, 'w') as f:
                f.write(new_prompt_content)
            print(f"New prompt for {agent_type} set as current.")

        except Exception as e:
            print(f"Failed to optimize prompt for {agent_type}: {e}")
