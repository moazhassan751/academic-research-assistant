"""
Enhanced configuration management system for Academic Research Assistant
"""

import os
import yaml
import json
import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
import re
from ..utils.validators import ResearchQueryValidator
from ..utils.error_handler import ValidationError, ConfigurationError

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Application environments"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class LogLevel(Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class APIConfig:
    """API configuration settings"""
    base_url: str
    timeout: int = 30
    max_retries: int = 3
    rate_limit: float = 1.0  # requests per second
    api_key: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate API configuration"""
        if self.timeout <= 0:
            raise ValidationError("API timeout must be positive", field="timeout", value=self.timeout)
        if self.max_retries < 0:
            raise ValidationError("Max retries must be non-negative", field="max_retries", value=self.max_retries)
        if self.rate_limit <= 0:
            raise ValidationError("Rate limit must be positive", field="rate_limit", value=self.rate_limit)


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    path: str = "data/research.db"
    backup_enabled: bool = True
    backup_interval: int = 3600  # seconds
    max_connections: int = 10
    connection_timeout: int = 30
    optimize_on_startup: bool = True
    
    def __post_init__(self):
        """Validate database configuration"""
        if self.max_connections <= 0:
            raise ValidationError("Max connections must be positive", field="max_connections", value=self.max_connections)
        if self.connection_timeout <= 0:
            raise ValidationError("Connection timeout must be positive", field="connection_timeout", value=self.connection_timeout)
        if self.backup_interval < 0:
            raise ValidationError("Backup interval must be non-negative", field="backup_interval", value=self.backup_interval)


@dataclass
class ExportConfig:
    """Export configuration settings"""
    output_directory: str = "data/outputs"
    default_formats: List[str] = field(default_factory=lambda: ["pdf", "docx"])
    pdf_settings: Dict[str, Any] = field(default_factory=lambda: {
        "page_size": "A4",
        "margin": "1in",
        "font_size": 12
    })
    docx_settings: Dict[str, Any] = field(default_factory=lambda: {
        "font_name": "Calibri",
        "font_size": 11
    })
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    
    def __post_init__(self):
        """Validate export configuration"""
        valid_formats = {"pdf", "docx", "html", "markdown", "txt", "json", "csv", "bibtex"}
        for fmt in self.default_formats:
            if fmt not in valid_formats:
                raise ValidationError(f"Invalid export format: {fmt}", field="default_formats", value=fmt)
        
        if self.max_file_size <= 0:
            raise ValidationError("Max file size must be positive", field="max_file_size", value=self.max_file_size)


@dataclass
class LoggingConfig:
    """Logging configuration settings"""
    level: str = "INFO"
    file_enabled: bool = True
    file_path: str = "logs/research_assistant.log"
    console_enabled: bool = True
    structured_logging: bool = True
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
    def __post_init__(self):
        """Validate logging configuration"""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.level not in valid_levels:
            raise ValidationError(f"Invalid log level: {self.level}", field="level", value=self.level)
        
        if self.max_file_size <= 0:
            raise ValidationError("Max file size must be positive", field="max_file_size", value=self.max_file_size)
        if self.backup_count < 0:
            raise ValidationError("Backup count must be non-negative", field="backup_count", value=self.backup_count)


@dataclass
class ResearchConfig:
    """Research-specific configuration"""
    max_papers_per_search: int = 100
    default_search_providers: List[str] = field(default_factory=lambda: ["openalex", "crossref", "semantic_scholar"])
    concurrent_requests: int = 5
    search_timeout: int = 300  # 5 minutes
    note_confidence_threshold: float = 0.7
    theme_frequency_threshold: int = 3
    
    def __post_init__(self):
        """Validate research configuration"""
        if self.max_papers_per_search <= 0:
            raise ValidationError("Max papers per search must be positive", field="max_papers_per_search", value=self.max_papers_per_search)
        if self.concurrent_requests <= 0:
            raise ValidationError("Concurrent requests must be positive", field="concurrent_requests", value=self.concurrent_requests)
        if self.search_timeout <= 0:
            raise ValidationError("Search timeout must be positive", field="search_timeout", value=self.search_timeout)
        if not 0 <= self.note_confidence_threshold <= 1:
            raise ValidationError("Note confidence threshold must be between 0 and 1", field="note_confidence_threshold", value=self.note_confidence_threshold)


@dataclass
class SecurityConfig:
    """Security configuration settings"""
    api_key_encryption: bool = True
    ssl_verify: bool = True
    request_timeout: int = 30
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    allowed_domains: List[str] = field(default_factory=lambda: [
        "api.openalex.org",
        "api.crossref.org",
        "api.semanticscholar.org",
        "export.arxiv.org"
    ])
    
    def __post_init__(self):
        """Validate security configuration"""
        if self.request_timeout <= 0:
            raise ValidationError("Request timeout must be positive", field="request_timeout", value=self.request_timeout)
        if self.max_request_size <= 0:
            raise ValidationError("Max request size must be positive", field="max_request_size", value=self.max_request_size)


@dataclass
class ApplicationConfig:
    """Main application configuration"""
    environment: str = "development"
    debug: bool = True
    
    # Sub-configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    research: ResearchConfig = field(default_factory=ResearchConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # API configurations
    apis: Dict[str, APIConfig] = field(default_factory=lambda: {
        "openalex": APIConfig(base_url="https://api.openalex.org", rate_limit=1.0),
        "crossref": APIConfig(base_url="https://api.crossref.org", rate_limit=0.5),
        "semantic_scholar": APIConfig(base_url="https://api.semanticscholar.org", rate_limit=1.0),
        "arxiv": APIConfig(base_url="http://export.arxiv.org", rate_limit=0.5)
    })
    
    def __post_init__(self):
        """Validate application configuration"""
        valid_environments = {"development", "testing", "production"}
        if self.environment not in valid_environments:
            raise ValidationError(f"Invalid environment: {self.environment}", field="environment", value=self.environment)


class ConfigurationManager:
    """Enhanced configuration management system"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config.yaml"
        self.env_prefix = "RESEARCH_ASSISTANT_"
        self._config: Optional[ApplicationConfig] = None
        self._watchers: List[callable] = []
        
        # Load configuration
        self.load_config()
    
    def load_config(self) -> ApplicationConfig:
        """Load configuration from file and environment variables"""
        try:
            # Start with default configuration
            config_dict = self._get_default_config()
            
            # Load from file if exists
            if Path(self.config_path).exists():
                file_config = self._load_config_file()
                config_dict = self._merge_configs(config_dict, file_config)
            
            # Override with environment variables
            env_config = self._load_env_config()
            config_dict = self._merge_configs(config_dict, env_config)
            
            # Create configuration object
            self._config = self._create_config_object(config_dict)
            
            # Validate configuration
            self._validate_config()
            
            # Apply environment-specific settings
            self._apply_environment_settings()
            
            logger.info(f"Configuration loaded successfully from {self.config_path}")
            return self._config
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise ConfigurationError(f"Configuration loading failed: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration as dictionary"""
        default_config = ApplicationConfig()
        return asdict(default_config)
    
    def _load_config_file(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                    return yaml.safe_load(f) or {}
                elif self.config_path.endswith('.json'):
                    return json.load(f) or {}
                else:
                    raise ConfigurationError(f"Unsupported config file format: {self.config_path}")
        
        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {self.config_path}")
            return {}
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in config file: {e}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in config file: {e}")
    
    def _load_env_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        env_config = {}
        
        for key, value in os.environ.items():
            if key.startswith(self.env_prefix):
                # Convert environment variable name to config path
                config_path = key[len(self.env_prefix):].lower().split('_')
                
                # Convert value to appropriate type
                converted_value = self._convert_env_value(value)
                
                # Set nested configuration value
                self._set_nested_value(env_config, config_path, converted_value)
        
        return env_config
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable value to appropriate type"""
        # Boolean values
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Integer values
        if value.isdigit():
            return int(value)
        
        # Float values
        try:
            return float(value)
        except ValueError:
            pass
        
        # JSON values (for complex types)
        if value.startswith('{') or value.startswith('['):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        # Comma-separated lists
        if ',' in value:
            return [item.strip() for item in value.split(',')]
        
        return value
    
    def _set_nested_value(self, config: Dict[str, Any], path: List[str], value: Any):
        """Set nested configuration value"""
        current = config
        
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[path[-1]] = value
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _create_config_object(self, config_dict: Dict[str, Any]) -> ApplicationConfig:
        """Create ApplicationConfig object from dictionary"""
        try:
            # Create nested configuration objects
            if 'database' in config_dict:
                config_dict['database'] = DatabaseConfig(**config_dict['database'])
            
            if 'logging' in config_dict:
                config_dict['logging'] = LoggingConfig(**config_dict['logging'])
            
            if 'research' in config_dict:
                config_dict['research'] = ResearchConfig(**config_dict['research'])
            
            if 'export' in config_dict:
                config_dict['export'] = ExportConfig(**config_dict['export'])
            
            if 'security' in config_dict:
                config_dict['security'] = SecurityConfig(**config_dict['security'])
            
            # Create API configurations
            if 'apis' in config_dict:
                api_configs = {}
                for api_name, api_config in config_dict['apis'].items():
                    if isinstance(api_config, dict):
                        api_configs[api_name] = APIConfig(**api_config)
                    else:
                        api_configs[api_name] = api_config
                config_dict['apis'] = api_configs
            
            return ApplicationConfig(**config_dict)
            
        except TypeError as e:
            raise ConfigurationError(f"Invalid configuration structure: {e}")
    
    def _validate_config(self):
        """Validate the complete configuration"""
        if not self._config:
            raise ConfigurationError("Configuration not loaded")
        
        # Validate API keys for production
        if self._config.environment == "production":
            for api_name, api_config in self._config.apis.items():
                if not api_config.api_key:
                    logger.warning(f"No API key configured for {api_name} in production")
        
        # Validate paths exist or can be created
        paths_to_check = [
            Path(self._config.database.path).parent,
            Path(self._config.logging.file_path).parent,
            Path(self._config.export.output_directory)
        ]
        
        for path in paths_to_check:
            try:
                path.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                raise ConfigurationError(f"Cannot create directory: {path}")
        
        # Validate security settings for production
        if self._config.environment == "production":
            if not self._config.security.ssl_verify:
                logger.warning("SSL verification disabled in production - security risk!")
            if self._config.debug:
                logger.warning("Debug mode enabled in production - security risk!")
    
    def _apply_environment_settings(self):
        """Apply environment-specific settings"""
        if not self._config:
            return
        
        if self._config.environment == "production":
            # Production settings
            self._config.debug = False
            self._config.logging.level = "WARNING"
            self._config.security.ssl_verify = True
            
        elif self._config.environment == "testing":
            # Testing settings
            self._config.database.path = ":memory:"  # In-memory database for tests
            self._config.logging.file_enabled = False
            self._config.research.max_papers_per_search = 10  # Smaller for tests
            
        elif self._config.environment == "development":
            # Development settings
            self._config.debug = True
            self._config.logging.level = "DEBUG"
    
    def get_config(self) -> ApplicationConfig:
        """Get current configuration"""
        if not self._config:
            raise ConfigurationError("Configuration not loaded")
        return self._config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key"""
        if not self._config:
            return default
        
        try:
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                if hasattr(value, k):
                    value = getattr(value, k)
                elif isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except (AttributeError, KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot-notation key"""
        if not self._config:
            raise ConfigurationError("Configuration not loaded")
        
        keys = key.split('.')
        current = self._config
        
        # Navigate to parent of target key
        for k in keys[:-1]:
            if hasattr(current, k):
                current = getattr(current, k)
            else:
                raise ConfigurationError(f"Configuration path not found: {'.'.join(keys[:-1])}")
        
        # Set the final value
        final_key = keys[-1]
        if hasattr(current, final_key):
            setattr(current, final_key, value)
        elif isinstance(current, dict):
            current[final_key] = value
        else:
            raise ConfigurationError(f"Cannot set configuration key: {key}")
        
        # Notify watchers
        self._notify_watchers(key, value)
    
    def save_config(self, path: Optional[str] = None) -> None:
        """Save current configuration to file"""
        if not self._config:
            raise ConfigurationError("No configuration to save")
        
        save_path = path or self.config_path
        config_dict = asdict(self._config)
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                if save_path.endswith('.json'):
                    json.dump(config_dict, f, indent=2, default=str)
                else:
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
            logger.info(f"Configuration saved to {save_path}")
            
        except (IOError, yaml.YAMLError) as e:
            raise ConfigurationError(f"Failed to save configuration: {e}")
    
    def reload_config(self) -> ApplicationConfig:
        """Reload configuration from file"""
        logger.info("Reloading configuration...")
        old_config = self._config
        
        try:
            new_config = self.load_config()
            logger.info("Configuration reloaded successfully")
            return new_config
        
        except Exception as e:
            logger.error(f"Failed to reload configuration, keeping old config: {e}")
            self._config = old_config
            raise
    
    def watch_config(self, callback: callable) -> None:
        """Add callback to be called when configuration changes"""
        self._watchers.append(callback)
    
    def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify all watchers of configuration change"""
        for watcher in self._watchers:
            try:
                watcher(key, value)
            except Exception as e:
                logger.error(f"Configuration watcher failed: {e}")
    
    def validate_api_key(self, api_name: str) -> bool:
        """Validate API key for specific service"""
        if api_name not in self._config.apis:
            return False
        
        api_config = self._config.apis[api_name]
        api_key = api_config.api_key or os.getenv(f"{self.env_prefix}{api_name.upper()}_API_KEY")
        
        if not api_key:
            return False
        
        # Basic validation - check if key looks reasonable
        if len(api_key) < 10:
            return False
        
        # Service-specific validation could be added here
        return True
    
    def get_api_config(self, api_name: str) -> Optional[APIConfig]:
        """Get API configuration for specific service"""
        if not self._config or api_name not in self._config.apis:
            return None
        
        api_config = self._config.apis[api_name]
        
        # Inject API key from environment if not set
        if not api_config.api_key:
            env_key = f"{self.env_prefix}{api_name.upper()}_API_KEY"
            api_config.api_key = os.getenv(env_key)
        
        return api_config
    
    def create_default_config_file(self, path: Optional[str] = None) -> None:
        """Create a default configuration file"""
        config_path = path or self.config_path
        
        if Path(config_path).exists():
            logger.warning(f"Configuration file already exists: {config_path}")
            return
        
        default_config = ApplicationConfig()
        config_dict = asdict(default_config)
        
        # Add comments for better understanding
        config_content = f"""# Academic Research Assistant Configuration
# Environment: {default_config.environment}

environment: {default_config.environment}
debug: {default_config.debug}

database:
  path: "{default_config.database.path}"
  backup_enabled: {default_config.database.backup_enabled}
  backup_interval: {default_config.database.backup_interval}
  max_connections: {default_config.database.max_connections}
  connection_timeout: {default_config.database.connection_timeout}
  optimize_on_startup: {default_config.database.optimize_on_startup}

logging:
  level: "{default_config.logging.level}"
  file_enabled: {default_config.logging.file_enabled}
  file_path: "{default_config.logging.file_path}"
  console_enabled: {default_config.logging.console_enabled}
  structured_logging: {default_config.logging.structured_logging}
  max_file_size: {default_config.logging.max_file_size}
  backup_count: {default_config.logging.backup_count}

research:
  max_papers_per_search: {default_config.research.max_papers_per_search}
  default_search_providers:
    - "openalex"
    - "crossref"
    - "semantic_scholar"
  concurrent_requests: {default_config.research.concurrent_requests}
  search_timeout: {default_config.research.search_timeout}
  note_confidence_threshold: {default_config.research.note_confidence_threshold}
  theme_frequency_threshold: {default_config.research.theme_frequency_threshold}

export:
  output_directory: "{default_config.export.output_directory}"
  default_formats:
    - "pdf"
    - "docx"
  pdf_settings:
    page_size: "A4"
    margin: "1in"
    font_size: 12
  docx_settings:
    font_name: "Calibri"
    font_size: 11
  max_file_size: {default_config.export.max_file_size}

security:
  api_key_encryption: {default_config.security.api_key_encryption}
  ssl_verify: {default_config.security.ssl_verify}
  request_timeout: {default_config.security.request_timeout}
  max_request_size: {default_config.security.max_request_size}
  allowed_domains:
    - "api.openalex.org"
    - "api.crossref.org"
    - "api.semanticscholar.org"
    - "export.arxiv.org"

apis:
  openalex:
    base_url: "https://api.openalex.org"
    timeout: 30
    max_retries: 3
    rate_limit: 1.0
    # api_key: "your_openalex_api_key_here"
  
  crossref:
    base_url: "https://api.crossref.org"
    timeout: 30
    max_retries: 3
    rate_limit: 0.5
    # api_key: "your_crossref_api_key_here"
  
  semantic_scholar:
    base_url: "https://api.semanticscholar.org"
    timeout: 30
    max_retries: 3
    rate_limit: 1.0
    # api_key: "your_semantic_scholar_api_key_here"
  
  arxiv:
    base_url: "http://export.arxiv.org"
    timeout: 30
    max_retries: 3
    rate_limit: 0.5

# Environment variables can override any setting above
# Format: RESEARCH_ASSISTANT_<SECTION>_<KEY>=<VALUE>
# Example: RESEARCH_ASSISTANT_DATABASE_PATH=custom_path.db
#          RESEARCH_ASSISTANT_APIS_OPENALEX_API_KEY=your_key
"""
        
        try:
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            logger.info(f"Default configuration file created: {config_path}")
            
        except IOError as e:
            raise ConfigurationError(f"Failed to create config file: {e}")


# Global configuration manager instance
config_manager = ConfigurationManager()

# Convenience function for backward compatibility
def config() -> ConfigurationManager:
    """Get global configuration manager"""
    return config_manager
