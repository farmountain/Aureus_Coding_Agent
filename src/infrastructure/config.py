"""
Configuration Management

Provides:
- YAML/ENV configuration loading
- Configuration validation
- Environment-specific configs
- Dynamic reconfiguration
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class AureusConfig:
    """Aureus configuration"""
    
    # Logging
    log_level: str = "INFO"
    log_dir: Optional[Path] = None
    log_json_format: bool = True
    
    # Performance
    enable_monitoring: bool = True
    enable_performance_tracking: bool = True
    
    # Model Provider
    default_model_provider: str = "mock"
    model_name: str = "mock-model"
    model_api_key: Optional[str] = None
    model_timeout: float = 30.0
    model_max_retries: int = 3
    
    # Memory
    memory_storage_dir: Path = field(default_factory=lambda: Path(".aureus/memory"))
    memory_max_sessions: int = 1000
    memory_compression_enabled: bool = True
    
    # Governance
    default_policy_path: Path = field(default_factory=lambda: Path(".aureus-policy.yaml"))
    enforce_budgets: bool = True
    require_human_approval: bool = True
    
    # Self-Play
    self_play_enabled: bool = False
    self_play_max_iterations: int = 10000
    self_play_require_tests_pass: bool = True
    
    # Security
    sandbox_enabled: bool = True
    validate_all_paths: bool = True
    
    # Environment
    environment: str = "development"  # development, staging, production
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'log_level': self.log_level,
            'log_dir': str(self.log_dir) if self.log_dir else None,
            'log_json_format': self.log_json_format,
            'enable_monitoring': self.enable_monitoring,
            'enable_performance_tracking': self.enable_performance_tracking,
            'default_model_provider': self.default_model_provider,
            'model_name': self.model_name,
            'model_timeout': self.model_timeout,
            'model_max_retries': self.model_max_retries,
            'memory_storage_dir': str(self.memory_storage_dir),
            'memory_max_sessions': self.memory_max_sessions,
            'memory_compression_enabled': self.memory_compression_enabled,
            'default_policy_path': str(self.default_policy_path),
            'enforce_budgets': self.enforce_budgets,
            'require_human_approval': self.require_human_approval,
            'self_play_enabled': self.self_play_enabled,
            'self_play_max_iterations': self.self_play_max_iterations,
            'self_play_require_tests_pass': self.self_play_require_tests_pass,
            'sandbox_enabled': self.sandbox_enabled,
            'validate_all_paths': self.validate_all_paths,
            'environment': self.environment
        }


class ConfigLoader:
    """
    Configuration loader with environment override support
    
    Priority (highest to lowest):
    1. Environment variables (AUREUS_*)
    2. Config file (aureus-config.yaml)
    3. Default values
    """
    
    @staticmethod
    def load(config_path: Optional[Path] = None) -> AureusConfig:
        """
        Load configuration
        
        Args:
            config_path: Path to config file (None = look for aureus-config.yaml)
            
        Returns:
            AureusConfig instance
        """
        # Start with defaults
        config = AureusConfig()
        
        # Load from file if exists
        if config_path is None:
            config_path = Path("aureus-config.yaml")
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                file_config = yaml.safe_load(f)
            
            if file_config:
                config = ConfigLoader._apply_dict_to_config(config, file_config)
        
        # Override with environment variables
        config = ConfigLoader._apply_env_to_config(config)
        
        return config
    
    @staticmethod
    def _apply_dict_to_config(config: AureusConfig, data: Dict[str, Any]) -> AureusConfig:
        """Apply dictionary values to config"""
        for key, value in data.items():
            if hasattr(config, key):
                # Convert string paths to Path objects
                if key.endswith('_dir') or key.endswith('_path'):
                    if value is not None:
                        value = Path(value)
                
                setattr(config, key, value)
        
        return config
    
    @staticmethod
    def _apply_env_to_config(config: AureusConfig) -> AureusConfig:
        """Apply environment variables to config"""
        env_mapping = {
            'AUREUS_LOG_LEVEL': 'log_level',
            'AUREUS_LOG_DIR': 'log_dir',
            'AUREUS_MODEL_PROVIDER': 'default_model_provider',
            'AUREUS_MODEL_NAME': 'model_name',
            'AUREUS_MODEL_API_KEY': 'model_api_key',
            'AUREUS_MEMORY_DIR': 'memory_storage_dir',
            'AUREUS_POLICY_PATH': 'default_policy_path',
            'AUREUS_SELF_PLAY': 'self_play_enabled',
            'AUREUS_ENVIRONMENT': 'environment'
        }
        
        for env_var, config_key in env_mapping.items():
            value = os.environ.get(env_var)
            
            if value is not None:
                # Type conversion
                if config_key.endswith('_enabled'):
                    value = value.lower() in ('true', '1', 'yes')
                elif config_key.endswith('_dir') or config_key.endswith('_path'):
                    value = Path(value)
                elif isinstance(getattr(config, config_key), int):
                    value = int(value)
                elif isinstance(getattr(config, config_key), float):
                    value = float(value)
                
                setattr(config, config_key, value)
        
        return config
    
    @staticmethod
    def save(config: AureusConfig, config_path: Path):
        """
        Save configuration to file
        
        Args:
            config: Configuration to save
            config_path: Path to save to
        """
        config_data = config.to_dict()
        
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)


class ConfigValidator:
    """Validate configuration"""
    
    @staticmethod
    def validate(config: AureusConfig) -> list[str]:
        """
        Validate configuration
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if config.log_level.upper() not in valid_log_levels:
            errors.append(f"Invalid log_level: {config.log_level}")
        
        # Validate environment
        valid_environments = ['development', 'staging', 'production']
        if config.environment not in valid_environments:
            errors.append(f"Invalid environment: {config.environment}")
        
        # Validate model timeout
        if config.model_timeout <= 0:
            errors.append(f"model_timeout must be positive: {config.model_timeout}")
        
        # Validate max retries
        if config.model_max_retries < 0:
            errors.append(f"model_max_retries must be non-negative: {config.model_max_retries}")
        
        # Validate max sessions
        if config.memory_max_sessions <= 0:
            errors.append(f"memory_max_sessions must be positive: {config.memory_max_sessions}")
        
        # Validate self-play iterations
        if config.self_play_max_iterations <= 0:
            errors.append(f"self_play_max_iterations must be positive: {config.self_play_max_iterations}")
        
        return errors


# Global configuration
_global_config: Optional[AureusConfig] = None


def get_config() -> AureusConfig:
    """Get global configuration"""
    global _global_config
    if _global_config is None:
        _global_config = ConfigLoader.load()
    return _global_config


def load_config(config_path: Optional[Path] = None) -> AureusConfig:
    """Load and set global configuration"""
    global _global_config
    _global_config = ConfigLoader.load(config_path)
    
    # Validate
    errors = ConfigValidator.validate(_global_config)
    if errors:
        raise ValueError(f"Configuration validation failed: {errors}")
    
    return _global_config


def reload_config():
    """Reload configuration from file/environment"""
    global _global_config
    _global_config = None
    return get_config()
