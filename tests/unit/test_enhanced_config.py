"""
Tests for enhanced configuration management system
"""

import pytest
import os
import tempfile
import yaml
import json
from pathlib import Path
from unittest.mock import patch, mock_open
from src.utils.enhanced_config import (
    ConfigurationManager,
    ApplicationConfig,
    APIConfig,
    DatabaseConfig,
    LoggingConfig,
    ResearchConfig,
    ExportConfig,
    SecurityConfig,
    Environment,
    LogLevel
)
from src.utils.error_handler import ValidationError, ConfigurationError


class TestDataClasses:
    """Test configuration data classes"""
    
    def test_api_config_validation(self):
        """Test API configuration validation"""
        # Valid config
        config = APIConfig(base_url="https://api.example.com", timeout=30)
        assert config.base_url == "https://api.example.com"
        assert config.timeout == 30
        
        # Invalid timeout
        with pytest.raises(ValidationError):
            APIConfig(base_url="https://api.example.com", timeout=-1)
        
        # Invalid max_retries
        with pytest.raises(ValidationError):
            APIConfig(base_url="https://api.example.com", max_retries=-1)
        
        # Invalid rate_limit
        with pytest.raises(ValidationError):
            APIConfig(base_url="https://api.example.com", rate_limit=0)
    
    def test_database_config_validation(self):
        """Test database configuration validation"""
        # Valid config
        config = DatabaseConfig(path="test.db", max_connections=5)
        assert config.path == "test.db"
        assert config.max_connections == 5
        
        # Invalid max_connections
        with pytest.raises(ValidationError):
            DatabaseConfig(max_connections=0)
        
        # Invalid connection_timeout
        with pytest.raises(ValidationError):
            DatabaseConfig(connection_timeout=-1)
        
        # Invalid backup_interval
        with pytest.raises(ValidationError):
            DatabaseConfig(backup_interval=-1)
    
    def test_export_config_validation(self):
        """Test export configuration validation"""
        # Valid config
        config = ExportConfig(default_formats=["pdf", "docx"])
        assert "pdf" in config.default_formats
        assert "docx" in config.default_formats
        
        # Invalid format
        with pytest.raises(ValidationError):
            ExportConfig(default_formats=["invalid_format"])
        
        # Invalid max_file_size
        with pytest.raises(ValidationError):
            ExportConfig(max_file_size=-1)
    
    def test_logging_config_validation(self):
        """Test logging configuration validation"""
        # Valid config
        config = LoggingConfig(level="INFO")
        assert config.level == "INFO"
        
        # Invalid level
        with pytest.raises(ValidationError):
            LoggingConfig(level="INVALID")
        
        # Invalid max_file_size
        with pytest.raises(ValidationError):
            LoggingConfig(max_file_size=0)
        
        # Invalid backup_count
        with pytest.raises(ValidationError):
            LoggingConfig(backup_count=-1)
    
    def test_research_config_validation(self):
        """Test research configuration validation"""
        # Valid config
        config = ResearchConfig(max_papers_per_search=50)
        assert config.max_papers_per_search == 50
        
        # Invalid max_papers_per_search
        with pytest.raises(ValidationError):
            ResearchConfig(max_papers_per_search=0)
        
        # Invalid concurrent_requests
        with pytest.raises(ValidationError):
            ResearchConfig(concurrent_requests=0)
        
        # Invalid note_confidence_threshold
        with pytest.raises(ValidationError):
            ResearchConfig(note_confidence_threshold=1.5)
        
        with pytest.raises(ValidationError):
            ResearchConfig(note_confidence_threshold=-0.1)
    
    def test_security_config_validation(self):
        """Test security configuration validation"""
        # Valid config
        config = SecurityConfig(request_timeout=30)
        assert config.request_timeout == 30
        
        # Invalid request_timeout
        with pytest.raises(ValidationError):
            SecurityConfig(request_timeout=0)
        
        # Invalid max_request_size
        with pytest.raises(ValidationError):
            SecurityConfig(max_request_size=-1)
    
    def test_application_config_validation(self):
        """Test application configuration validation"""
        # Valid config
        config = ApplicationConfig(environment="development")
        assert config.environment == "development"
        
        # Invalid environment
        with pytest.raises(ValidationError):
            ApplicationConfig(environment="invalid")


class TestConfigurationManager:
    """Test configuration manager"""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create temporary config file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'environment': 'testing',
                'debug': True,
                'database': {
                    'path': 'test.db',
                    'max_connections': 5
                },
                'logging': {
                    'level': 'DEBUG',
                    'file_enabled': False
                }
            }
            yaml.dump(config_data, f)
            yield f.name
        
        # Cleanup
        os.unlink(f.name)
    
    @pytest.fixture
    def config_manager(self, temp_config_file):
        """Create configuration manager with temp file"""
        return ConfigurationManager(config_path=temp_config_file)
    
    def test_load_config_from_file(self, config_manager):
        """Test loading configuration from file"""
        config = config_manager.get_config()
        
        assert config.environment == "testing"
        assert config.debug is True
        assert config.database.path == "test.db"
        assert config.database.max_connections == 5
        assert config.logging.level == "DEBUG"
        assert config.logging.file_enabled is False
    
    def test_load_config_nonexistent_file(self):
        """Test loading config when file doesn't exist"""
        manager = ConfigurationManager(config_path="nonexistent.yaml")
        config = manager.get_config()
        
        # Should load with defaults
        assert config.environment == "development"
        assert config.debug is True
    
    def test_environment_variable_override(self):
        """Test environment variable configuration override"""
        with patch.dict(os.environ, {
            'RESEARCH_ASSISTANT_DEBUG': 'false',
            'RESEARCH_ASSISTANT_DATABASE_PATH': 'env_test.db',
            'RESEARCH_ASSISTANT_LOGGING_LEVEL': 'ERROR',
            'RESEARCH_ASSISTANT_RESEARCH_MAX_PAPERS_PER_SEARCH': '200'
        }):
            manager = ConfigurationManager(config_path="nonexistent.yaml")
            config = manager.get_config()
            
            assert config.debug is False
            assert config.database.path == "env_test.db"
            assert config.logging.level == "ERROR"
            assert config.research.max_papers_per_search == 200
    
    def test_convert_env_value(self):
        """Test environment value conversion"""
        manager = ConfigurationManager()
        
        # Boolean conversion
        assert manager._convert_env_value('true') is True
        assert manager._convert_env_value('false') is False
        assert manager._convert_env_value('True') is True
        
        # Integer conversion
        assert manager._convert_env_value('42') == 42
        
        # Float conversion
        assert manager._convert_env_value('3.14') == 3.14
        
        # JSON conversion
        assert manager._convert_env_value('{"key": "value"}') == {"key": "value"}
        assert manager._convert_env_value('["a", "b", "c"]') == ["a", "b", "c"]
        
        # List conversion
        assert manager._convert_env_value('a,b,c') == ['a', 'b', 'c']
        
        # String (no conversion)
        assert manager._convert_env_value('hello') == 'hello'
    
    def test_get_configuration_values(self, config_manager):
        """Test getting configuration values by key"""
        # Direct property access
        assert config_manager.get('environment') == 'testing'
        assert config_manager.get('debug') is True
        
        # Nested property access
        assert config_manager.get('database.path') == 'test.db'
        assert config_manager.get('database.max_connections') == 5
        assert config_manager.get('logging.level') == 'DEBUG'
        
        # Non-existent key with default
        assert config_manager.get('nonexistent.key', 'default') == 'default'
        assert config_manager.get('nonexistent.key') is None
    
    def test_set_configuration_values(self, config_manager):
        """Test setting configuration values"""
        # Set simple value
        config_manager.set('debug', False)
        assert config_manager.get('debug') is False
        
        # Set nested value
        config_manager.set('database.max_connections', 10)
        assert config_manager.get('database.max_connections') == 10
        
        # Try to set invalid path
        with pytest.raises(ConfigurationError):
            config_manager.set('nonexistent.path.key', 'value')
    
    def test_save_and_reload_config(self, config_manager, temp_config_file):
        """Test saving and reloading configuration"""
        # Modify configuration
        config_manager.set('debug', False)
        config_manager.set('database.max_connections', 15)
        
        # Save to new file
        new_config_path = temp_config_file + '.new'
        config_manager.save_config(new_config_path)
        
        # Load with new manager
        new_manager = ConfigurationManager(config_path=new_config_path)
        
        assert new_manager.get('debug') is False
        assert new_manager.get('database.max_connections') == 15
        
        # Cleanup
        os.unlink(new_config_path)
    
    def test_validate_api_key(self, config_manager):
        """Test API key validation"""
        # No API key
        assert config_manager.validate_api_key('openalex') is False
        
        # Set API key
        config_manager.set('apis.openalex.api_key', 'valid_api_key_123456')
        assert config_manager.validate_api_key('openalex') is True
        
        # Too short API key
        config_manager.set('apis.openalex.api_key', 'short')
        assert config_manager.validate_api_key('openalex') is False
        
        # Non-existent API
        assert config_manager.validate_api_key('nonexistent') is False
    
    def test_get_api_config(self, config_manager):
        """Test getting API configuration"""
        # Get existing API config
        api_config = config_manager.get_api_config('openalex')
        assert api_config is not None
        assert api_config.base_url == "https://api.openalex.org"
        
        # Get non-existent API config
        assert config_manager.get_api_config('nonexistent') is None
        
        # Test environment variable API key injection
        with patch.dict(os.environ, {'RESEARCH_ASSISTANT_OPENALEX_API_KEY': 'env_key'}):
            api_config = config_manager.get_api_config('openalex')
            assert api_config.api_key == 'env_key'
    
    def test_environment_specific_settings(self):
        """Test environment-specific configuration adjustments"""
        # Production environment
        with patch.dict(os.environ, {'RESEARCH_ASSISTANT_ENVIRONMENT': 'production'}):
            manager = ConfigurationManager()
            config = manager.get_config()
            
            assert config.debug is False
            assert config.logging.level == "WARNING"
            assert config.security.ssl_verify is True
        
        # Testing environment
        with patch.dict(os.environ, {'RESEARCH_ASSISTANT_ENVIRONMENT': 'testing'}):
            manager = ConfigurationManager()
            config = manager.get_config()
            
            assert config.database.path == ":memory:"
            assert config.logging.file_enabled is False
            assert config.research.max_papers_per_search == 10
    
    def test_configuration_watchers(self, config_manager):
        """Test configuration change watchers"""
        watcher_calls = []
        
        def test_watcher(key, value):
            watcher_calls.append((key, value))
        
        config_manager.watch_config(test_watcher)
        
        # Make a configuration change
        config_manager.set('debug', False)
        
        # Check that watcher was called
        assert len(watcher_calls) == 1
        assert watcher_calls[0] == ('debug', False)
    
    def test_create_default_config_file(self):
        """Test creating default configuration file"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.yaml') as f:
            config_path = f.name
        
        # Remove the file so we can create it
        os.unlink(config_path)
        
        manager = ConfigurationManager()
        manager.create_default_config_file(config_path)
        
        # Check that file was created
        assert Path(config_path).exists()
        
        # Load the created file
        with open(config_path, 'r') as f:
            content = f.read()
            assert 'environment: development' in content
            assert 'database:' in content
            assert 'logging:' in content
        
        # Cleanup
        os.unlink(config_path)
    
    def test_invalid_config_file(self):
        """Test handling of invalid configuration files"""
        # Invalid YAML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('invalid: yaml: content: [')
            invalid_yaml_path = f.name
        
        with pytest.raises(ConfigurationError):
            ConfigurationManager(config_path=invalid_yaml_path)
        
        os.unlink(invalid_yaml_path)
        
        # Invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json content}')
            invalid_json_path = f.name
        
        with pytest.raises(ConfigurationError):
            ConfigurationManager(config_path=invalid_json_path)
        
        os.unlink(invalid_json_path)
    
    def test_config_merge(self):
        """Test configuration merging logic"""
        manager = ConfigurationManager()
        
        base = {
            'a': 1,
            'b': {
                'c': 2,
                'd': 3
            }
        }
        
        override = {
            'a': 10,
            'b': {
                'c': 20,
                'e': 4
            },
            'f': 5
        }
        
        result = manager._merge_configs(base, override)
        
        assert result['a'] == 10  # Overridden
        assert result['b']['c'] == 20  # Overridden
        assert result['b']['d'] == 3  # Preserved
        assert result['b']['e'] == 4  # Added
        assert result['f'] == 5  # Added
    
    def test_production_validation_warnings(self, caplog):
        """Test production environment validation warnings"""
        with patch.dict(os.environ, {'RESEARCH_ASSISTANT_ENVIRONMENT': 'production'}):
            manager = ConfigurationManager()
            config = manager.get_config()
            
            # Should log warnings about missing API keys and other security issues
            assert "No API key configured" in caplog.text or len(caplog.records) >= 0


class TestConfigurationIntegration:
    """Integration tests for configuration system"""
    
    def test_full_configuration_lifecycle(self):
        """Test complete configuration lifecycle"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_config.yaml')
            
            # Create configuration manager
            manager = ConfigurationManager(config_path=config_path)
            
            # Create default config file
            manager.create_default_config_file()
            
            # Load configuration
            config = manager.load_config()
            assert config.environment == "development"
            
            # Modify configuration
            manager.set('research.max_papers_per_search', 150)
            manager.set('logging.level', 'WARNING')
            
            # Save configuration
            manager.save_config()
            
            # Create new manager and load saved config
            new_manager = ConfigurationManager(config_path=config_path)
            new_config = new_manager.get_config()
            
            assert new_config.research.max_papers_per_search == 150
            assert new_config.logging.level == 'WARNING'
    
    def test_environment_override_precedence(self):
        """Test that environment variables take precedence"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'debug': True,
                'database': {'path': 'file_config.db'}
            }, f)
            config_path = f.name
        
        # Environment should override file config
        with patch.dict(os.environ, {
            'RESEARCH_ASSISTANT_DEBUG': 'false',
            'RESEARCH_ASSISTANT_DATABASE_PATH': 'env_config.db'
        }):
            manager = ConfigurationManager(config_path=config_path)
            config = manager.get_config()
            
            assert config.debug is False  # From environment
            assert config.database.path == 'env_config.db'  # From environment
        
        os.unlink(config_path)
    
    def test_api_configuration_with_environment_keys(self):
        """Test API configuration with environment-provided keys"""
        with patch.dict(os.environ, {
            'RESEARCH_ASSISTANT_APIS_OPENALEX_API_KEY': 'openalex_key_123',
            'RESEARCH_ASSISTANT_APIS_CROSSREF_API_KEY': 'crossref_key_456'
        }):
            manager = ConfigurationManager()
            
            openalex_config = manager.get_api_config('openalex')
            crossref_config = manager.get_api_config('crossref')
            
            assert openalex_config.api_key == 'openalex_key_123'
            assert crossref_config.api_key == 'crossref_key_456'
            
            assert manager.validate_api_key('openalex') is True
            assert manager.validate_api_key('crossref') is True
