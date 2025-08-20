import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self._config = self._load_config()
        self._setup_directories()
        self._validate_configuration()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file with fallback defaults"""
        default_config = {
            'storage': {
                'database_path': 'data/research.db',
                'papers_dir': 'data/papers',
                'cache_dir': 'data/cache',
                'outputs_dir': 'data/outputs'
            },
            'llm': {
                'development': {
                    'provider': 'gemini',
                    'model': 'gemini-2.5-flash',
                    'temperature': 0.1,
                    'max_tokens': 4096
                },
                'production': {
                    'provider': 'gemini',
                    'model': 'gemini-2.5-flash',
                    'temperature': 0.1,
                    'max_tokens': 4096
                }
            },
            'apis': {
                'openalex': {
                    'base_url': 'https://api.openalex.org/works',
                    'rate_limit': 10,
                    'timeout': 30,
                    'user_agent': 'AcademicResearchAssistant/1.0 (mailto:rmoazhassan555@gmail.com)'
                },
                'crossref': {
                    'base_url': 'https://api.crossref.org/works',
                    'rate_limit': 1,
                    'timeout': 30,
                    'mailto': 'rmoazhassan555@gmail.com'
                },
                'arxiv': {
                    'base_url': 'http://export.arxiv.org/api/query',
                    'rate_limit': 3,
                    'timeout': 30,
                    'max_results': 100,
                    'delay': 3
                }
            },
            'research': {
                'max_papers_default': 50,
                'max_retries': 3,
                'min_confidence_threshold': 0.5,
                'deduplication': {
                    'doi_priority': True,
                    'title_similarity_threshold': 0.85,
                    'author_match_threshold': 0.7
                }
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/research_assistant.log',
                'max_file_size': '10MB',
                'backup_count': 5
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f) or {}
                    # Merge with defaults
                    return self._merge_configs(default_config, loaded_config)
            except Exception as e:
                print(f"Warning: Error loading config file {self.config_path}: {e}")
                print("Using default configuration")
        else:
            print(f"Config file {self.config_path} not found, using defaults")
        
        return default_config
    
    def _merge_configs(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge loaded config with defaults"""
        merged = default.copy()
        
        for key, value in loaded.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def _setup_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [
            self.get('storage.papers_dir', 'data/papers'),
            self.get('storage.cache_dir', 'data/cache'),
            self.get('storage.outputs_dir', 'data/outputs'),
            Path(self.get('logging.file', 'logs/research_assistant.log')).parent,
            Path(self.get('storage.database_path', 'data/research.db')).parent
        ]
        
        for dir_path in directories:
            try:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"Warning: Could not create directory {dir_path}: {e}")
    
    def _validate_configuration(self):
        """Validate critical configuration settings"""
        errors = []
        warnings = []
        
        # Check API keys
        api_keys = self.api_keys
        if not api_keys.get('google'):
            errors.append("GOOGLE_API_KEY is not set in environment variables")
        
        # Check user agent and mailto configuration
        openalex_user_agent = self.get('apis.openalex.user_agent')
        crossref_mailto = self.get('apis.crossref.mailto')
        
        if (not openalex_user_agent or 
            'your-email@example.com' in openalex_user_agent or 
            'mailto:' not in openalex_user_agent):
            warnings.append("Please set a valid email in apis.openalex.user_agent for better OpenAlex rate limits")
        
        if crossref_mailto == 'your-email@example.com' or not crossref_mailto:
            warnings.append("Please set a valid email in apis.crossref.mailto for better CrossRef rate limits")
        
        # Check environment
        env = self.environment
        if env not in ['development', 'production', 'testing']:
            warnings.append(f"Unknown environment '{env}', using development settings")
        
        # Check LLM configuration
        llm_config = self.llm_config
        if not llm_config:
            errors.append(f"LLM configuration not found for environment '{env}'")
        
        # Print warnings and errors
        if warnings:
            print("Configuration Warnings:")
            for warning in warnings:
                print(f"  - {warning}")
        
        if errors:
            print("Configuration Errors:")
            for error in errors:
                print(f"  - {error}")
            raise ValueError("Critical configuration errors found")
    
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
        """Get current environment from env variable or default to development"""
        return os.getenv('ENVIRONMENT', 'development').lower()
    
    @property
    def llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration for current environment"""
        config = self.get(f'llm.{self.environment}')
        if not config:
            # Fallback to development config
            config = self.get('llm.development', {})
        return config
    
    @property
    def api_keys(self) -> Dict[str, Optional[str]]:
        """Get API keys from environment variables"""
        return {
            'google': os.getenv('GOOGLE_API_KEY'),
            'openai': os.getenv('OPENAI_API_KEY')
        }
    
    @property
    def database_path(self) -> str:
        """Get database path with environment variable override"""
        return os.getenv('DATABASE_PATH', self.get('storage.database_path', 'data/research.db'))
    
    @property
    def log_level(self) -> str:
        """Get log level with environment variable override"""
        return os.getenv('LOG_LEVEL', self.get('logging.level', 'INFO')).upper()
    
    @property
    def max_papers_default(self) -> int:
        """Get default maximum papers setting"""
        try:
            return int(os.getenv('MAX_PAPERS_DEFAULT', self.get('research.max_papers_default', 50)))
        except (ValueError, TypeError):
            return 50
    
    @property
    def request_timeout(self) -> int:
        """Get request timeout setting"""
        try:
            return int(os.getenv('REQUEST_TIMEOUT', self.get('apis.openalex.timeout', 30)))
        except (ValueError, TypeError):
            return 30
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment == 'development'
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment == 'production'
    
    def validate_api_keys(self) -> bool:
        """Validate that required API keys are present"""
        api_keys = self.api_keys
        
        # Google API key is required
        if not api_keys.get('google'):
            return False
        
        return True
    
    def get_rate_limits(self) -> Dict[str, int]:
        """Get rate limits from environment or config"""
        return {
            'gemini': int(os.getenv('GEMINI_REQUESTS_PER_MINUTE', 
                                   self.get('apis.gemini.rate_limit', 10))),
            'openalex': int(os.getenv('OPENALEX_REQUESTS_PER_SECOND',
                                    self.get('apis.openalex.rate_limit', 10))),
            'crossref': int(os.getenv('CROSSREF_REQUESTS_PER_SECOND',
                                    self.get('apis.crossref.rate_limit', 1))),
            'arxiv': int(os.getenv('ARXIV_DELAY_SECONDS',
                               self.get('apis.arxiv.delay', 3)))
        }
    
    def get_api_config(self, api_name: str) -> Dict[str, Any]:
        """Get complete configuration for a specific API"""
        return self.get(f'apis.{api_name}', {})
    
    def get_openalex_config(self) -> Dict[str, Any]:
        """Get OpenAlex API configuration"""
        return self.get_api_config('openalex')
    
    def get_crossref_config(self) -> Dict[str, Any]:
        """Get CrossRef API configuration"""
        return self.get_api_config('crossref')
    
    def get_arxiv_config(self) -> Dict[str, Any]:
        """Get ArXiv API configuration"""
        return self.get_api_config('arxiv')
    
    def get_deduplication_config(self) -> Dict[str, Any]:
        """Get deduplication configuration"""
        return self.get('research.deduplication', {
            'doi_priority': True,
            'title_similarity_threshold': 0.85,
            'author_match_threshold': 0.7
        })
    
    def get_export_config(self) -> Dict[str, Any]:
        """Get export configuration"""
        return self.get('export', {
            'output_directory': 'data/outputs',
            'default_formats': ['pdf', 'docx'],
            'pdf_settings': {
                'page_size': 'A4',
                'margin': '1in',
                'font_size': 12
            },
            'docx_settings': {
                'font_name': 'Calibri',
                'font_size': 11
            },
            'max_file_size': 104857600
        })
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return self.get('security', {
            'api_key_encryption': True,
            'ssl_verify': True,
            'request_timeout': 30,
            'max_request_size': 10485760,
            'allowed_domains': [
                'api.openalex.org',
                'api.crossref.org',
                'api.semanticscholar.org',
                'export.arxiv.org',
                'generativelanguage.googleapis.com'
            ]
        })
    
    def get_research_config(self) -> Dict[str, Any]:
        """Get complete research configuration"""
        return self.get('research', {
            'max_papers_default': 50,
            'max_retries': 3,
            'min_confidence_threshold': 0.5,
            'deduplication': {
                'doi_priority': True,
                'title_similarity_threshold': 0.85,
                'author_match_threshold': 0.7
            }
        })
    
    def save_config(self, config_path: Optional[str] = None) -> bool:
        """Save current configuration to YAML file"""
        try:
            save_path = Path(config_path) if config_path else self.config_path
            
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(self._config, f, default_flow_style=False, indent=2)
            
            print(f"Configuration saved to {save_path}")
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False

# Global config instance
config = Config()