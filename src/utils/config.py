import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self._config = self._load_config()
        self._setup_directories()
    
    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _setup_directories(self):
        """Create necessary directories if they don't exist"""
        dirs = [
            self._config['storage']['papers_dir'],
            self._config['storage']['cache_dir'],
            self._config['storage']['outputs_dir']
        ]
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str, default=None):
        """Get config value using dot notation (e.g., 'llm.development.model')"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    @property
    def environment(self) -> str:
        return os.getenv('ENVIRONMENT', 'development')
    
    @property
    def llm_config(self) -> Dict[str, Any]:
        return self.get(f'llm.{self.environment}', {})
    
    @property
    def api_keys(self) -> Dict[str, str]:
        return {
            'google': os.getenv('GOOGLE_API_KEY'),
            'openai': os.getenv('OPENAI_API_KEY'),
            'semantic_scholar': os.getenv('SEMANTIC_SCHOLAR_API_KEY')
        }

config = Config()
