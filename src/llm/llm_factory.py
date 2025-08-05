from typing import Union
from .gemini_client import GeminiClient
from .openai_client import OpenAIClient
from ..utils.config import config

class LLMFactory:
    @staticmethod
    def create_llm() -> Union[GeminiClient, OpenAIClient]:
        """Create LLM client based on configuration"""
        llm_config = config.llm_config
        provider = llm_config.get('provider', 'gemini')
        
        if provider == 'gemini':
            return GeminiClient(
                api_key=config.api_keys['google'],
                model=llm_config.get('model', 'gemini-2.5-flash'),
                temperature=llm_config.get('temperature', 0.1),
                max_tokens=llm_config.get('max_tokens', 4096)
            )
        elif provider == 'openai':
            return OpenAIClient(
                api_key=config.api_keys['openai'],
                model=llm_config.get('model', 'gpt-4-turbo'),
                temperature=llm_config.get('temperature', 0.1),
                max_tokens=llm_config.get('max_tokens', 4096)
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")