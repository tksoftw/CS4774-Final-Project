"""Google Gemini API service wrapper."""

from typing import Optional
import google.generativeai as genai
from app.config import get_settings


class GeminiService:
    """Service for interacting with Google Gemini API."""
    
    def __init__(self):
        settings = get_settings()
        genai.configure(api_key=settings.gemini_api_key)
        self.model_name = settings.gemini_model
        self.embedding_model = settings.gemini_embedding_model
        self.model = genai.GenerativeModel(self.model_name)
    
    def get_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Get a chat completion from Gemini.
        
        Args:
            prompt: The user's prompt/question
            system_prompt: Optional system instructions
            temperature: Creativity level (0-1)
            max_tokens: Maximum response length
            
        Returns:
            The assistant's response text
        """
        # Combine system prompt and user prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        
        response = self.model.generate_content(
            full_prompt,
            generation_config=generation_config,
        )
        
        return response.text
    
    def get_embedding(self, text: str, task_type: str = "retrieval_document") -> list[float]:
        """Get embedding vector for text.
        
        Args:
            text: Text to embed
            task_type: One of "retrieval_document" (for stored docs) or "retrieval_query" (for searches)
            
        Returns:
            Embedding vector as list of floats
        """
        result = genai.embed_content(
            model=self.embedding_model,
            content=text,
            task_type=task_type,
        )
        
        return result['embedding']
    
    def get_query_embedding(self, text: str) -> list[float]:
        """Get embedding vector for a search query.
        
        Args:
            text: Query text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        return self.get_embedding(text, task_type="retrieval_query")
    
    def get_embeddings_batch(self, texts: list[str], task_type: str = "retrieval_document") -> list[list[float]]:
        """Get embedding vectors for multiple texts.
        
        Args:
            texts: List of texts to embed
            task_type: One of "retrieval_document" or "retrieval_query"
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            embedding = self.get_embedding(text, task_type=task_type)
            embeddings.append(embedding)
        
        return embeddings

