from ..core.interfaces import LLMInterface
from typing import List, Dict, Any, Optional
import random

class MockLLM(LLMInterface):
    """
    A mock LLM for testing and development without API costs.
    Returns predefined or random responses.
    """
    async def generate(self, prompt: str, context: Optional[List[Dict[str, Any]]] = None, **kwargs) -> str:
        # Simple heuristic response based on keywords
        prompt_lower = prompt.lower()

        if "plan" in prompt_lower:
            return "1. Analyze requirements\n2. Design architecture\n3. Implement core\n4. Test"
        elif "code" in prompt_lower or "implement" in prompt_lower:
            return "def solution():\n    print('Hello World')\n    return True"
        elif "critic" in prompt_lower or "review" in prompt_lower:
            return "The solution is functional but lacks error handling. Grade: 8/10."
        else:
            return f"Processed request: {prompt[:50]}..."

    async def embed(self, text: str) -> List[float]:
        # Return a random vector of dimension 1536
        return [random.random() for _ in range(1536)]
