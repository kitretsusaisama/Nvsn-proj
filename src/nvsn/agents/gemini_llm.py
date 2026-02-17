import google.generativeai as genai
from ..core.interfaces import LLMInterface
from typing import List, Dict, Any, Optional
import os
import structlog
import asyncio

logger = structlog.get_logger()

class GeminiLLM(LLMInterface):
    """
    LLM provider using Google's Gemini API.
    """
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-pro"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API Key not found. Please set GOOGLE_API_KEY environment variable.")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
        self.logger = logger.bind(provider="Gemini", model=model_name)

    async def generate(self, prompt: str, context: Optional[List[Dict[str, Any]]] = None, **kwargs) -> str:
        self.logger.info("Generating content", prompt_preview=prompt[:50])

        try:
            # Run blocking call in executor
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=kwargs.get("temperature", 0.7)
                )
            )
            return response.text
        except Exception as e:
            self.logger.error("Generation failed", error=str(e))
            return f"Error generating content: {str(e)}"

    async def embed(self, text: str) -> List[float]:
        try:
            # Model name for embedding. 'models/embedding-001' is common for free tier
            embedding_model = "models/embedding-001"

            result = await asyncio.to_thread(
                genai.embed_content,
                model=embedding_model,
                content=text,
                task_type="retrieval_document"
            )

            # The API returns dict with 'embedding' key
            return result['embedding']
        except Exception as e:
            self.logger.error("Embedding failed", error=str(e))
            # Fallback or re-raise. For stability, returning zero vector might be safer for MVP but misleading.
            # Let's raise to be explicit about failure.
            raise e
