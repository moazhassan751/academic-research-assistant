import openai
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from ..utils.logging import logger

class OpenAIClient:
    def __init__(self, api_key: str, model: str = "gpt-4-turbo",
                 temperature: float = 0.1, max_tokens: int = 4096):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        logger.info(f"Initialized OpenAI client with model: {model}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using OpenAI API"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count (approximate)"""
        return len(text.split()) * 1.3  # Rough estimation