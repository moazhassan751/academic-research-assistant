import google.generativeai as genai
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from ..utils.logging import logger

class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash", 
                 temperature: float = 0.1, max_tokens: int = 4096):
        self.api_key = api_key
        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        
        logger.info(f"Initialized Gemini client with model: {model}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using Gemini API"""
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"SYSTEM: {system_prompt}\n\nUSER: {prompt}"
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens
                )
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return self.model.count_tokens(text).total_tokens