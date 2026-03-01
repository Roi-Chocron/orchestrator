import os
import asyncio
import google.generativeai as genai
from typing import Dict, Any, List

class GuideWriter:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config["model"]
        self.client = genai.GenerativeModel(self.model_name)
        self.guides_path = "orchestrator/guides"

    async def write_guide(self, agent_type: str, postmortems: List[str]):
        postmortems_text = "\n\n".join(postmortems)
        prompt = (
            f"You are an AI specialized in writing improvement guides for other AI agents. "
            f"Based on the following task postmortems for the '{agent_type}' agent, "
            f"write a concise improvement guide (max 300 words). "
            f"Focus on identifying recurring issues, best practices, and specific recommendations to improve the agent's performance and reduce failures.\n\n"
            f"Agent Type: {agent_type}\n\n"
            f"Recent Task Postmortems:\n{postmortems_text}\n\n"
            f"Improvement Guide for {agent_type} Agent:"
        )

        print(f"Calling Gemini to write improvement guide for {agent_type}...")
        try:
            response = await asyncio.to_thread(self.client.generate_content, prompt)
            guide_content = response.text.strip()
            guide_file_path = os.path.join(self.guides_path, f"{agent_type}_guide.md")
            with open(guide_file_path, 'w') as f:
                f.write(guide_content)
            print(f"Improvement guide for {agent_type} written to {guide_file_path}")
        except Exception as e:
            print(f"Failed to write improvement guide for {agent_type}: {e}")
