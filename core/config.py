import os
import yaml
from pathlib import Path
from pydantic import BaseModel, Field

class LLMConfig(BaseModel):
    base_url: str
    api_key: str
    model: str

class StorageConfig(BaseModel):
    data_path: str = "./data"
    
    @property
    def system_skills_path(self) -> str:
        return os.path.join(self.data_path, "system", "skills")
    
    @property
    def system_mcp_config_path(self) -> str:
        return os.path.join(self.data_path, "system", "mcp_config.json")
    
    @property
    def user_skills_path(self) -> str:
        return os.path.join(self.data_path, "user", "skills")
    
    @property
    def user_mcp_config_path(self) -> str:
        return os.path.join(self.data_path, "user", "mcp_config.json")

    @property
    def upload_dir(self) -> str:
        return os.path.join(self.data_path, "uploads")

    def ensure_structure(self):
        """Ensure all required directories and files exist."""
        # Create directories
        for path in [self.system_skills_path, self.user_skills_path, self.upload_dir]:
            os.makedirs(path, exist_ok=True)
            
        # Create MCP config files if they don't exist
        default_mcp_config = '{"mcpServers": {}}'
        
        for path in [self.system_mcp_config_path, self.user_mcp_config_path]:
            # Ensure parent dir exists
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            if not os.path.exists(path):
                with open(path, "w") as f:
                    f.write(default_mcp_config)
    


class SlackConfig(BaseModel):
    enabled: bool = False
    bot_token: str = Field(default="")
    app_token: str = Field(default="")

class FeishuConfig(BaseModel):
    enabled: bool = False
    app_id: str = Field(default="")
    app_secret: str = Field(default="")

class ChannelsConfig(BaseModel):
    slack: SlackConfig = Field(default_factory=SlackConfig)
    feishu: FeishuConfig = Field(default_factory=FeishuConfig)

class Config(BaseModel):
    llm: LLMConfig
    storage: StorageConfig
    channels: ChannelsConfig = Field(default_factory=ChannelsConfig)
    log_level: str = "INFO"

def load_config(config_path: str = "config.yaml") -> Config:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)
    
    # Expand env vars in API Key
    api_key = raw_config.get("llm", {}).get("api_key", "")
    if api_key.startswith("${") and api_key.endswith("}"):
        env_var = api_key[2:-1]
        raw_config["llm"]["api_key"] = os.getenv(env_var, "")

    # Expand Slack env vars
    slack_cfg = raw_config.get("channels", {}).get("slack", {})
    for field in ["bot_token", "app_token"]:
        val = slack_cfg.get(field, "")
        if val.startswith("${") and val.endswith("}"):
            env_var = val[2:-1]
            raw_config.setdefault("channels", {}).setdefault("slack", {})[field] = os.getenv(env_var, "")

    # Expand Feishu env vars
    feishu_cfg = raw_config.get("channels", {}).get("feishu", {})
    for field in ["app_id", "app_secret"]:
        val = feishu_cfg.get(field, "")
        if val.startswith("${") and val.endswith("}"):
            env_var = val[2:-1]
            raw_config.setdefault("channels", {}).setdefault("feishu", {})[field] = os.getenv(env_var, "")
        
    config = Config(**raw_config)
    
    config.storage.ensure_structure()
    
    return config
