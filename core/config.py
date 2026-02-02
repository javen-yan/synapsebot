import os
import yaml
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class LLMConfig(BaseModel):
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    
    @field_validator('base_url', 'api_key', 'model', mode='after')
    @classmethod
    def validate_required_fields(cls, v, info):
        """Ensure required fields are not empty after environment variable expansion"""
        if not v:
            raise ValueError(f"LLM configuration field '{info.field_name}' is required but not provided")
        return v

class StorageConfig(BaseModel):
    data_path: str = "~/.synapsebot"
    memory_enabled: bool = True
    memory_max_context: int = 2000
    
    @property
    def system_skills_path(self) -> str:
        """System skills path (read-only, from core/system/skills)"""
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "core", "system", "skills")
    
    @property
    def system_mcp_config_path(self) -> str:
        """System MCP config path (read-only, from core/system/mcp_config.json)"""
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "core", "system", "mcp_config.json")
    
    @property
    def user_skills_path(self) -> str:
        """User skills path (writable, in user data directory)"""
        return os.path.join(os.path.expanduser(self.data_path), "user", "skills")
    
    @property
    def user_mcp_config_path(self) -> str:
        """User MCP config path (writable, in user data directory)"""
        return os.path.join(os.path.expanduser(self.data_path), "user", "mcp_config.json")

    @property
    def get_memory_path(self) -> str:
        return os.path.join(os.path.expanduser(self.data_path), "memory")

    @property
    def upload_dir(self) -> str:
        return os.path.join(os.path.expanduser(self.data_path), "uploads")

    def ensure_structure(self):
        """Ensure all required user directories and files exist."""
        # Expand ~ in data_path
        data_path = os.path.expanduser(self.data_path)
        self.data_path = data_path
        
        # Create user directories only (system resources are in core/system)
        for path in [self.user_skills_path, self.upload_dir, self.get_memory_path]:
            os.makedirs(path, exist_ok=True)
        
        # Create user MCP config if it doesn't exist
        default_mcp_config = '{"mcpServers": {}}'
        if not os.path.exists(self.user_mcp_config_path):
            os.makedirs(os.path.dirname(self.user_mcp_config_path), exist_ok=True)
            with open(self.user_mcp_config_path, "w") as f:
                f.write(default_mcp_config)
    


class SlackConfig(BaseModel):
    enabled: bool = False
    bot_token: str = Field(default="")
    app_token: str = Field(default="")

class FeishuConfig(BaseModel):
    enabled: bool = False
    app_id: str = Field(default="")
    app_secret: str = Field(default="")

class WebConfig(BaseModel):
    enabled: bool = True # Default to True for now

class ChannelsConfig(BaseModel):
    slack: SlackConfig = Field(default_factory=SlackConfig)
    feishu: FeishuConfig = Field(default_factory=FeishuConfig)
    web: WebConfig = Field(default_factory=WebConfig)

class Config(BaseModel):
    llm: LLMConfig
    storage: StorageConfig
    channels: ChannelsConfig = Field(default_factory=ChannelsConfig)
    log_level: str = "INFO"


# Global singleton instance
_config_instance: Optional["Config"] = None

def get_config(config_path: str = "config.yaml", reload: bool = False) -> "Config":
    """
    Get the global configuration instance. 
    Loads it if it hasn't been loaded yet or if reload is True.
    """
    global _config_instance
    
    if _config_instance is None or reload:
        _config_instance = load_config(config_path)
        
    return _config_instance

def expand_env_var(value: Optional[str], fallback_env_vars: list[str] = None) -> Optional[str]:
    """
    Expand environment variable in a config value.
    
    Supports two formats:
    1. ${ENV_VAR} syntax in the value string
    2. Direct environment variable fallback if value is None/empty
    
    Args:
        value: The config value (may contain ${ENV_VAR} or be None)
        fallback_env_vars: List of environment variable names to try as fallback
        
    Returns:
        Expanded value or None if not found
    """
    # If value contains ${ENV_VAR}, expand it
    if value and isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        env_var = value[2:-1]
        return os.getenv(env_var)
    
    # If value is provided and not an env var reference, return as-is
    if value:
        return value
    
    # Try fallback environment variables
    if fallback_env_vars:
        for env_var in fallback_env_vars:
            env_value = os.getenv(env_var)
            if env_value:
                return env_value
    
    return None


def load_config(config_path: str = "config.yaml") -> Config:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)
    
    # Expand LLM configuration with environment variable support
    llm_config = raw_config.get("llm", {})
    
    # Support both config file and environment variables for LLM settings
    # Priority: config file value > environment variable
    llm_config["base_url"] = expand_env_var(
        llm_config.get("base_url"),
        fallback_env_vars=["LLM_BASE_URL"]
    )
    
    llm_config["api_key"] = expand_env_var(
        llm_config.get("api_key"),
        fallback_env_vars=["LLM_API_KEY"]
    )
    
    llm_config["model"] = expand_env_var(
        llm_config.get("model"),
        fallback_env_vars=["LLM_MODEL"]
    )
    
    raw_config["llm"] = llm_config

    # Expand Slack env vars
    slack_cfg = raw_config.get("channels", {}).get("slack", {})
    if slack_cfg:
        for field in ["bot_token", "app_token"]:
            expanded = expand_env_var(slack_cfg.get(field))
            if expanded:
                raw_config.setdefault("channels", {}).setdefault("slack", {})[field] = expanded

    # Expand Feishu env vars
    feishu_cfg = raw_config.get("channels", {}).get("feishu", {})
    if feishu_cfg:
        for field in ["app_id", "app_secret"]:
            expanded = expand_env_var(feishu_cfg.get(field))
            if expanded:
                raw_config.setdefault("channels", {}).setdefault("feishu", {})[field] = expanded
        
    config = Config(**raw_config)
    
    config.storage.ensure_structure()
    
    return config
