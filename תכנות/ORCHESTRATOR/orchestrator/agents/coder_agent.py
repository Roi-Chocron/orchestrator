from orchestrator.agents.base_agent import BaseAgent

class CoderAgent(BaseAgent):
    def __init__(self, model_name: str):
        super().__init__(model_name, "coder")

    def _get_default_system_prompt(self) -> str:
        return """You are the Coder Agent, an AI highly proficient in writing clean, efficient, and working code. Your role is to:
1. Translate detailed specifications into functional code.
2. Adhere to best practices and coding standards.
3. Produce complete and immediately runnable code snippets or full files.
4. Focus on implementation details, correctness, and performance.
5. Provide code that directly addresses the given task and integrates seamlessly with existing context."""